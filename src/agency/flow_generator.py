#!/usr/bin/env python3
"""
WARPCORE Agency Flow Generator
Parses real agent JSON files and generates dynamic Mermaid flow diagrams
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class AgentFlowGenerator:
    def __init__(self, agents_dir: str = None):
        self.agents_dir = Path(agents_dir) if agents_dir else Path(__file__).parent / "agents"
        self.docs_dir = Path(__file__).parent.parent.parent / "docs" / "agency"
        self.agents_data = {}
        self.flow_relationships = {}
        
    def parse_agent_files(self) -> Dict[str, Any]:
        """Parse all agent JSON files and extract flow relationships"""
        print("🔍 Parsing agent files for flow relationships...")
        
        agents = {}
        relationships = []
        
        # Find all agent JSON files
        agent_files = list(self.agents_dir.glob("*.json"))
        agent_files = [f for f in agent_files if not f.name.startswith('.') and f.name != 'mama_bear.json']
        
        print(f"📁 Found {len(agent_files)} agent files")
        
        for agent_file in sorted(agent_files):
            try:
                with open(agent_file, 'r') as f:
                    agent_data = json.load(f)
                
                # Extract key info from filename and data
                filename = agent_file.stem
                agent_id = agent_data.get('agent_id', self._extract_agent_name(filename))
                
                # Parse position from filename (e.g., "0a", "2b", "3")
                position = self._extract_position(filename)
                
                # Extract inputs and outputs from filename pattern
                inputs, outputs = self._parse_filename_flow(filename)
                
                # Also check JSON data for relationships
                json_deps = agent_data.get('dependencies', [])
                json_outputs = agent_data.get('outputs_to', [])
                
                # Extract real cache patterns
                cache_pattern = agent_data.get('cache_pattern', '')
                input_cache_pattern = agent_data.get('input_cache_pattern', '')
                
                agent_info = {
                    'id': agent_id,
                    'filename': filename,
                    'position': position,
                    'inputs_from_filename': inputs,
                    'outputs_from_filename': outputs,
                    'dependencies_from_json': json_deps,
                    'outputs_to_from_json': json_outputs,
                    'role': self._extract_role(agent_data.get('prompt', '')),
                    'workflow_position': agent_data.get('workflow_position', position),
                    'cache_pattern': agent_data.get('cache_pattern', ''),
                    'validation_rules': agent_data.get('validation_rules', []),
                    'success_criteria': agent_data.get('success_criteria', [])
                }
                
                agents[agent_id] = agent_info
                print(f"  ✅ {agent_id} ({filename})")
                
            except Exception as e:
                print(f"  ❌ Error parsing {agent_file}: {e}")
        
        self.agents_data = agents
        return agents
    
    
    def _extract_position(self, filename: str) -> str:
        """Extract position from filename (e.g., '0a', '2b', '3')"""
        match = re.match(r'^([0-9]+[ab]?|neg[0-9]+)', filename)
        if match:
            pos = match.group(1)
            return pos.replace('neg', '-')
        return '?'
    
    def _extract_agent_name(self, filename: str) -> str:
        """Extract agent name from filename"""
        # Pattern: position_name_from_inputs_to_outputs
        parts = filename.split('_')
        if len(parts) >= 2:
            return parts[1]  # Second part is usually the agent name
        return filename
    
    def _parse_filename_flow(self, filename: str) -> tuple:
        """Parse input/output relationships from filename"""
        # Pattern: position_agent_from_inputs_to_outputs
        inputs = []
        outputs = []
        
        if '_from_' in filename and '_to_' in filename:
            try:
                from_part = filename.split('_from_')[1].split('_to_')[0]
                to_part = filename.split('_to_')[1]
                
                # Parse inputs
                if from_part and from_part != 'none':
                    inputs = [inp.strip() for inp in from_part.split('_') if inp.strip()]
                
                # Parse outputs
                if to_part and to_part != 'complete' and to_part != 'end':
                    outputs = [out.strip() for out in to_part.split('_') if out.strip()]
                
            except Exception as e:
                print(f"  ⚠️ Error parsing flow from {filename}: {e}")
        
        return inputs, outputs
    
    def _extract_role(self, prompt: str) -> str:
        """Extract role description from agent prompt"""
        if '## ROLE' in prompt:
            role_section = prompt.split('## ROLE')[1].split('##')[0]
            # Get first meaningful line
            lines = [line.strip() for line in role_section.split('\n') if line.strip()]
            if lines:
                return lines[0].replace('You are the', '').replace('**', '').strip()
        return "Agent"
    
    def generate_mermaid_flow(self) -> str:
        """Generate Mermaid flowchart using comprehensive schema definition"""
        if not self.agents_data:
            self.parse_agent_files()
        
        print("🎨 Generating Mermaid flow diagram from schema definition...")
        
        mermaid = "flowchart TD\n"
        
        # Use schema definitions if available
        if self.flow_schema and 'agent_definitions' in self.flow_schema:
            schema_agents = self.flow_schema['agent_definitions']
            
            # Generate nodes from schema
            for agent_key, agent_def in schema_agents.items():
                position = agent_def['position']
                name = agent_def['name']
                role = agent_def['role'][:25] + "..." if len(agent_def['role']) > 25 else agent_def['role']
                
                mermaid += f'    {position}["{position}<br/>{name}<br/>{role}"]\n'
            
            # Add external USER node
            mermaid += '    USER(["👤 USER<br/>Requirements Input"])\n'
            
            # Generate connections from schema
            if 'flow_relationships' in self.flow_schema:
                relationships = self.flow_schema['flow_relationships']
                
                # Linear flow connections
                for flow in relationships.get('linear_flow', []):
                    from_agent = schema_agents[flow['from']]['position']
                    to_agent = schema_agents[flow['to']]['position']
                    flow_type = flow.get('type', '')
                    
                    if flow_type:
                        mermaid += f'    {from_agent} -->|"{flow_type}"| {to_agent}\n'
                    else:
                        mermaid += f'    {from_agent} --> {to_agent}\n'
                
                # Decision flow connections
                for decision in relationships.get('decision_flows', []):
                    from_pos = schema_agents[decision['from']]['position']
                    
                    for target in decision['to']:
                        to_pos = schema_agents[target]['position']
                        condition = decision['conditions'][target]
                        
                        mermaid += f'    {from_pos} -->|"{condition}"| {to_pos}\n'
                
                # External input connections
                for ext_input in relationships.get('external_inputs', []):
                    source = ext_input['source']
                    target_pos = schema_agents[ext_input['to']]['position']
                    input_type = ext_input['type']
                    
                    mermaid += f'    {source} -->|"{input_type}"| {target_pos}\n'
        
        else:
            # Fallback to original parsing if schema not available
            print("⚠️ Using fallback agent parsing (schema not available)")
            sorted_agents = sorted(self.agents_data.values(), key=lambda x: self._sort_key(x['position']))
            
            # Generate nodes
            for agent in sorted_agents:
                node_id = agent['position']
                agent_name = agent['id'].upper()
                role = agent['role'][:20] + "..." if len(agent['role']) > 20 else agent['role']
                
                mermaid += f'    {node_id}["{node_id}<br/>{agent_name}<br/>{role}"]\n'
        
            # Define fallback flow relationships
            correct_flow = [
                ("0a", "0b", ""),           # ORIGIN → BOSS
                ("0b", "1", ""),            # BOSS → PATHFINDER
                ("1", "2a", ""),            # PATHFINDER → ARCHITECT
                ("2b", "2a", "USER INPUT"),  # ORACLE → ARCHITECT (from user)
                ("2a", "3", ""),            # ARCHITECT → ENFORCER
                ("3", "4a", ""),            # ENFORCER → CRAFTSMAN
                ("4a", "4b", ""),           # CRAFTSMAN → CRAFTBUDDY
                ("4b", "4a", "Loop Back"),  # CRAFTBUDDY → CRAFTSMAN (loop)
                ("4b", "5", "Promote"),     # CRAFTBUDDY → GATEKEEPER (promote)
                ("5", "4a", "Need Fixes"),  # GATEKEEPER → CRAFTSMAN (fixes)
                ("5", "0b", "New Cycle")    # GATEKEEPER → BOSS (new cycle)
            ]
            
            # Generate connections
            for source, target, label in correct_flow:
                if self._has_agent_at_position(source) and self._has_agent_at_position(target):
                    if label:
                        mermaid += f'    {source} -->|"{label}"| {target}\n'
                    else:
                        mermaid += f'    {source} --> {target}\n'
                elif source == "2b" and target == "2a":  # Special case for Oracle from external
                    mermaid += f'    {source} -->|"{label}"| {target}\n'
            
            # Add external source for Oracle
            mermaid += '    USER(["👤 USER<br/>Requirements"]) --> 2b\n'
        
        # Add styling
        mermaid += """
    
    %% Styling
    classDef origin fill:#ff6b6b,stroke:#333,stroke-width:2px
    classDef boss fill:#4ecdc4,stroke:#333,stroke-width:2px
    classDef pathfinder fill:#45b7d1,stroke:#333,stroke-width:2px
    classDef oracle fill:#ffeaa7,stroke:#333,stroke-width:2px
    classDef architect fill:#96ceb4,stroke:#333,stroke-width:2px
    classDef enforcer fill:#fab1a0,stroke:#333,stroke-width:2px
    classDef craftsman fill:#fd79a8,stroke:#333,stroke-width:2px
    classDef craftbuddy fill:#e17055,stroke:#333,stroke-width:2px
    classDef gatekeeper fill:#00b894,stroke:#333,stroke-width:2px
    classDef complete fill:#a8e6cf,stroke:#333,stroke-width:2px
"""
        
        # Apply styles based on schema or agent data
        if self.flow_schema and 'agent_definitions' in self.flow_schema:
            # Use schema definitions for styling
            for agent_key, agent_def in self.flow_schema['agent_definitions'].items():
                pos = agent_def['position']
                name = agent_key.lower()
                
                if 'origin' in name:
                    mermaid += f"    class {pos} origin\n"
                elif 'boss' in name:
                    mermaid += f"    class {pos} boss\n"
                elif 'pathfinder' in name:
                    mermaid += f"    class {pos} pathfinder\n"
                elif 'oracle' in name:
                    mermaid += f"    class {pos} oracle\n"
                elif 'architect' in name:
                    mermaid += f"    class {pos} architect\n"
                elif 'enforcer' in name:
                    mermaid += f"    class {pos} enforcer\n"
                elif 'craftsman' in name:
                    mermaid += f"    class {pos} craftsman\n"
                elif 'craftbuddy' in name or 'buddy' in name:
                    mermaid += f"    class {pos} craftbuddy\n"
                elif 'gatekeeper' in name:
                    mermaid += f"    class {pos} gatekeeper\n"
        else:
            # Apply styles using parsed agent data
            sorted_agents = sorted(self.agents_data.values(), key=lambda x: self._sort_key(x['position']))
            for agent in sorted_agents:
                pos = agent['position']
                name = agent['id'].lower()
                
                if 'origin' in name:
                    mermaid += f"    class {pos} origin\n"
                elif 'boss' in name:
                    mermaid += f"    class {pos} boss\n"
                elif 'pathfinder' in name:
                    mermaid += f"    class {pos} pathfinder\n"
                elif 'oracle' in name:
                    mermaid += f"    class {pos} oracle\n"
                elif 'architect' in name:
                    mermaid += f"    class {pos} architect\n"
                elif 'enforcer' in name:
                    mermaid += f"    class {pos} enforcer\n"
                elif 'craftsman' in name:
                    mermaid += f"    class {pos} craftsman\n"
                elif 'craftbuddy' in name or 'buddy' in name:
                    mermaid += f"    class {pos} craftbuddy\n"
                elif 'gatekeeper' in name:
                    mermaid += f"    class {pos} gatekeeper\n"
        
        return mermaid
    
    def _sort_key(self, position: str) -> tuple:
        """Generate sort key for position ordering"""
        if position.startswith('-'):
            return (-1, int(position[1:]), 'a')
        
        match = re.match(r'^([0-9]+)([ab]?)$', position)
        if match:
            num = int(match.group(1))
            suffix = match.group(2) or 'a'
            return (0, num, suffix)
        
        return (1, 999, position)
    
    def _find_agent_by_name_or_pos(self, identifier: str) -> Optional[Dict]:
        """Find agent by name or position identifier"""
        identifier = identifier.lower()
        
        for agent in self.agents_data.values():
            if (identifier in agent['id'].lower() or 
                identifier == agent['position'] or
                identifier in agent['filename'].lower()):
                return agent
        return None
    
    def _has_agent_at_position(self, position: str) -> bool:
        """Check if an agent exists at the given position"""
        return any(agent['position'] == position for agent in self.agents_data.values())
    
    def generate_html_documentation(self) -> str:
        """Generate complete HTML documentation with Mermaid flow"""
        if not self.agents_data:
            self.parse_agent_files()
        
        mermaid_flow = self.generate_mermaid_flow()
        timestamp = datetime.now().isoformat()
        
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WARPCORE Agent System - Flow Documentation</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
    <style>
        {self._get_css_styles()}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 WARPCORE Agent System</h1>
            <p>Dynamic Flow Documentation - Generated from Real Agent Schemas</p>
            <p class="watermark">🚀 WARP-DEMO FLOW SYSTEM - Generated: {timestamp}</p>
        </div>

        <div class="tab-container">
            <div class="tab-nav">
                <button class="tab-button active" onclick="showTab('flow')">📊 Flow</button>
                <button class="tab-button" onclick="showTab('agents')">🤖 Agents</button>
                <button class="tab-button" onclick="showTab('schema')">📋 Schema</button>
                <button class="tab-button" onclick="showTab('files')">📁 Files</button>
            </div>

            <!-- Flow Tab -->
            <div id="flow-tab" class="tab-content active">
                <div class="tab-pane">
                    <div class="stats-grid">
                        {self._generate_stats_html()}
                    </div>
                    <div class="mermaid-container">
                        <div class="mermaid">
{mermaid_flow}
                        </div>
                    </div>
                    {self._generate_flow_patterns_html()}
                </div>
            </div>

            <!-- Agents Tab -->
            <div id="agents-tab" class="tab-content">
                <div class="tab-pane">
                    <div class="agent-grid">
                        {self._generate_agent_cards_html()}
                    </div>
                </div>
            </div>

            <!-- Schema Tab -->
            <div id="schema-tab" class="tab-content">
                <div class="tab-pane">
                    <h3>📋 Agent Schema Analysis</h3>
                    <div class="schema-preview">
{self._generate_schema_json()}
                    </div>
                </div>
            </div>

            <!-- Files Tab -->
            <div id="files-tab" class="tab-content">
                <div class="tab-pane">
                    <h3>📁 Agent Files - Current Structure</h3>
                    <div class="file-list">
                        {self._generate_file_list_html()}
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        {self._get_javascript()}
    </script>
</body>
</html>"""
        
        return html_template
    
    def _generate_stats_html(self) -> str:
        """Generate statistics HTML"""
        total_agents = len(self.agents_data)
        
        # Count by position types
        origin_agents = sum(1 for a in self.agents_data.values() if a['position'].startswith('-') or 'origin' in a['id'])
        boss_agents = sum(1 for a in self.agents_data.values() if a['position'] == '0' or 'boss' in a['id'])
        
        return f"""
                        <div class="stat-card">
                            <span class="stat-value">{total_agents}</span>
                            <span class="stat-label">Total Agents</span>
                        </div>
                        <div class="stat-card">
                            <span class="stat-value">{len(self._get_unique_positions())}</span>
                            <span class="stat-label">Unique Positions</span>
                        </div>
                        <div class="stat-card">
                            <span class="stat-value">{self._count_loops()}</span>
                            <span class="stat-label">Loop Patterns</span>
                        </div>
                        <div class="stat-card">
                            <span class="stat-value">{self._count_parallel()}</span>
                            <span class="stat-label">Parallel Flows</span>
                        </div>
        """
    
    def _generate_agent_cards_html(self) -> str:
        """Generate agent cards HTML"""
        cards_html = ""
        sorted_agents = sorted(self.agents_data.values(), key=lambda x: self._sort_key(x['position']))
        
        colors = {
            'origin': '#ff6b6b', 'boss': '#4ecdc4', 'pathfinder': '#45b7d1',
            'oracle': '#ffeaa7', 'architect': '#96ceb4', 'enforcer': '#fab1a0',
            'craftsman': '#fd79a8', 'craftbuddy': '#e17055', 'gatekeeper': '#00b894'
        }
        
        for agent in sorted_agents:
            color = '#00ff88'  # default
            for name, agent_color in colors.items():
                if name in agent['id'].lower():
                    color = agent_color
                    break
            
            inputs = ', '.join(agent['inputs_from_filename']) if agent['inputs_from_filename'] else 'None'
            outputs = ', '.join(agent['outputs_from_filename']) if agent['outputs_from_filename'] else 'End'
            
            cards_html += f"""
                        <div class="agent-card">
                            <div class="agent-header">
                                <div class="agent-position" style="background: {color};">{agent['position']}</div>
                                <div class="agent-info">
                                    <h3>{agent['id'].upper()}</h3>
                                    <div class="role">{agent['role']}</div>
                                </div>
                            </div>
                            <div class="agent-details">
                                <div><strong>File:</strong> {agent['filename']}.json</div>
                                <div><strong>Inputs:</strong> {inputs}</div>
                                <div><strong>Outputs:</strong> {outputs}</div>
                                <div><strong>Cache:</strong> {agent['cache_pattern']}</div>
                            </div>
                        </div>
            """
        
        return cards_html
    
    def _generate_file_list_html(self) -> str:
        """Generate file list HTML"""
        files_html = ""
        sorted_agents = sorted(self.agents_data.values(), key=lambda x: self._sort_key(x['position']))
        
        for agent in sorted_agents:
            files_html += f'<div class="file-item">{agent["filename"]}.json</div>\n'
        
        return files_html
    
    def _generate_schema_json(self) -> str:
        """Generate schema JSON representation"""
        if self.flow_schema:
            # Use the comprehensive schema if available
            display_schema = {
                "flow_pattern": self.flow_schema.get('flow_pattern', 'WARPCORE Agent Flow'),
                "schema_version": self.flow_schema.get('schema_version', '1.0.0'),
                "generated_from": "Comprehensive schema definition + real agent files",
                "timestamp": datetime.now().isoformat(),
                "watermark": self.flow_schema.get('watermark', '🚀 WARP-DEMO FLOW'),
                "agent_definitions": self.flow_schema.get('agent_definitions', {}),
                "flow_relationships": self.flow_schema.get('flow_relationships', {}),
                "schema_transformations": self.flow_schema.get('schema_transformations', {}),
                "flow_patterns": self.flow_schema.get('flow_patterns', {})
            }
        else:
            # Fallback to parsed agent data
            display_schema = {
                "flow_pattern": "Dynamic WARPCORE Agent Data Flow",
                "generated_from": "Real agent JSON files (fallback)",
                "timestamp": datetime.now().isoformat(),
                "agents": {}
            }
            
            for agent_id, agent in self.agents_data.items():
                display_schema["agents"][agent_id] = {
                    "position": agent['position'],
                    "filename": agent['filename'],
                    "inputs": agent['inputs_from_filename'],
                    "outputs": agent['outputs_from_filename'],
                    "role": agent['role'],
                    "cache_pattern": agent['cache_pattern']
                }
        
        return json.dumps(display_schema, indent=2)
    
    def _generate_flow_patterns_html(self) -> str:
        """Generate flow patterns explanation"""
        schema_info = ""
        if self.flow_schema:
            schema_info = f"<strong>Schema Version:</strong> {self.flow_schema.get('schema_version', 'Unknown')}<br>"
            
        return f"""
                    <div class="flow-patterns">
                        <h3>🔄 WARPCORE Agent Flow Patterns</h3>
                        <div class="pattern-grid">
                            <div class="pattern-item">
                                <strong>Schema-Driven Flow:</strong><br>
                                {schema_info}
                                Flow relationships defined in comprehensive schema with input/output types
                            </div>
                            <div class="pattern-item">
                                <strong>Convergent Architecture:</strong><br>
                                PATHFINDER (codebase analysis) and ORACLE (user specs) both output to ARCHITECT in common schema format
                            </div>
                            <div class="pattern-item">
                                <strong>Decision Loops:</strong><br>
                                CRAFTBUDDY: loop back to CRAFTSMAN or promote to GATEKEEPER<br>
                                GATEKEEPER: send fixes to CRAFTSMAN or new cycle to BOSS
                            </div>
                            <div class="pattern-item">
                                <strong>Schema Transformations:</strong><br>
                                Each agent performs specific data transformations with defined input/output schemas
                            </div>
                        </div>
                    </div>
        """
    
    def _get_unique_positions(self) -> set:
        """Get unique agent positions"""
        return set(agent['position'] for agent in self.agents_data.values())
    
    def _count_loops(self) -> int:
        """Count loop patterns in the flow"""
        # Look for craftbuddy -> enforcer pattern
        loops = 0
        for agent in self.agents_data.values():
            if 'craftbuddy' in agent['id'].lower() or 'buddy' in agent['id'].lower():
                if any('enforcer' in output for output in agent['outputs_from_filename']):
                    loops += 1
        return loops
    
    def _count_parallel(self) -> int:
        """Count parallel flow patterns"""
        # Look for multiple agents outputting to the same target
        targets = {}
        for agent in self.agents_data.values():
            for output in agent['outputs_from_filename']:
                if output not in targets:
                    targets[output] = []
                targets[output].append(agent['id'])
        
        return sum(1 for sources in targets.values() if len(sources) > 1)
    
    def _get_css_styles(self) -> str:
        """Get CSS styles for the HTML documentation"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        html, body {
            height: 100vh;
            overflow-x: hidden;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 100%);
            color: #e6e6e6;
        }

        .container {
            padding: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }

        .header {
            text-align: center;
            padding: 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            backdrop-filter: blur(10px);
            margin-bottom: 20px;
        }

        .header h1 {
            color: #00ff88;
            font-size: 2rem;
            margin-bottom: 10px;
            text-shadow: 0 0 20px rgba(0, 255, 136, 0.5);
        }

        .watermark {
            background: rgba(255, 0, 0, 0.1);
            color: #ff6b6b;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 0.8rem;
            border: 1px solid #ff6b6b;
            display: inline-block;
            margin-top: 10px;
        }

        .tab-container {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            overflow: hidden;
        }

        .tab-nav {
            display: flex;
            background: rgba(255, 255, 255, 0.1);
        }

        .tab-button {
            flex: 1;
            padding: 15px;
            background: transparent;
            border: none;
            color: #b0b0b0;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.3s ease;
        }

        .tab-button:hover {
            background: rgba(0, 255, 136, 0.1);
            color: #00ff88;
        }

        .tab-button.active {
            background: rgba(0, 255, 136, 0.2);
            color: #00ff88;
            border-bottom: 2px solid #00ff88;
        }

        .tab-content {
            display: none;
            padding: 20px;
        }

        .tab-content.active {
            display: block;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }

        .stat-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        }

        .stat-value {
            font-size: 1.5rem;
            font-weight: bold;
            color: #00ff88;
            display: block;
            margin-bottom: 5px;
        }

        .stat-label {
            color: #b0b0b0;
            font-size: 0.8rem;
        }

        .mermaid-container {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
        }

        .agent-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
        }

        .agent-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 15px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
        }

        .agent-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(0, 255, 136, 0.3);
            border-color: #00ff88;
        }

        .agent-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
        }

        .agent-position {
            width: 35px;
            height: 35px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: #000;
        }

        .agent-info h3 {
            color: #00ff88;
            font-size: 1.1rem;
            margin-bottom: 2px;
        }

        .role {
            color: #b0b0b0;
            font-size: 0.8rem;
        }

        .agent-details {
            font-size: 0.8rem;
            line-height: 1.4;
        }

        .agent-details div {
            margin-bottom: 5px;
        }

        .file-list {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            padding: 15px;
            font-family: 'Courier New', monospace;
            font-size: 0.8rem;
        }

        .file-item {
            padding: 8px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            color: #e6e6e6;
        }

        .file-item:last-child {
            border-bottom: none;
        }

        .schema-preview {
            background: rgba(0, 0, 0, 0.4);
            border-radius: 8px;
            padding: 15px;
            font-family: 'Courier New', monospace;
            font-size: 0.7rem;
            color: #e6e6e6;
            line-height: 1.4;
            overflow-x: auto;
        }

        .flow-patterns {
            background: rgba(255, 204, 0, 0.1);
            border-radius: 8px;
            padding: 15px;
            margin-top: 20px;
        }

        .flow-patterns h3 {
            color: #ffcc00;
            margin-bottom: 10px;
        }

        .pattern-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            font-size: 0.85rem;
        }

        .pattern-item {
            padding: 10px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 5px;
        }

        @media (max-width: 768px) {
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
            .agent-grid {
                grid-template-columns: 1fr;
            }
            .pattern-grid {
                grid-template-columns: 1fr;
            }
        }
        """
    
    def _get_javascript(self) -> str:
        """Get JavaScript for the HTML documentation"""
        return """
        // Initialize Mermaid
        mermaid.initialize({
            startOnLoad: true,
            theme: 'dark',
            flowchart: {
                useMaxWidth: true,
                htmlLabels: true
            }
        });

        // Tab switching function
        function showTab(tabName) {
            // Hide all tabs
            const tabs = document.querySelectorAll('.tab-content');
            tabs.forEach(tab => tab.classList.remove('active'));
            
            // Remove active from all buttons
            const buttons = document.querySelectorAll('.tab-button');
            buttons.forEach(button => button.classList.remove('active'));
            
            // Show selected tab
            document.getElementById(tabName + '-tab').classList.add('active');
            
            // Activate clicked button
            event.target.classList.add('active');
        }

        // Add hover effects
        document.querySelectorAll('.agent-card').forEach(card => {
            card.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-3px) scale(1.02)';
            });
            
            card.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0) scale(1)';
            });
        });
        """
    
    def build_documentation(self, output_file: str = None) -> str:
        """Build complete documentation and save to file"""
        if not output_file:
            output_file = str(self.docs_dir / "warpcore_agent_flow_dynamic.html")
        
        # Ensure docs directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        html_content = self.generate_html_documentation()
        
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        print(f"✅ Documentation built: {output_file}")
        return output_file


def main():
    """Command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="WARPCORE Agent Flow Generator")
    parser.add_argument('--agents-dir', '-a', help='Path to agents directory')
    parser.add_argument('--output', '-o', help='Output HTML file path')
    parser.add_argument('--mode', '-m', choices=['flow', 'html', 'both'], default='both',
                        help='Generation mode: flow (mermaid only), html (full docs), both')
    
    args = parser.parse_args()
    
    generator = AgentFlowGenerator(agents_dir=args.agents_dir)
    
    if args.mode in ['flow', 'both']:
        mermaid = generator.generate_mermaid_flow()
        print("Generated Mermaid Flow:")
        print("=" * 50)
        print(mermaid)
        print("=" * 50)
    
    if args.mode in ['html', 'both']:
        output_file = generator.build_documentation(args.output)
        print(f"📄 HTML documentation: file://{os.path.abspath(output_file)}")


if __name__ == "__main__":
    main()