#!/usr/bin/env python3
"""
🎯 FRANCHISE ROUTER DASHBOARD 🎯
Interactive web dashboard for dynamic agent routing
"""

import json
from flask import Flask, render_template_string, jsonify, request
from franchise_router import load_franchise_router

app = Flask(__name__)

# HTML template for the dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎯 Franchise Router Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            color: #f8fafc;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header {
            text-align: center;
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(124, 58, 237, 0.1));
            border: 1px solid rgba(139, 92, 246, 0.2);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 2.5rem;
            background: linear-gradient(135deg, #8b5cf6, #7c3aed);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(139, 92, 246, 0.2);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            transition: transform 0.2s;
        }
        .stat-card:hover { transform: translateY(-2px); }
        .stat-value {
            font-size: 2rem;
            font-weight: bold;
            color: #8b5cf6;
            display: block;
            margin-bottom: 5px;
        }
        .stat-label {
            color: #cbd5e1;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .panel {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(139, 92, 246, 0.2);
            border-radius: 12px;
            margin-bottom: 20px;
            overflow: hidden;
        }
        .panel-header {
            background: rgba(139, 92, 246, 0.1);
            padding: 15px 20px;
            border-bottom: 1px solid rgba(139, 92, 246, 0.1);
            font-weight: 600;
        }
        .panel-body { padding: 20px; }
        .agent-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 15px;
        }
        .agent-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(139, 92, 246, 0.15);
            border-radius: 8px;
            padding: 15px;
            transition: all 0.2s;
        }
        .agent-card:hover {
            border-color: rgba(139, 92, 246, 0.4);
            background: rgba(139, 92, 246, 0.05);
        }
        .agent-name {
            font-weight: 600;
            color: #8b5cf6;
            margin-bottom: 5px;
        }
        .agent-position {
            color: #94a3b8;
            font-size: 0.9rem;
            margin-bottom: 10px;
        }
        .route-list {
            list-style: none;
            margin-top: 10px;
        }
        .route-list li {
            background: rgba(139, 92, 246, 0.1);
            border-radius: 4px;
            padding: 5px 8px;
            margin: 2px 0;
            font-size: 0.85rem;
        }
        .loop-badge {
            background: #f59e0b;
            color: #000;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.7rem;
            margin-left: 5px;
        }
        .control-panel {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(139, 92, 246, 0.2);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .control-row {
            display: flex;
            gap: 15px;
            align-items: center;
            margin-bottom: 15px;
        }
        select, input {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(139, 92, 246, 0.3);
            border-radius: 6px;
            padding: 8px 12px;
            color: #f8fafc;
            font-size: 0.9rem;
        }
        button {
            background: linear-gradient(135deg, #8b5cf6, #7c3aed);
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            color: white;
            font-weight: 500;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover { transform: translateY(-1px); }
        .result-box {
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(139, 92, 246, 0.2);
            border-radius: 8px;
            padding: 15px;
            font-family: monospace;
            white-space: pre-wrap;
            margin-top: 15px;
            min-height: 100px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Franchise Router Dashboard</h1>
            <p>Dynamic Agent Flow Management</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <span class="stat-value" id="total-agents">{{ summary.total_agents }}</span>
                <span class="stat-label">Total Agents</span>
            </div>
            <div class="stat-card">
                <span class="stat-value" id="total-routes">{{ summary.total_routes }}</span>
                <span class="stat-label">Total Routes</span>
            </div>
            <div class="stat-card">
                <span class="stat-value" id="loop-pairs">{{ summary.loop_pairs }}</span>
                <span class="stat-label">Loop Pairs</span>
            </div>
            <div class="stat-card">
                <span class="stat-value" id="entry-points">{{ summary.entry_points|length }}</span>
                <span class="stat-label">Entry Points</span>
            </div>
        </div>

        <div class="control-panel">
            <h3>🔀 Route Explorer</h3>
            <div class="control-row">
                <label>From Agent:</label>
                <select id="from-agent">
                    {% for agent_id in summary.agents.keys() %}
                    <option value="{{ agent_id }}">{{ summary.agents[agent_id].name }} ({{ agent_id }})</option>
                    {% endfor %}
                </select>
                <button onclick="getNextAgents()">Get Next Agents</button>
            </div>
            <div class="control-row">
                <label>To Agent:</label>
                <select id="to-agent">
                    {% for agent_id in summary.agents.keys() %}
                    <option value="{{ agent_id }}">{{ summary.agents[agent_id].name }} ({{ agent_id }})</option>
                    {% endfor %}
                </select>
                <button onclick="findPath()">Find Path</button>
            </div>
            <div class="result-box" id="results">Select an agent to explore routing options...</div>
        </div>

        <div class="panel">
            <div class="panel-header">🤖 Agent Network ({{ summary.total_agents }} agents)</div>
            <div class="panel-body">
                <div class="agent-grid">
                    {% for agent_id, agent_info in summary.agents.items() %}
                    <div class="agent-card">
                        <div class="agent-name">{{ agent_info.name }}</div>
                        <div class="agent-position">Position: {{ agent_info.position }} | ID: {{ agent_id }}</div>
                        {% if agent_info.has_outgoing %}
                        <strong>Routes ({{ agent_info.route_count }}):</strong>
                        <ul class="route-list">
                            {% for route in routing[agent_id] %}
                            <li>
                                → {{ route.target.upper() }}
                                {% if route.type == 'loop' %}<span class="loop-badge">LOOP</span>{% endif %}
                            </li>
                            {% endfor %}
                        </ul>
                        {% else %}
                        <div style="color: #94a3b8; font-style: italic;">No outgoing routes</div>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>

        <div class="panel">
            <div class="panel-header">📊 Flow Summary</div>
            <div class="panel-body">
                <p><strong>Franchise:</strong> {{ summary.franchise_name }}</p>
                <p><strong>Entry Points:</strong> {{ summary.entry_points|join(', ') }}</p>
                <p><strong>Completion Points:</strong> {{ summary.completion_points|join(', ') }}</p>
                <p><strong>Loop Pairs:</strong> 
                {% for loop in loops %}
                    {{ loop[0] }} ↔ {{ loop[1] }}{% if not loop_last %}, {% endif %}
                {% endfor %}
                </p>
            </div>
        </div>
    </div>

    <script>
        function getNextAgents() {
            const fromAgent = document.getElementById('from-agent').value;
            fetch(`/api/next-agents/${fromAgent}`)
                .then(response => response.json())
                .then(data => {
                    const results = document.getElementById('results');
                    if (data.next_agents && data.next_agents.length > 0) {
                        let output = `Next agents from ${data.agent_name}:\\n`;
                        data.next_agents.forEach(agent => {
                            const loopBadge = agent.is_loop ? ' [LOOP]' : '';
                            output += `→ ${agent.agent_name} (${agent.condition})${loopBadge}\\n`;
                        });
                        results.textContent = output;
                    } else {
                        results.textContent = `No outgoing routes from ${fromAgent}`;
                    }
                })
                .catch(error => {
                    document.getElementById('results').textContent = `Error: ${error.message}`;
                });
        }

        function findPath() {
            const fromAgent = document.getElementById('from-agent').value;
            const toAgent = document.getElementById('to-agent').value;
            
            fetch(`/api/path/${fromAgent}/${toAgent}`)
                .then(response => response.json())
                .then(data => {
                    const results = document.getElementById('results');
                    if (data.path && data.path.length > 0) {
                        results.textContent = `Path from ${fromAgent} to ${toAgent}:\\n${data.path.join(' → ')}`;
                    } else {
                        results.textContent = `No path found from ${fromAgent} to ${toAgent}`;
                    }
                })
                .catch(error => {
                    document.getElementById('results').textContent = `Error: ${error.message}`;
                });
        }
    </script>
</body>
</html>
"""

# Load router
router = None

@app.route('/')
def dashboard():
    try:
        global router
        if not router:
            router = load_franchise_router("framer")
        
        summary = router.get_workflow_summary()
        
        return render_template_string(DASHBOARD_HTML, 
                                    summary=summary,
                                    routing=router.config['routing'],
                                    loops=router.config['loops'])
    except Exception as e:
        return f"Error loading dashboard: {e}", 500

@app.route('/api/next-agents/<agent_id>')
def api_next_agents(agent_id):
    try:
        next_agents = router.get_next_agents(agent_id)
        agent_info = router.get_agent_info(agent_id)
        return jsonify({
            'agent_id': agent_id,
            'agent_name': agent_info['name'] if agent_info else agent_id.upper(),
            'next_agents': next_agents
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/path/<from_agent>/<to_agent>')
def api_path(from_agent, to_agent):
    try:
        path = router.get_workflow_path(from_agent, to_agent)
        return jsonify({
            'from': from_agent,
            'to': to_agent,
            'path': path
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/summary')
def api_summary():
    try:
        return jsonify(router.get_workflow_summary())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🎯 Starting Franchise Router Dashboard...")
    print("📊 Dashboard: http://localhost:5555")
    app.run(host='localhost', port=5555, debug=True)