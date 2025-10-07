#!/usr/bin/env python3
"""
WARPCORE Analytics Dashboard Server
Serves real workflow data from /tmp directory with CORS support
"""

import os
import json
import glob
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
import re

class WARPCOREHandler(SimpleHTTPRequestHandler):
    """Custom handler for WARPCORE dashboard with API endpoints"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory='web', **kwargs)
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

    def do_OPTIONS(self):
        """Handle preflight CORS requests"""
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        """Handle GET requests with API routing"""
        parsed_path = urlparse(self.path)
        
        # API Routes
        if parsed_path.path == '/api/workflow-files':
            self.handle_workflow_files()
        elif parsed_path.path.startswith('/data/'):
            filename = parsed_path.path[6:]  # Remove '/data/' prefix
            self.handle_data_request(filename)
        elif parsed_path.path == '/data/analytics':
            self.handle_analytics_request()
        elif parsed_path.path == '/api/status':
            self.handle_status_request()
        elif parsed_path.path == '/api/execution-logs':
            self.handle_execution_logs_request()
        elif parsed_path.path.startswith('/api/workflow-logs/'):
            workflow_id = parsed_path.path.split('/')[-1]
            self.handle_workflow_logs_request(workflow_id)
        else:
            # Serve static files
            if parsed_path.path == '/' or parsed_path.path == '':
                self.path = '/index.html'
            super().do_GET()

    def handle_workflow_files(self):
        """Return list of workflow files"""
        try:
            workflow_files = []
            patterns = ['.data/wf_*_*.json', '.data/wf_*_seq_*.json']
            
            for pattern in patterns:
                files = glob.glob(pattern)
                for file_path in files:
                    if os.path.isfile(file_path):
                        filename = os.path.basename(file_path)
                        workflow_files.append({
                            'filename': filename,
                            'path': file_path,
                            'size': os.path.getsize(file_path),
                            'modified': os.path.getmtime(file_path)
                        })
            
            workflow_files.sort(key=lambda x: x['modified'], reverse=True)
            self.send_json_response(workflow_files)
            
        except Exception as e:
            self.send_error_response(f"Error listing workflow files: {str(e)}")

    def handle_data_request(self, filename):
        """Serve specific workflow data file"""
        try:
            if not re.match(r'^wf_[a-zA-Z0-9_-]+\.json$', filename):
                self.send_error_response("Invalid filename")
                return
            
            file_path = f'.data/{filename}'
            
            if not os.path.isfile(file_path):
                self.send_error_response(f"File not found: {filename}")
                return
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.send_json_response(data)
            
        except json.JSONDecodeError as e:
            self.send_error_response(f"Invalid JSON in file {filename}: {str(e)}")
        except Exception as e:
            self.send_error_response(f"Error reading file {filename}: {str(e)}")

    def handle_analytics_request(self):
        """Serve the latest analytics orchestrator data"""
        try:
            pattern = '.data/wf_*_seq_004_analytics_orchestration.json'
            analytics_files = glob.glob(pattern)
            
            if not analytics_files:
                pattern = '.data/wf_*analytics*.json'
                analytics_files = glob.glob(pattern)
            
            if not analytics_files:
                self.send_error_response("No analytics data available")
                return
            
            latest_file = max(analytics_files, key=os.path.getmtime)
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.send_json_response(data)
            
        except Exception as e:
            self.send_error_response(f"Error loading analytics data: {str(e)}")

    def handle_status_request(self):
        """Return server and data status"""
        try:
            workflow_count = len(glob.glob('.data/wf_*.json'))
            all_files = glob.glob('.data/wf_*.json')
            latest_timestamp = max([os.path.getmtime(f) for f in all_files]) if all_files else 0
            
            status = {
                'server_status': 'running',
                'workflow_files_count': workflow_count,
                'latest_update': latest_timestamp,
                'data_directory': '.data',
                'server_time': time.time()
            }
            
            self.send_json_response(status)
            
        except Exception as e:
            self.send_error_response(f"Error getting status: {str(e)}")

    def send_json_response(self, data):
        """Send JSON response"""
        json_data = json.dumps(data, indent=2, default=str)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(json_data))
        self.end_headers()
        self.wfile.write(json_data.encode('utf-8'))

    def handle_execution_logs_request(self):
        """Serve recent execution logs"""
        try:
            log_file = '.data/.data/workflow_execution.jsonl'
            if not os.path.exists(log_file):
                # Try alternate location
                log_file = '.data/workflow_execution.jsonl'
            
            if not os.path.exists(log_file):
                self.send_json_response({
                    'logs': [],
                    'message': 'No execution logs found. Run agents to generate logs.'
                })
                return
            
            logs = []
            with open(log_file, 'r') as f:
                lines = f.readlines()[-50:]  # Get last 50 log entries
                for line in lines:
                    try:
                        log_entry = json.loads(line.strip())
                        logs.append(log_entry)
                    except json.JSONDecodeError:
                        continue
            
            # Sort by timestamp (most recent first)
            logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            self.send_json_response({
                'logs': logs,
                'total_entries': len(logs),
                'log_file': log_file
            })
            
        except Exception as e:
            self.send_error_response(f"Error loading execution logs: {str(e)}")
    
    def handle_workflow_logs_request(self, workflow_id):
        """Serve logs for a specific workflow"""
        try:
            log_file = '.data/.data/workflow_execution.jsonl'
            if not os.path.exists(log_file):
                log_file = '.data/workflow_execution.jsonl'
            
            if not os.path.exists(log_file):
                self.send_json_response({
                    'logs': [],
                    'workflow_id': workflow_id,
                    'message': 'No execution logs found'
                })
                return
            
            logs = []
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        if log_entry.get('workflow_id') == workflow_id:
                            logs.append(log_entry)
                    except json.JSONDecodeError:
                        continue
            
            logs.sort(key=lambda x: x.get('timestamp', ''))
            
            # Create execution summary
            summary = {
                'workflow_id': workflow_id,
                'total_log_entries': len(logs),
                'agents_involved': list(set(log.get('agent_name', '') for log in logs)),
                'action_types': {},
                'timeline': logs
            }
            
            for log in logs:
                action_type = log.get('action_type', 'UNKNOWN')
                summary['action_types'][action_type] = summary['action_types'].get(action_type, 0) + 1
            
            self.send_json_response(summary)
            
        except Exception as e:
            self.send_error_response(f"Error loading workflow logs: {str(e)}")

    def send_error_response(self, message):
        """Send error response"""
        error_data = {
            'error': True,
            'message': message,
            'timestamp': time.time()
        }
        json_data = json.dumps(error_data)
        self.send_response(500)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(json_data))
        self.end_headers()
        self.wfile.write(json_data.encode('utf-8'))

    def log_message(self, format, *args):
        """Custom logging"""
        print(f"[{self.date_time_string()}] {format % args}")

def main():
    """Start the WARPCORE dashboard server"""
    PORT = 8080
    HOST = '0.0.0.0'
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    os.chdir(parent_dir)
    
    print(f"Starting WARPCORE Analytics Dashboard Server...")
    print(f"Dashboard URL: http://localhost:{PORT}")
    print(f"Data source: .data/wf_*.json")
    print("-" * 50)
    
    workflow_files = glob.glob('.data/wf_*.json')
    print(f"Found {len(workflow_files)} workflow files")
    for f in sorted(workflow_files)[-3:]:
        print(f"  - {os.path.basename(f)}")
    
    print("-" * 50)
    
    try:
        with HTTPServer((HOST, PORT), WARPCOREHandler) as httpd:
            print(f"✅ Server running at http://localhost:{PORT}")
            print("Press Ctrl+C to stop")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except OSError as e:
        print(f"❌ Server error: {e}")

if __name__ == '__main__':
    main()