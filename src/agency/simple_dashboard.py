#!/usr/bin/env python3
"""
🎯 SIMPLE FRANCHISE DASHBOARD 🎯
Static HTML dashboard with Python HTTP server
"""

import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from franchise_router import load_franchise_router

def generate_dashboard_html():
    """Generate static HTML dashboard"""
    try:
        print("🔄 Loading franchise router...")
        router = load_franchise_router("framer")
        summary = router.get_workflow_summary()
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎯 Franchise Router Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            color: #f8fafc;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{
            text-align: center;
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(124, 58, 237, 0.1));
            border: 1px solid rgba(139, 92, 246, 0.2);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            font-size: 2.5rem;
            background: linear-gradient(135deg, #8b5cf6, #7c3aed);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(139, 92, 246, 0.2);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            transition: transform 0.2s;
        }}
        .stat-card:hover {{ transform: translateY(-2px); }}
        .stat-value {{
            font-size: 2rem;
            font-weight: bold;
            color: #8b5cf6;
            display: block;
            margin-bottom: 5px;
        }}
        .stat-label {{
            color: #cbd5e1;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .panel {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(139, 92, 246, 0.2);
            border-radius: 12px;
            margin-bottom: 20px;
            overflow: hidden;
        }}
        .panel-header {{
            background: rgba(139, 92, 246, 0.1);
            padding: 15px 20px;
            border-bottom: 1px solid rgba(139, 92, 246, 0.1);
            font-weight: 600;
        }}
        .panel-body {{ padding: 20px; }}
        .agent-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 15px;
        }}
        .agent-card {{
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(139, 92, 246, 0.15);
            border-radius: 8px;
            padding: 15px;
            transition: all 0.2s;
        }}
        .agent-card:hover {{
            border-color: rgba(139, 92, 246, 0.4);
            background: rgba(139, 92, 246, 0.05);
        }}
        .agent-name {{
            font-weight: 600;
            color: #8b5cf6;
            margin-bottom: 5px;
        }}
        .agent-position {{
            color: #94a3b8;
            font-size: 0.9rem;
            margin-bottom: 10px;
        }}
        .route-list {{
            list-style: none;
            margin-top: 10px;
        }}
        .route-list li {{
            background: rgba(139, 92, 246, 0.1);
            border-radius: 4px;
            padding: 5px 8px;
            margin: 2px 0;
            font-size: 0.85rem;
        }}
        .loop-badge {{
            background: #f59e0b;
            color: #000;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.7rem;
            margin-left: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Franchise Router Dashboard</h1>
            <p>Dynamic Agent Flow Management - {summary['franchise_name']}</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <span class="stat-value">{summary['total_agents']}</span>
                <span class="stat-label">Total Agents</span>
            </div>
            <div class="stat-card">
                <span class="stat-value">{summary['total_routes']}</span>
                <span class="stat-label">Total Routes</span>
            </div>
            <div class="stat-card">
                <span class="stat-value">{summary['loop_pairs']}</span>
                <span class="stat-label">Loop Pairs</span>
            </div>
            <div class="stat-card">
                <span class="stat-value">{len(summary['entry_points'])}</span>
                <span class="stat-label">Entry Points</span>
            </div>
        </div>

        <div class="panel">
            <div class="panel-header">🤖 Agent Network ({summary['total_agents']} agents)</div>
            <div class="panel-body">
                <div class="agent-grid">"""
        
        # Generate agent cards
        for agent_id, agent_info in summary['agents'].items():
            has_routes = agent_info.get('has_outgoing', False)
            route_count = agent_info.get('route_count', 0)
            
            html += f"""
                    <div class="agent-card">
                        <div class="agent-name">{agent_info['name']}</div>
                        <div class="agent-position">Position: {agent_info['position']} | ID: {agent_id}</div>"""
            
            if has_routes and agent_id in router.config['routing']:
                html += f"""
                        <strong>Routes ({route_count}):</strong>
                        <ul class="route-list">"""
                for route in router.config['routing'][agent_id]:
                    loop_badge = '<span class="loop-badge">LOOP</span>' if route['type'] == 'loop' else ''
                    html += f"""
                            <li>→ {route['target'].upper()} {loop_badge}</li>"""
                html += """
                        </ul>"""
            else:
                html += """
                        <div style="color: #94a3b8; font-style: italic;">No outgoing routes</div>"""
            
            html += """
                    </div>"""
        
        html += f"""
                </div>
            </div>
        </div>

        <div class="panel">
            <div class="panel-header">📊 Flow Summary</div>
            <div class="panel-body">
                <p><strong>Franchise:</strong> {summary['franchise_name']}</p>
                <p><strong>Entry Points:</strong> {', '.join(summary['entry_points'])}</p>
                <p><strong>Completion Points:</strong> {', '.join(summary['completion_points'])}</p>
                <p><strong>Loop Pairs:</strong> {', '.join([f"{loop[0]} ↔ {loop[1]}" for loop in router.config['loops']])}</p>
            </div>
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    except Exception as e:
        return f"""<!DOCTYPE html>
<html><head><title>Error</title></head>
<body style="font-family: monospace; padding: 20px; background: #1a1a1a; color: #ff6b6b;">
<h1>❌ Dashboard Error</h1>
<pre>{str(e)}</pre>
</body></html>"""

def main():
    """Generate dashboard and serve it"""
    print("🎯 Generating franchise dashboard...")
    
    # Generate HTML
    html_content = generate_dashboard_html()
    
    # Write to file
    dashboard_file = Path("dashboard.html")
    dashboard_file.write_text(html_content)
    print(f"✅ Dashboard generated: {dashboard_file.absolute()}")
    
    # Start HTTP server
    class CustomHandler(SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            super().end_headers()
    
    port = 8888
    print(f"🚀 Starting HTTP server on http://localhost:{port}")
    
    server = HTTPServer(('localhost', port), CustomHandler)
    
    try:
        print("📊 Dashboard ready! Opening browser...")
        os.system(f"open http://localhost:{port}/dashboard.html")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        server.shutdown()

if __name__ == "__main__":
    main()