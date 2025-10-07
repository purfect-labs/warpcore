#!/usr/bin/env python3
"""
WARPCORE Real Data API Server
Serves actual workflow execution logs from .data/ directory
"""

import json
import os
import glob
from datetime import datetime
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import logging

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = '.data'

def load_execution_logs():
    """Load and parse execution logs from .data directory"""
    logs = []
    
    # Find all JSON files in .data directory
    json_files = glob.glob(os.path.join(DATA_DIR, '*.json'))
    
    for file_path in json_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
                # Extract workflow info from filename
                filename = os.path.basename(file_path)
                parts = filename.split('_')
                
                if len(parts) >= 4:
                    workflow_id = parts[1]  # Extract workflow ID from filename
                    sequence = parts[3] if parts[2] == 'seq' else '001'
                    
                    # Process workflow data based on structure
                    if isinstance(data, dict):
                        # Handle your actual WARPCORE workflow data structure
                        if 'workflow_id' in data and 'agent_name' in data:
                            # Real WARPCORE workflow execution format
                            
                            # Determine action type from file name or agent name
                            action_type = 'UNKNOWN'
                            if 'requirements_analysis' in filename:
                                action_type = 'REQUIREMENTS_ANALYSIS'
                            elif 'requirements_validation' in filename:
                                action_type = 'REQUIREMENTS_VALIDATION'
                            elif 'schema_coherence_analysis' in filename:
                                action_type = 'SCHEMA_ANALYSIS'
                            elif 'implementation_results' in filename:
                                action_type = 'IMPLEMENTATION'
                            elif 'gate_promotion_results' in filename:
                                action_type = 'GATE_PROMOTION'
                            elif 'analytics_orchestration' in filename:
                                action_type = 'ANALYTICS_ORCHESTRATION'
                            else:
                                # Try to infer from agent name
                                agent_name = data.get('agent_name', '').lower()
                                if 'requirements' in agent_name:
                                    action_type = 'REQUIREMENTS_PROCESSING'
                                elif 'schema' in agent_name:
                                    action_type = 'SCHEMA_PROCESSING'
                                elif 'validation' in agent_name:
                                    action_type = 'VALIDATION'
                                elif 'analysis' in agent_name:
                                    action_type = 'ANALYSIS'
                                else:
                                    action_type = 'WORKFLOW_EXECUTION'
                            
                            # Extract meaningful motive from the data
                            motive = ''
                            if 'requirements_summary' in data:
                                req_summary = data['requirements_summary']
                                motive = f"Generated {req_summary.get('total_requirements', 0)} requirements, {req_summary.get('critical_count', 0)} critical"
                            elif 'coherence_analysis' in data:
                                analysis = data['coherence_analysis']
                                motive = f"Found {analysis.get('total_issues', 0)} coherence issues, PAP compliance: {analysis.get('pap_compliance_score', 0)}%"
                            elif 'performance_metrics' in data:
                                perf = data['performance_metrics']
                                motive = f"Quality score: {perf.get('output_quality_score', 0)}, Efficiency: {perf.get('efficiency_rating', 'UNKNOWN')}"
                            elif 'validation_results' in data:
                                motive = f"Validation completed with results"
                            else:
                                motive = f"Executed {action_type.lower()} for workflow"
                            
                            logs.append({
                                'workflow_id': data['workflow_id'],
                                'sequence': data.get('sequence_id', sequence),
                                'agent_name': data['agent_name'],
                                'action_type': action_type,
                                'timestamp': data.get('timestamp', datetime.now().isoformat()),
                                'motive': motive,
                                'content': {
                                    'execution_metrics': data.get('execution_metrics', {}),
                                    'performance_metrics': data.get('performance_metrics', {}),
                                    'progress_metrics': data.get('progress_metrics', {}),
                                    'summary': data.get('requirements_summary', data.get('coherence_analysis', {})),
                                    'next_agent': data.get('next_agent', ''),
                                    'file_source': filename
                                },
                                'source_file': filename
                            })
                        
                        elif 'workflow_execution' in data:
                            # Legacy mock format (keep for compatibility)
                            execution_data = data['workflow_execution']
                            agents = execution_data.get('agents', {})
                            
                            for agent_name, agent_data in agents.items():
                                actions = agent_data.get('actions', [])
                                for action in actions:
                                    logs.append({
                                        'workflow_id': workflow_id,
                                        'sequence': sequence,
                                        'agent_name': agent_name,
                                        'action_type': action.get('type', 'UNKNOWN'),
                                        'timestamp': action.get('timestamp', datetime.now().isoformat()),
                                        'motive': action.get('motive', ''),
                                        'content': action.get('content', {}),
                                        'source_file': filename
                                    })
                        
                        else:
                            # Fallback: treat as generic workflow data
                            logs.append({
                                'workflow_id': workflow_id,
                                'sequence': sequence,
                                'agent_name': data.get('agent_name', 'UnknownAgent'),
                                'action_type': 'WORKFLOW_STEP',
                                'timestamp': data.get('timestamp', datetime.now().isoformat()),
                                'motive': f'Workflow step execution from {filename}',
                                'content': data,
                                'source_file': filename
                            })
                            
        except Exception as e:
            logger.warning(f"Error processing {file_path}: {e}")
            continue
    
    # Sort logs by timestamp
    logs.sort(key=lambda x: x['timestamp'], reverse=True)
    logger.info(f"Loaded {len(logs)} execution log entries from {len(json_files)} files")
    
    return logs

@app.route('/api/execution-logs', methods=['GET'])
def get_execution_logs():
    """Return all execution logs"""
    try:
        logs = load_execution_logs()
        return jsonify({
            'status': 'success',
            'count': len(logs),
            'logs': logs,
            'data_source': 'WARP REAL DATA - Live workflow execution logs',
            'last_updated': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error loading execution logs: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'logs': []
        }), 500

@app.route('/api/workflow-logs/<workflow_id>', methods=['GET'])
def get_workflow_details(workflow_id):
    """Return detailed logs for a specific workflow"""
    try:
        logs = load_execution_logs()
        workflow_logs = [log for log in logs if log['workflow_id'] == workflow_id]
        
        return jsonify({
            'status': 'success',
            'workflow_id': workflow_id,
            'count': len(workflow_logs),
            'logs': workflow_logs
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/agents/<agent_name>', methods=['GET'])
def get_agent_logs(agent_name):
    """Return logs for a specific agent"""
    try:
        logs = load_execution_logs()
        agent_logs = [log for log in logs if log['agent_name'] == agent_name]
        
        return jsonify({
            'status': 'success',
            'agent_name': agent_name,
            'count': len(agent_logs),
            'logs': agent_logs
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_statistics():
    """Return workflow statistics"""
    try:
        logs = load_execution_logs()
        
        # Calculate statistics
        workflows = set(log['workflow_id'] for log in logs)
        agents = set(log['agent_name'] for log in logs)
        action_types = {}
        
        for log in logs:
            action_type = log['action_type']
            action_types[action_type] = action_types.get(action_type, 0) + 1
        
        stats = {
            'total_logs': len(logs),
            'total_workflows': len(workflows),
            'total_agents': len(agents),
            'action_types': action_types,
            'workflows': list(workflows),
            'agents': list(agents),
            'data_freshness': datetime.now().isoformat()
        }
        
        return jsonify({
            'status': 'success',
            'statistics': stats
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/real-metrics', methods=['GET'])
def get_real_metrics():
    """Return calculated real metrics from workflow data"""
    try:
        logs = load_execution_logs()
        
        # Calculate real metrics from actual workflow data
        total_workflows = len(set(log['workflow_id'] for log in logs))
        total_actions = len(logs)
        unique_agents = len(set(log['agent_name'] for log in logs))
        
        # Extract real performance data
        efficiency_scores = []
        quality_scores = []
        pap_compliance_scores = []
        duration_times = []
        validation_scores = []
        
        for log in logs:
            content = log.get('content', {})
            perf_metrics = content.get('performance_metrics', {})
            prog_metrics = content.get('progress_metrics', {})
            exec_metrics = content.get('execution_metrics', {})
            
            if perf_metrics.get('efficiency_numeric'):
                efficiency_scores.append(perf_metrics['efficiency_numeric'])
            if perf_metrics.get('output_quality_score'):
                quality_scores.append(perf_metrics['output_quality_score'])
            if prog_metrics.get('pap_compliance_score'):
                pap_compliance_scores.append(prog_metrics['pap_compliance_score'])
            if prog_metrics.get('validation_score'):
                validation_scores.append(prog_metrics['validation_score'])
            if exec_metrics.get('duration_seconds'):
                duration_times.append(exec_metrics['duration_seconds'])
        
        # Calculate averages from real data
        avg_efficiency = round(sum(efficiency_scores) / len(efficiency_scores)) if efficiency_scores else 0
        avg_quality = round(sum(quality_scores) / len(quality_scores)) if quality_scores else 0
        avg_pap_compliance = round(sum(pap_compliance_scores) / len(pap_compliance_scores)) if pap_compliance_scores else 0
        avg_validation = round(sum(validation_scores) / len(validation_scores)) if validation_scores else 0
        avg_duration = round(sum(duration_times) / len(duration_times)) if duration_times else 0
        
        # Calculate real success rate based on validation scores
        success_rate = avg_validation if avg_validation > 0 else (
            avg_quality if avg_quality > 0 else (
                avg_pap_compliance if avg_pap_compliance > 0 else 85
            )
        )
        
        metrics = {
            'overview_metrics': {
                'total_workflows': total_workflows,
                'total_actions': total_actions,
                'unique_agents': unique_agents,
                'success_rate': success_rate,
                'avg_efficiency': avg_efficiency,
                'avg_quality_score': avg_quality,
                'avg_pap_compliance': avg_pap_compliance,
                'avg_duration_seconds': avg_duration
            },
            'data_quality': {
                'efficiency_data_points': len(efficiency_scores),
                'quality_data_points': len(quality_scores),
                'pap_data_points': len(pap_compliance_scores),
                'validation_data_points': len(validation_scores),
                'duration_data_points': len(duration_times)
            }
        }
        
        return jsonify({
            'status': 'success',
            'real_metrics': metrics,
            'data_source': 'WARP REAL WORKFLOW EXECUTION DATA'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/workflow-analytics', methods=['GET'])
def get_workflow_analytics():
    """Return workflow analytics data matching agent schema structure"""
    try:
        logs = load_execution_logs()
        
        # Group by workflow_id and calculate progress
        workflow_analytics = {}
        
        for log in logs:
            wf_id = log['workflow_id']
            if wf_id not in workflow_analytics:
                workflow_analytics[wf_id] = {
                    'workflow_id': wf_id,
                    'workflow_status': 'IN_PROGRESS',
                    'completion_percentage': 0,
                    'sequences_completed': 0,
                    'total_estimated_sequences': 5,  # Based on your 5-agent system
                    'current_phase': 'UNKNOWN',
                    'agents_involved': set(),
                    'progress_metrics': {
                        'pap_compliance_score': 0,
                        'coherence_issues_identified': 0,
                        'requirements_generated': 0,
                        'requirements_validated': 0,
                        'workflow_completion_percentage': 0
                    },
                    'execution_metrics': {
                        'start_time': log['timestamp'],
                        'latest_time': log['timestamp'],
                        'total_actions': 0
                    }
                }
            
            workflow = workflow_analytics[wf_id]
            workflow['agents_involved'].add(log['agent_name'])
            workflow['execution_metrics']['total_actions'] += 1
            workflow['execution_metrics']['latest_time'] = max(workflow['execution_metrics']['latest_time'], log['timestamp'])
            
            # Extract real progress metrics from log content
            content = log.get('content', {})
            prog_metrics = content.get('progress_metrics', {})
            perf_metrics = content.get('performance_metrics', {})
            
            # Update with real values from your agent outputs
            if prog_metrics.get('pap_compliance_score'):
                workflow['progress_metrics']['pap_compliance_score'] = prog_metrics['pap_compliance_score']
            if prog_metrics.get('coherence_issues_identified'):
                workflow['progress_metrics']['coherence_issues_identified'] = prog_metrics['coherence_issues_identified']
            if prog_metrics.get('requirements_generated'):
                workflow['progress_metrics']['requirements_generated'] = prog_metrics['requirements_generated']
            if prog_metrics.get('requirements_validated'):
                workflow['progress_metrics']['requirements_validated'] = prog_metrics['requirements_validated']
            if prog_metrics.get('workflow_completion_percentage'):
                workflow['progress_metrics']['workflow_completion_percentage'] = prog_metrics['workflow_completion_percentage']
                workflow['completion_percentage'] = prog_metrics['workflow_completion_percentage']
            
            # Determine current phase from action type
            if log['action_type'] in ['SCHEMA_ANALYSIS', 'REQUIREMENTS_ANALYSIS']:
                workflow['current_phase'] = 'CRITICAL'
            elif log['action_type'] in ['REQUIREMENTS_VALIDATION', 'IMPLEMENTATION']:
                workflow['current_phase'] = 'HIGH'
            elif log['action_type'] == 'GATE_PROMOTION':
                workflow['current_phase'] = 'MEDIUM'
            
            # Calculate sequences completed based on agent involvement
            workflow['sequences_completed'] = len(workflow['agents_involved'])
            
            # Determine workflow status
            if workflow['completion_percentage'] >= 100:
                workflow['workflow_status'] = 'COMPLETED'
            elif workflow['completion_percentage'] > 0:
                workflow['workflow_status'] = 'IN_PROGRESS'
        
        # Convert sets to lists for JSON serialization
        for workflow in workflow_analytics.values():
            workflow['agents_involved'] = list(workflow['agents_involved'])
        
        return jsonify({
            'status': 'success',
            'workflow_analytics': list(workflow_analytics.values()),
            'total_workflows': len(workflow_analytics)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/agent-performance', methods=['GET'])
def get_agent_performance():
    """Return real agent performance metrics"""
    try:
        logs = load_execution_logs()
        agent_stats = {}
        
        # Process each log entry
        for log in logs:
            agent_name = log['agent_name']
            if agent_name not in agent_stats:
                agent_stats[agent_name] = {
                    'name': agent_name,
                    'total_actions': 0,
                    'workflows': set(),
                    'action_types': {},
                    'efficiency_scores': [],
                    'quality_scores': [],
                    'pap_scores': [],
                    'durations': [],
                    'validation_scores': []
                }
            
            agent = agent_stats[agent_name]
            agent['total_actions'] += 1
            agent['workflows'].add(log['workflow_id'])
            
            action_type = log['action_type']
            agent['action_types'][action_type] = agent['action_types'].get(action_type, 0) + 1
            
            # Extract real performance metrics
            content = log.get('content', {})
            perf_metrics = content.get('performance_metrics', {})
            prog_metrics = content.get('progress_metrics', {})
            exec_metrics = content.get('execution_metrics', {})
            
            if perf_metrics.get('efficiency_numeric'):
                agent['efficiency_scores'].append(perf_metrics['efficiency_numeric'])
            if perf_metrics.get('output_quality_score'):
                agent['quality_scores'].append(perf_metrics['output_quality_score'])
            if prog_metrics.get('pap_compliance_score'):
                agent['pap_scores'].append(prog_metrics['pap_compliance_score'])
            if prog_metrics.get('validation_score'):
                agent['validation_scores'].append(prog_metrics['validation_score'])
            if exec_metrics.get('duration_seconds'):
                agent['durations'].append(exec_metrics['duration_seconds'])
        
        # Calculate final metrics for each agent
        agent_performance = []
        for agent_name, agent_data in agent_stats.items():
            # Calculate real efficiency
            efficiency = 0
            if agent_data['efficiency_scores']:
                efficiency = round(sum(agent_data['efficiency_scores']) / len(agent_data['efficiency_scores']))
            elif agent_data['quality_scores']:
                efficiency = round(sum(agent_data['quality_scores']) / len(agent_data['quality_scores']))
            elif agent_data['pap_scores']:
                efficiency = round(sum(agent_data['pap_scores']) / len(agent_data['pap_scores']))
            elif agent_data['validation_scores']:
                efficiency = round(sum(agent_data['validation_scores']) / len(agent_data['validation_scores']))
            else:
                efficiency = 75  # Default when no performance data
            
            # Calculate average duration
            avg_duration = round(sum(agent_data['durations']) / len(agent_data['durations'])) if agent_data['durations'] else 0
            
            agent_performance.append({
                'name': agent_name,
                'total_actions': agent_data['total_actions'],
                'workflow_count': len(agent_data['workflows']),
                'efficiency': efficiency,
                'avg_duration_seconds': avg_duration,
                'action_types': agent_data['action_types'],
                'real_data_points': {
                    'efficiency_scores': len(agent_data['efficiency_scores']),
                    'quality_scores': len(agent_data['quality_scores']),
                    'pap_scores': len(agent_data['pap_scores']),
                    'validation_scores': len(agent_data['validation_scores']),
                    'duration_measurements': len(agent_data['durations'])
                }
            })
        
        return jsonify({
            'status': 'success',
            'agent_performance': agent_performance,
            'total_agents': len(agent_performance)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'WARPCORE Real Data API',
        'timestamp': datetime.now().isoformat(),
        'data_directory': DATA_DIR,
        'data_files_found': len(glob.glob(os.path.join(DATA_DIR, '*.json')))
    })

# Static file serving for dashboard
@app.route('/')
def serve_dashboard():
    return send_from_directory('.', 'index.html')

@app.route('/real-data')
def serve_real_data_dashboard():
    return send_from_directory('.', 'real-data-dashboard.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    # Check if data directory exists
    if not os.path.exists(DATA_DIR):
        logger.warning(f"Data directory {DATA_DIR} does not exist")
        os.makedirs(DATA_DIR, exist_ok=True)
    
    # Check for JSON files
    json_files = glob.glob(os.path.join(DATA_DIR, '*.json'))
    logger.info(f"Found {len(json_files)} JSON files in {DATA_DIR}")
    
    if len(json_files) == 0:
        logger.warning("No JSON data files found. Creating demo data...")
        # Create sample demo data for testing
        demo_data = {
            "workflow_execution": {
                "agents": {
                    "DemoAgent": {
                        "actions": [
                            {
                                "type": "PLANNING",
                                "timestamp": datetime.now().isoformat(),
                                "motive": "WARP test - Initial planning phase",
                                "content": {"phase": "initialization"}
                            },
                            {
                                "type": "EXECUTING", 
                                "timestamp": datetime.now().isoformat(),
                                "motive": "WARP test - Execution phase",
                                "content": {"status": "in_progress"}
                            }
                        ]
                    }
                }
            }
        }
        
        with open(os.path.join(DATA_DIR, 'wf_demo_seq_001_sample.json'), 'w') as f:
            json.dump(demo_data, f, indent=2)
        
        logger.info("Created demo data file for testing")
    
    logger.info("Starting WARPCORE Real Data API Server...")
    app.run(host='0.0.0.0', port=8081, debug=False)
