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
import threading
import queue
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory, Response
from flask_cors import CORS
import re
import signal
import psutil

# Global process tracking
running_processes = {}

# Global streaming support
stream_clients = {}
client_counter = 0

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
def load_config():
    """Load configuration from config.json"""
    config_path = Path(__file__).parent / 'config.json'
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("Config file not found, using defaults")
        return {
            "api_server": {"host": "localhost", "port": 8081},
            "paths": {
                "base_dir": "../..",
                "data_dir": "../../.data",
                "franchise_dir": "../../agents/franchise"
            }
        }

CONFIG = load_config()
app = Flask(__name__)
CORS(app)

# Data directories - computed from config
SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR / CONFIG['paths']['base_dir']
DATA_DIR = SCRIPT_DIR / CONFIG['paths']['data_dir']
FRANCHISE_DIR = SCRIPT_DIR / CONFIG['paths']['franchise_dir']
WORKFLOWS_DIR = BASE_DIR / 'workflows'

# Auto-discover available franchises
def discover_franchises():
    """Auto-discover available franchises from directory structure"""
    franchises = []
    if FRANCHISE_DIR.exists():
        for franchise_path in FRANCHISE_DIR.iterdir():
            if franchise_path.is_dir() and (franchise_path / 'agents').exists():
                franchises.append(franchise_path.name)
    return sorted(franchises)

AVAILABLE_FRANCHISES = discover_franchises()

logger.info(f"Data directory: {DATA_DIR}")
logger.info(f"Franchise directory: {FRANCHISE_DIR}")
logger.info(f"Workflows directory: {WORKFLOWS_DIR}")
logger.info(f"Discovered franchises: {AVAILABLE_FRANCHISES}")

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

def load_agent_specs(franchise=None):
    """Load agent specifications from franchise directories"""
    agents = []
    
    if not FRANCHISE_DIR.exists():
        logger.warning(f"Franchise directory not found: {FRANCHISE_DIR}")
        return agents
    
    # If specific franchise requested, load only that
    franchises_to_load = [franchise] if franchise else AVAILABLE_FRANCHISES
    
    for franchise_name in franchises_to_load:
        franchise_path = FRANCHISE_DIR / franchise_name / 'agents'
        if not franchise_path.exists():
            continue
            
        agent_files = list(franchise_path.glob('*.json'))
        
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
                    'franchise': franchise_name,
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
    """Health check endpoint with franchise discovery"""
    try:
        agents = load_agent_specs()
        agent_count = len(agents)
        
        return jsonify({
            'status': 'healthy',
            'service': 'WARPCORE Clean API',
            'timestamp': datetime.now().isoformat(),
            'data_directory': str(DATA_DIR),
            'franchise_directory': str(FRANCHISE_DIR),
            'franchises': AVAILABLE_FRANCHISES,
            'agents_found': agent_count,
            'data_files_found': len(list(DATA_DIR.glob('*.json'))) if DATA_DIR.exists() else 0
        })
    except Exception as e:
        return jsonify({
            'status': 'healthy_with_errors',
            'service': 'WARPCORE Clean API',
            'timestamp': datetime.now().isoformat(),
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

@app.route('/api/franchises', methods=['GET'])
def get_franchises():
    """Get list of available franchises"""
    return jsonify({
        'status': 'success',
        'franchises': AVAILABLE_FRANCHISES,
        'data_source': 'AUTO-DISCOVERED FROM FILESYSTEM'
    })

@app.route('/api/agents', methods=['GET'])
@app.route('/api/agents/<franchise>', methods=['GET'])
def get_agents(franchise=None):
    """Return list of agents, optionally filtered by franchise"""
    try:
        # Get franchise from path parameter or query parameter
        if not franchise:
            franchise = request.args.get('franchise')
            
        if franchise and franchise not in AVAILABLE_FRANCHISES:
            return jsonify({
                'status': 'error',
                'message': f'Unknown franchise: {franchise}',
                'available_franchises': AVAILABLE_FRANCHISES
            }), 404
            
        agents = load_agent_specs(franchise)
        return jsonify({
            'status': 'success',
            'franchise': franchise or 'all',
            'agents': agents,
            'count': len(agents),
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
    """Execute an agent via subprocess with franchise support"""
    try:
        data = request.json
        agent_id = data.get('agent_id')
        franchise = data.get('franchise', 'staff')  # Default to staff franchise
        workflow_id = data.get('workflow_id')
        custom_prompt = data.get('custom_prompt')
        src_dir = data.get('src_dir', str(SCRIPT_DIR.parent.parent))  # Default to warpcore root
        
        if not agent_id:
            return jsonify({
                'status': 'error',
                'message': 'agent_id is required'
            }), 400
            
        if franchise not in AVAILABLE_FRANCHISES:
            return jsonify({
                'status': 'error',
                'message': f'Unknown franchise: {franchise}',
                'available_franchises': AVAILABLE_FRANCHISES
            }), 400
        
        # Build command to execute agent with franchise
        cmd = ['python3', 'agency.py', '--franchise', franchise, agent_id]
        
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

# STREAMING ENDPOINTS

@app.route('/api/agent/<agent_id>/execute/stream', methods=['POST'])
def execute_agent_stream(agent_id):
    """Start agent execution with streaming output"""
    global client_counter, stream_clients
    
    try:
        data = request.get_json() or {}
        franchise = data.get('franchise')
        custom_prompt = data.get('custom_prompt', '')
        src_dir = data.get('src_dir', str(SCRIPT_DIR.parent))
        workflow_id = data.get('workflow_id', f'wf_{datetime.now().strftime("%Y%m%d_%H%M%S")}_{agent_id}')
        
        # Create new client for streaming
        client_counter += 1
        client_id = f'client_{client_counter}'
        stream_clients[client_id] = queue.Queue()
        
        # Start agent execution in background thread
        threading.Thread(
            target=run_agent_streaming,
            args=(agent_id, franchise, custom_prompt, src_dir, workflow_id, client_id),
            daemon=True
        ).start()
        
        return jsonify({
            'status': 'success',
            'client_id': client_id,
            'agent_id': agent_id,
            'franchise': franchise,
            'workflow_id': workflow_id
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/stream/<client_id>')
def agent_stream(client_id):
    """Server-Sent Events stream for agent execution output"""
    def generate():
        if client_id not in stream_clients:
            yield f"data: ERROR: Invalid client ID\n\n"
            return
            
        client_queue = stream_clients[client_id]
        
        try:
            while True:
                try:
                    # Get message from queue (blocking with timeout)
                    message = client_queue.get(timeout=1)
                    if message is None:  # End signal
                        break
                    yield f"data: {message}\n\n"
                except queue.Empty:
                    # Send heartbeat
                    yield f"data: [heartbeat]\n\n"
        except Exception as e:
            yield f"data: ERROR: {str(e)}\n\n"
        finally:
            # Clean up client
            if client_id in stream_clients:
                del stream_clients[client_id]
    
    return Response(generate(), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*'
    })

def run_agent_streaming(agent_id, franchise, custom_prompt, src_dir, workflow_id, client_id):
    """Execute agent with streaming output to client queue"""
    if client_id not in stream_clients:
        return
    
    client_queue = stream_clients[client_id]
    
    try:
        client_queue.put(f"🚀 WARPCORE Agent Execution Started")
        client_queue.put(f"📋 Agent: {agent_id}")
        client_queue.put(f"🏢 Franchise: {franchise or 'default'}")
        client_queue.put(f"🆔 Workflow: {workflow_id}")
        client_queue.put(f"📁 Directory: {src_dir}")
        client_queue.put("")
        
        # Build command - try different CLI patterns
        cmd_variants = [
            # Direct warp agent execution
            ['warp', 'agent', 'run', agent_id],
            # Python CLI execution  
            ['python3', '-m', 'src.cli.main', 'agent', 'run', agent_id],
            # Direct python execution
            ['python3', 'src/cli/main.py', 'agent', 'run', agent_id]
        ]
        
        if franchise:
            for cmd in cmd_variants:
                cmd.extend(['--franchise', franchise])
        
        if custom_prompt:
            client_queue.put(f"📝 Using custom prompt ({len(custom_prompt)} chars)")
            for cmd in cmd_variants:
                cmd.extend(['--prompt', custom_prompt])
        
        client_queue.put(f"⚡ Starting agent execution...")
        client_queue.put("")
        
        # Try each command variant
        process = None
        for i, cmd in enumerate(cmd_variants):
            try:
                client_queue.put(f"🔄 Trying command variant {i+1}: {' '.join(cmd[:4])}...")
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    cwd=src_dir
                )
                
                # Test if process started successfully
                import time
                time.sleep(0.1)
                if process.poll() is None:
                    client_queue.put(f"✅ Command started successfully (PID: {process.pid})")
                    client_queue.put("")
                    break
                else:
                    client_queue.put(f"❌ Command failed quickly")
                    process = None
                    
            except FileNotFoundError:
                client_queue.put(f"❌ Command not found: {cmd[0]}")
                process = None
                continue
            except Exception as e:
                client_queue.put(f"❌ Error: {str(e)}")
                process = None
                continue
        
        if not process:
            client_queue.put("❌ All command variants failed")
            client_queue.put("💡 Make sure WARP CLI is installed and available")
            return
        
        # Track running process
        process_key = f"{workflow_id}_{agent_id}_{process.pid}"
        running_processes[process_key] = {
            'process': process,
            'agent_id': agent_id,
            'workflow_id': workflow_id,
            'pid': process.pid,
            'start_time': datetime.now().isoformat(),
            'command': ' '.join(cmd)
        }
        
        # Stream output line by line
        for line in iter(process.stdout.readline, ''):
            if not line:
                break
            client_queue.put(line.rstrip())
        
        process.wait()
        
        # Process completed
        client_queue.put("")
        client_queue.put(f"✅ Agent execution completed with code: {process.returncode}")
        
        # Remove from running processes
        if process_key in running_processes:
            del running_processes[process_key]
        
        # Check for output files
        data_dir = Path(src_dir) / '.data'
        if data_dir.exists():
            output_files = list(data_dir.glob('*.json'))
            if output_files:
                client_queue.put(f"📄 Generated {len(output_files)} output files in .data/")
                for f in output_files[-3:]:  # Show last 3 files
                    client_queue.put(f"  📄 {f.name}")
        
    except Exception as e:
        client_queue.put(f"❌ Execution Error: {str(e)}")
        logger.error(f"Streaming execution error: {e}")
    finally:
        # Signal end of stream
        client_queue.put(None)

# STATIC FILES
@app.route('/')
def dashboard():
    """Serve main dashboard"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    api_config = CONFIG['api_server']
    logger.info(f"Starting WARPCORE Agency API Server on {api_config['host']}:{api_config['port']}...")
    logger.info(f"Base directory: {BASE_DIR}")
    logger.info(f"Data directory: {DATA_DIR}")
    logger.info(f"Franchise directory: {FRANCHISE_DIR}")
    app.run(host=api_config['host'], port=api_config['port'], debug=False)
