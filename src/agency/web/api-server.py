#!/usr/bin/env python3
"""
WARPCORE Agency API Server - Clean Minimal Version
Serves real workflow execution logs and agent management with minimal endpoints
"""

import os
import sys
import json
import glob
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory, Response
from flask_cors import CORS
import re
import signal
import psutil

# Global process tracking
running_processes = {}

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Data directory - computed relative to script location, not hardcoded
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / '.data'
AGENTS_DIR = SCRIPT_DIR.parent / 'agents'
WORKFLOWS_DIR = SCRIPT_DIR.parent / 'workflows'

logger.info(f"Data directory: {DATA_DIR}")
logger.info(f"Agents directory: {AGENTS_DIR}")
logger.info(f"Workflows directory: {WORKFLOWS_DIR}")

def load_execution_logs():
    """Load and parse workflow execution logs from .data directory"""
    logs = []
    
    if not DATA_DIR.exists():
        logger.warning(f"Data directory not found: {DATA_DIR}")
        return logs
    
    json_files = list(DATA_DIR.glob('*.json'))
    logger.info(f"Found {len(json_files)} JSON files in data directory")
    
    for file_path in json_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            filename = file_path.name
            
            # Extract workflow_id and sequence from filename using regex
            wf_match = re.search(r'(wf_\d{8}_\d{6}_[a-f0-9]+)', filename)
            workflow_id = wf_match.group(1) if wf_match else 'unknown'
            
            seq_match = re.search(r'(\d{3})', filename)
            sequence = seq_match.group(1) if seq_match else '000'
            
            # Extract agent name from data or filename
            agent_name = data.get('agent_name', 'unknown_agent')
            
            # Handle different data structures
            if 'actions' in data and isinstance(data['actions'], list):
                # Multiple actions in file
                for i, action in enumerate(data['actions']):
                    logs.append({
                        'workflow_id': workflow_id,
                        'sequence': f"{sequence}-{i:02d}",
                        'agent_name': action.get('agent_name', agent_name),
                        'action_type': action.get('type', 'UNKNOWN'),
                        'timestamp': action.get('timestamp', datetime.now().isoformat()),
                        'motive': action.get('motive', ''),
                        'content': action.get('content', {}),
                        'source_file': filename
                    })
            else:
                # Single action/entry
                logs.append({
                    'workflow_id': workflow_id,
                    'sequence': sequence,
                    'agent_name': agent_name,
                    'action_type': data.get('action_type', 'WORKFLOW_STEP'),
                    'timestamp': data.get('timestamp', datetime.now().isoformat()),
                    'motive': f'Workflow step from {filename}',
                    'content': data,
                    'source_file': filename
                })
                        
        except Exception as e:
            logger.warning(f"Error processing {file_path}: {e}")
            continue
    
    # Sort by timestamp
    logs.sort(key=lambda x: x['timestamp'], reverse=True)
    logger.info(f"Loaded {len(logs)} execution log entries")
    
    return logs

def load_agent_specs():
    """Load agent specifications from agents directory"""
    agents = []
    
    if not AGENTS_DIR.exists():
        logger.warning(f"Agents directory not found: {AGENTS_DIR}")
        return agents
    
    agent_files = list(AGENTS_DIR.glob('*.json'))
    
    for agent_file in agent_files:
        try:
            with open(agent_file, 'r') as f:
                agent_data = json.load(f)
            
            # Extract agent name using regex from filename
            filename = agent_file.name
            
            # Extract step prefix and agent name
            step_match = re.match(r'^(\d+[a-z]?)', filename)
            step_prefix = step_match.group(1) if step_match else None
            
            # Extract clean agent name (remove step prefix and extensions)
            name_match = re.search(r'(?:\d+[a-z]?_)?([a-zA-Z_]+)(?:_from_.*)?\.json$', filename)
            agent_name = name_match.group(1) if name_match else agent_data.get('agent_id', 'unknown')
            
            # Ensure workflow_position is an integer
            workflow_pos = agent_data.get('workflow_position', 0)
            if not isinstance(workflow_pos, int):
                try:
                    workflow_pos = int(workflow_pos)
                except (ValueError, TypeError):
                    workflow_pos = 0
            
            agents.append({
                'id': agent_data.get('agent_id', agent_name),
                'agent_name': str(agent_name),
                'filename': filename,
                'step_prefix': step_prefix,
                'workflow_position': workflow_pos,
                'dependencies': agent_data.get('dependencies', []),
                'outputs_to': agent_data.get('outputs_to', []),
                'has_prompt': bool(agent_data.get('prompt', '')),
                'validation_rules': len(agent_data.get('validation_rules', [])),
                'success_criteria': len(agent_data.get('success_criteria', [])),
                'version': agent_data.get('agent_version', '1.0.0'),
                'cache_pattern': agent_data.get('cache_pattern', '')
            })
            
        except Exception as e:
            logger.warning(f"Error loading agent {agent_file}: {e}")
            continue
    
    # Sort safely by workflow_position (int) and agent_name (str)
    def sort_key(agent):
        pos = agent.get('workflow_position', 0)
        if not isinstance(pos, int):
            pos = 0
        name = str(agent.get('agent_name', ''))
        return (pos, name)
    
    return sorted(agents, key=sort_key)

# CORE ENDPOINTS

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint with agent discovery sample"""
    try:
        agents = load_agent_specs()
        agent_names = [agent['id'] for agent in agents[:5]]  # First 5 agent IDs
        
        return jsonify({
            'status': 'healthy',
            'service': 'WARPCORE Clean API',
            'timestamp': datetime.now().isoformat(),
            'data_directory': str(DATA_DIR),
            'agents_found': len(agents),
            'data_files_found': len(list(DATA_DIR.glob('*.json'))) if DATA_DIR.exists() else 0,
            'sample_agents': agent_names,
            'discovery_method': 'schema-based regex parsing'
        })
    except Exception as e:
        return jsonify({
            'status': 'healthy_with_errors',
            'service': 'WARPCORE Clean API',
            'timestamp': datetime.now().isoformat(),
            'data_directory': str(DATA_DIR),
            'agents_found': 0,
            'data_files_found': len(list(DATA_DIR.glob('*.json'))) if DATA_DIR.exists() else 0,
            'error': str(e)
        })

@app.route('/api/execution-logs', methods=['GET'])
def get_execution_logs():
    """Return all execution logs"""
    try:
        logs = load_execution_logs()
        return jsonify({
            'status': 'success',
            'count': len(logs),
            'logs': logs,
            'data_source': 'REAL WORKFLOW EXECUTION DATA'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'logs': []
        }), 500

@app.route('/api/workflow-logs', methods=['GET'])
def get_workflow_logs():
    """Return filtered workflow execution logs"""
    try:
        logs = load_execution_logs()
        
        # Filter by query parameters
        workflow_id = request.args.get('workflow_id')
        agent_name = request.args.get('agent_name')
        limit = request.args.get('limit', type=int)
        
        filtered_logs = logs
        
        if workflow_id:
            filtered_logs = [log for log in filtered_logs if log['workflow_id'] == workflow_id]
        
        if agent_name:
            filtered_logs = [log for log in filtered_logs if log['agent_name'] == agent_name]
        
        if limit:
            filtered_logs = filtered_logs[:limit]
        
        return jsonify({
            'status': 'success',
            'count': len(filtered_logs),
            'total_logs': len(logs),
            'filters': {
                'workflow_id': workflow_id,
                'agent_name': agent_name,
                'limit': limit
            },
            'logs': filtered_logs,
            'data_source': 'REAL WORKFLOW EXECUTION DATA'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'logs': []
        }), 500

@app.route('/api/agents', methods=['GET'])
def get_agents():
    """Return list of all agents with their specs"""
    try:
        agents = load_agent_specs()
        return jsonify({
            'status': 'success',
            'agents': agents,
            'data_source': 'REAL AGENT SPECIFICATION FILES'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'agents': []
        }), 500

@app.route('/api/agent-specs/<agent_name>', methods=['GET'])
def get_agent_specs(agent_name):
    """Get full specifications for a specific agent - dynamically discovered"""
    try:
        # Find agent file by name (could be in various filename patterns)
        agent_files = list(AGENTS_DIR.glob('*.json')) if AGENTS_DIR.exists() else []
        
        target_file = None
        for agent_file in agent_files:
            with open(agent_file, 'r') as f:
                agent_data = json.load(f)
            
            # Check if this matches the requested agent
            if (agent_data.get('agent_id') == agent_name or 
                agent_name in agent_file.name.lower()):
                target_file = agent_file
                break
        
        if not target_file:
            return jsonify({
                'status': 'error',
                'message': f'Agent not found: {agent_name}',
                'available_agents': [f.stem for f in agent_files]
            }), 404
        
        # Load full agent specification
        with open(target_file, 'r') as f:
            agent_data = json.load(f)
        
        specs = {
            'agent_info': {
                'agent_id': agent_data.get('agent_id', 'unknown'),
                'agent_version': agent_data.get('agent_version', '1.0.0'),
                'workflow_position': agent_data.get('workflow_position', 0),
                'dependencies': agent_data.get('dependencies', []),
                'outputs_to': agent_data.get('outputs_to', []),
                'cache_pattern': agent_data.get('cache_pattern', ''),
                'input_cache_pattern': agent_data.get('input_cache_pattern', '')
            },
            'output_schema': agent_data.get('output_schema', {}),
            'validation_rules': agent_data.get('validation_rules', []),
            'success_criteria': agent_data.get('success_criteria', []),
            'prompt_length': len(agent_data.get('prompt', '')),
            'prompt_preview': agent_data.get('prompt', '')[:500] + '...' if agent_data.get('prompt', '') else 'No prompt available',
            'file_info': {
                'filename': target_file.name,
                'file_path': str(target_file),
                'last_modified': datetime.fromtimestamp(target_file.stat().st_mtime).isoformat()
            }
        }
        
        return jsonify({
            'status': 'success',
            'agent_specifications': specs,
            'data_source': 'REAL AGENT SPECIFICATION FILE'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/agents/<agent_name>/prompt', methods=['GET'])
def get_agent_prompt(agent_name):
    """Get full prompt for a specific agent"""
    try:
        agent_files = list(AGENTS_DIR.glob('*.json')) if AGENTS_DIR.exists() else []
        
        for agent_file in agent_files:
            with open(agent_file, 'r') as f:
                agent_data = json.load(f)
            
            if (agent_data.get('agent_id') == agent_name or 
                agent_name in agent_file.name.lower()):
                
                prompt = agent_data.get('prompt', '')
                
                # Replace placeholders if provided in query params
                workflow_id = request.args.get('workflow_id')
                trace_id = request.args.get('trace_id')
                
                if workflow_id:
                    prompt = prompt.replace('{workflow_id}', workflow_id)
                if trace_id:
                    prompt = prompt.replace('{trace_id}', trace_id)
                
                return jsonify({
                    'status': 'success',
                    'agent_id': agent_data.get('agent_id'),
                    'prompt': prompt
                })
        
        return jsonify({
            'status': 'error',
            'message': f'Agent not found: {agent_name}'
        }), 404
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/execute-agent', methods=['POST'])
def execute_agent():
    """Execute an agent via subprocess"""
    try:
        data = request.json
        agent_id = data.get('agent_id')
        workflow_id = data.get('workflow_id')
        custom_prompt = data.get('custom_prompt')
        src_dir = data.get('src_dir', str(SCRIPT_DIR.parent.parent))  # Default to warpcore root
        
        if not agent_id:
            return jsonify({
                'status': 'error',
                'message': 'agent_id is required'
            }), 400
        
        # Build command to execute agent
        cmd = ['python3', 'agency.py', agent_id]
        
        if workflow_id:
            cmd.append(workflow_id)
        
        if custom_prompt:
            cmd.append(custom_prompt)
        
        if src_dir != str(SCRIPT_DIR.parent.parent):
            cmd.extend(['--client-dir', src_dir])
        
        logger.info(f"Executing: {' '.join(cmd)}")
        
        # Start process without waiting for completion
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(SCRIPT_DIR.parent)
        )
        
        # Track the process
        process_key = f"{agent_id}_{workflow_id}_{process.pid}"
        running_processes[process_key] = {
            'process': process,
            'agent_id': agent_id,
            'workflow_id': workflow_id,
            'command': ' '.join(cmd),
            'start_time': datetime.now().isoformat(),
            'pid': process.pid
        }
        
        # Clean up completed processes
        completed_keys = [k for k, v in running_processes.items() if v['process'].poll() is not None]
        for key in completed_keys:
            del running_processes[key]
        
        return jsonify({
            'status': 'success',
            'agent_id': agent_id,
            'workflow_id': workflow_id,
            'command': ' '.join(cmd),
            'process_id': process.pid,
            'process_key': process_key,
            'execution_started': True,
            'note': 'Process started in background. Use stop-workflow to terminate.'
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({
            'status': 'error',
            'message': 'Agent execution timed out (5 minutes)'
        }), 408
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/stop-workflow/<workflow_id>', methods=['POST'])
def stop_workflow(workflow_id):
    """Stop running processes for a specific workflow"""
    try:
        stopped_processes = []
        remaining_processes = {}
        
        for key, proc_info in running_processes.items():
            if proc_info['workflow_id'] == workflow_id:
                process = proc_info['process']
                if process.poll() is None:  # Process still running
                    try:
                        process.terminate()
                        stopped_processes.append({
                            'pid': proc_info['pid'],
                            'agent_id': proc_info['agent_id'],
                            'command': proc_info['command']
                        })
                    except Exception as e:
                        logger.warning(f"Failed to terminate process {proc_info['pid']}: {e}")
                        remaining_processes[key] = proc_info
            else:
                remaining_processes[key] = proc_info
        
        # Update running processes
        running_processes.clear()
        running_processes.update(remaining_processes)
        
        return jsonify({
            'status': 'success',
            'message': f'Stop signals sent for workflow {workflow_id}',
            'workflow_id': workflow_id,
            'stopped_processes': stopped_processes,
            'processes_terminated': len(stopped_processes)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/execute-agent-stream', methods=['GET'])
def execute_agent_stream():
    """Stream agent execution output using Server-Sent Events"""
    agent_id = request.args.get('agent')
    
    if not agent_id:
        return jsonify({'status': 'error', 'message': 'Agent parameter required'}), 400
    
    def generate_stream():
        # This is a simple implementation - for now just return a placeholder
        # In a full implementation, you'd stream actual process output
        yield f"data: {{\"type\": \"start\", \"command\": \"python3 agency.py {agent_id}\"}}\n\n"
        yield f"data: {{\"type\": \"output\", \"line\": \"Streaming not fully implemented yet - use /api/execute-agent for now\"}}\n\n"
        yield f"data: {{\"type\": \"complete\", \"success\": false, \"exit_code\": 1}}\n\n"
    
    return Response(generate_stream(), mimetype='text/event-stream')

@app.route('/api/workflow-ids', methods=['GET'])
def get_workflow_ids():
    """Get list of all unique workflow IDs from execution logs"""
    try:
        logs = load_execution_logs()
        workflow_ids = sorted(list(set(log['workflow_id'] for log in logs if log['workflow_id'] != 'unknown')))
        
        return jsonify({
            'status': 'success',
            'workflow_ids': workflow_ids,
            'count': len(workflow_ids),
            'data_source': 'REAL WORKFLOW EXECUTION DATA'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'workflow_ids': []
        }), 500

@app.route('/api/running-processes', methods=['GET'])
def get_running_processes():
    """Get list of currently running agent processes"""
    try:
        # Clean up completed processes first
        active_processes = {}
        for key, proc_info in running_processes.items():
            if proc_info['process'].poll() is None:  # Still running
                active_processes[key] = {
                    'agent_id': proc_info['agent_id'],
                    'workflow_id': proc_info['workflow_id'],
                    'pid': proc_info['pid'],
                    'start_time': proc_info['start_time'],
                    'command': proc_info['command'],
                    'status': 'running'
                }
        
        # Update global tracking
        running_processes.clear()
        for key, proc_info in list(running_processes.items()):
            if proc_info['process'].poll() is None:
                running_processes[key] = proc_info
        
        return jsonify({
            'status': 'success',
            'running_processes': list(active_processes.values()),
            'count': len(active_processes)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'running_processes': []
        }), 500

# STATIC FILES
@app.route('/')
def dashboard():
    """Serve main dashboard"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    logger.info("Starting WARPCORE Clean API Server...")
    app.run(host='0.0.0.0', port=8081, debug=False)