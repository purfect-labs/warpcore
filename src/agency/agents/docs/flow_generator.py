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
        self.agents_dir = Path(agents_dir) if agents_dir else Path(__file__).parent.parent
        self.docs_dir = Path(__file__).parent.parent.parent.parent / "docs" / "agency"
        self.agents_data = {}
        self.flow_relationships = {}
        self.flow_schema = self.load_schema()
        self.mermaid_config = self.load_mermaid_config()
        
    def parse_agent_files(self) -> Dict[str, Any]:
        """Parse all agent JSON files and extract flow relationships"""
        print("🔍 Parsing agent files for flow relationships...")
        
        agents = {}
        relationships = []
        
        # Find all agent JSON files
        agent_files = list(self.agents_dir.glob("*.json"))
        agent_files = [f for f in agent_files if not f.name.startswith('.')]
        
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
    
    def load_schema(self) -> Optional[Dict]:
        """Load the comprehensive flow schema from JSON file"""
        # Try agents/docs directory first (static location)
        agents_docs_schema = Path(__file__).parent / "warpcore_agent_flow_schema.json"
        
        if agents_docs_schema.exists():
            try:
                with open(agents_docs_schema, 'r') as f:
                    schema = json.load(f)
                print(f"✅ Loaded comprehensive flow schema (agents/docs): {agents_docs_schema}")
                return schema
            except Exception as e:
                print(f"⚠️ Error loading schema file {agents_docs_schema}: {e}")
        
        # Fallback to agency directory
        schema_file = self.agents_dir.parent / "warpcore_agent_flow_schema.json"
        if schema_file.exists():
            try:
                with open(schema_file, 'r') as f:
                    schema = json.load(f)
                print(f"✅ Loaded comprehensive flow schema (agency): {schema_file}")
                return schema
            except Exception as e:
                print(f"⚠️ Error loading schema file {schema_file}: {e}")
        
        # Final fallback to main docs directory
        docs_schema_file = self.docs_dir / "warpcore_agent_flow_schema.json"
        if docs_schema_file.exists():
            try:
                with open(docs_schema_file, 'r') as f:
                    schema = json.load(f)
                print(f"✅ Loaded comprehensive flow schema (main docs): {docs_schema_file}")
                return schema
            except Exception as e:
                print(f"⚠️ Error loading schema file {docs_schema_file}: {e}")
        
        print(f"❌ Schema file not found in any location:")
        print(f"  - {agents_docs_schema}")
        print(f"  - {schema_file}")
        print(f"  - {docs_schema_file}")
        return None
    
    def load_mermaid_config(self) -> Optional[Dict]:
        """Load Mermaid flow configuration from JSON file"""
        config_file = Path(__file__).parent / "mermaid_flow_config.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                print(f"✅ Loaded Mermaid flow config: {config_file}")
                return config
            except Exception as e:
                print(f"⚠️ Error loading Mermaid config {config_file}: {e}")
        else:
            print(f"⚠️ Mermaid config not found: {config_file}")
        
        return None
    
    def save_schema_to_docs(self) -> bool:
        """Save current schema to agents/docs directory for static availability"""
        if not self.flow_schema:
            print("⚠️ No schema loaded, cannot save to docs")
            return False
        
        # Save to agents/docs directory (same directory as this script)
        docs_schema_file = Path(__file__).parent / "warpcore_agent_flow_schema.json"
        
        try:
            with open(docs_schema_file, 'w') as f:
                json.dump(self.flow_schema, f, indent=2)
            print(f"✅ Schema saved to docs: {docs_schema_file}")
            return True
        except Exception as e:
            print(f"❌ Error saving schema to docs: {e}")
            return False
    
    def save_mermaid_to_docs(self) -> bool:
        """Save standalone Mermaid diagram to agents/docs directory"""
        try:
            mermaid_flow = self.generate_mermaid_flow()
            
            # Save raw Mermaid code
            mermaid_file = Path(__file__).parent / "warpcore_agent_flow.mermaid"
            with open(mermaid_file, 'w') as f:
                f.write(mermaid_flow)
            print(f"✅ Mermaid diagram saved: {mermaid_file}")
            
            # Also save as HTML with Mermaid viewer
            html_content = self._generate_standalone_mermaid_html(mermaid_flow)
            html_file = Path(__file__).parent / "warpcore_agent_flow_standalone.html"
            with open(html_file, 'w') as f:
                f.write(html_content)
            print(f"✅ Standalone Mermaid HTML saved: {html_file}")
            
            return True
        except Exception as e:
            print(f"❌ Error saving Mermaid diagram: {e}")
            return False
    
    def _generate_standalone_mermaid_html(self, mermaid_code: str) -> str:
        """Generate a standalone HTML file with just the Mermaid diagram"""
        timestamp = datetime.now().isoformat()
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WARPCORE Agent Flow - Standalone Mermaid Diagram</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
            color: #f8fafc;
            min-height: 100vh;
            line-height: 1.6;
        }}
        .header {{
            text-align: center;
            margin-bottom: 20px;
        }}
        .header h1 {{
            color: #8b5cf6;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 15px;
            text-shadow: 0 0 20px rgba(139, 92, 246, 0.3);
            background: linear-gradient(135deg, #8b5cf6, #7c3aed);
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .watermark {{
            background: rgba(139, 92, 246, 0.1);
            color: #a78bfa;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 0.85rem;
            border: 1px solid rgba(139, 92, 246, 0.3);
            display: inline-block;
            font-weight: 500;
        }}
        .mermaid-container {{
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(30, 41, 59, 0.6) 100%);
            border-radius: 16px;
            padding: 30px;
            text-align: center;
            margin: 30px auto;
            max-width: 1200px;
            border: 1px solid rgba(139, 92, 246, 0.1);
            backdrop-filter: blur(20px);
            box-shadow: 0 8px 32px rgba(139, 92, 246, 0.1);
        }}
        .info {{
            text-align: center;
            margin-top: 20px;
            font-size: 0.9rem;
            color: #b0b0b0;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 WARPCORE Agent Flow</h1>
        <div class="watermark">Generated: {timestamp}</div>
    </div>
    
    <div class="mermaid-container">
        <div class="mermaid">
{mermaid_code}
        </div>
    </div>
    
    <div class="info">
        <p>This is a standalone Mermaid diagram showing the complete WARPCORE agent workflow.</p>
        <p>Generated from comprehensive agent schema with all flow relationships and decision logic.</p>
    </div>
    
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'dark',
            flowchart: {{
                useMaxWidth: true,
                htmlLabels: true
            }}
        }});
    </script>
</body>
</html>"""
    
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
        """Generate Mermaid flowchart using config-driven approach"""
        if not self.agents_data:
            self.parse_agent_files()
        
        print("🎨 Generating Mermaid flow diagram from schema definition...")
        
        # Get config or use defaults
        config = self.mermaid_config if self.mermaid_config else self._get_default_mermaid_config()
        
        # Start with diagram type from config
        diagram_type = config.get('flow_config', {}).get('diagram_type', 'flowchart TD')
        mermaid = f"{diagram_type}\n"
        
        # Add title comment if configured
        if config.get('output_options', {}).get('add_title_comment', True):
            title = config.get('flow_config', {}).get('title', 'WARPCORE Agent Flow')
            mermaid += f"    %% {title}\n"
        
        # Add watermark comment if configured
        if config.get('output_options', {}).get('add_watermark_comment', True):
            watermark = config.get('flow_config', {}).get('watermark', '')
            if watermark:
                mermaid += f"    %% {watermark}\n\n"
        
        # Generate nodes using config templates
        if self.flow_schema and 'agent_definitions' in self.flow_schema:
            mermaid += self._generate_nodes_from_schema(config)
            mermaid += self._generate_connections_from_schema(config)
        else:
            # Fallback mode
            print("⚠️ Using fallback agent parsing (schema not available)")
            mermaid += self._generate_fallback_nodes_and_connections(config)
        
        # Add styling if configured
        if config.get('output_options', {}).get('include_styling', True):
            mermaid += self._generate_styling(config)
        
        return mermaid
    
    def _get_default_mermaid_config(self) -> Dict:
        """Get default Mermaid configuration if config file not available"""
        return {
            'flow_config': {'diagram_type': 'flowchart TD', 'title': 'WARPCORE Agent Flow'},
            'node_templates': {
                'agent_node': '{position}["{position}<br/>{name}<br/>{role_short}"]',
                'user_node': 'USER(["👤 USER<br/>{description}"])'
            },
            'flow_patterns': {'role_truncation': {'max_length': 25, 'suffix': '...'}},
            'output_options': {'include_styling': True, 'add_title_comment': True, 'add_watermark_comment': False}
        }
    
    def _generate_nodes_from_schema(self, config: Dict) -> str:
        """Generate Mermaid nodes from schema using config templates"""
        mermaid = ""
        schema_agents = self.flow_schema['agent_definitions']
        node_template = config.get('node_templates', {}).get('agent_node', '{position}["{position}<br/>{name}<br/>{role_short}"]')
        user_template = config.get('node_templates', {}).get('user_node', 'USER(["👤 USER<br/>{description}"])')
        
        # Role truncation settings
        role_config = config.get('flow_patterns', {}).get('role_truncation', {})
        max_length = role_config.get('max_length', 25)
        suffix = role_config.get('suffix', '...')
        
        # Generate agent nodes
        for agent_key, agent_def in schema_agents.items():
            position = agent_def['position']
            name = agent_def['name']
            role = agent_def['role']
            role_short = role[:max_length] + suffix if len(role) > max_length else role
            
            node = node_template.format(
                position=position,
                name=name,
                role_short=role_short
            )
            mermaid += f"    {node}\n"
        
        # Add USER node
        user_node = user_template.format(description="Requirements Input")
        mermaid += f"    {user_node}\n"
        
        # Add development tools section
        mermaid += "\n    %% Development Tools\n"
        dev_tools = [
            ("MAMA_BEAR", "🤱 MAMA BEAR<br/>QA & Production Readiness", "hexagon"),
            ("HARMONY", "🎭 HARMONY<br/>Coherence Guardian", "diamond")
        ]
        
        for tool_id, tool_label, shape in dev_tools:
            if shape == "hexagon":
                mermaid += f"    {tool_id}{{{{{tool_label}}}}}\n"
            elif shape == "diamond":
                mermaid += f"    {tool_id}{{{tool_label}}}\n"
            else:
                mermaid += f"    {tool_id}[\"{tool_label}\"]\n"
        
        return mermaid
    
    def _generate_connections_from_schema(self, config: Dict) -> str:
        """Generate Mermaid connections from schema"""
        mermaid = ""
        
        if 'flow_relationships' not in self.flow_schema:
            return mermaid
        
        relationships = self.flow_schema['flow_relationships']
        schema_agents = self.flow_schema['agent_definitions']
        edge_style = config.get('edge_styles', {}).get('default', {})
        label_format = edge_style.get('label_format', '|"{label}"|')
        
        # Linear flow connections
        for flow in relationships.get('linear_flow', []):
            from_agent = schema_agents[flow['from']]['position']
            to_agent = schema_agents[flow['to']]['position']
            flow_type = flow.get('type', '')
            
            if flow_type:
                label = label_format.format(label=flow_type)
                mermaid += f"    {from_agent} -->{label} {to_agent}\n"
            else:
                mermaid += f"    {from_agent} --> {to_agent}\n"
        
        # Decision flow connections
        for decision in relationships.get('decision_flows', []):
            from_pos = schema_agents[decision['from']]['position']
            
            for target in decision['to']:
                to_pos = schema_agents[target]['position']
                condition = decision['conditions'][target]
                label = label_format.format(label=condition)
                mermaid += f"    {from_pos} -->{label} {to_pos}\n"
        
        # External input connections
        for ext_input in relationships.get('external_inputs', []):
            source = ext_input['source']
            target_pos = schema_agents[ext_input['to']]['position']
            input_type = ext_input['type']
            label = label_format.format(label=input_type)
            mermaid += f"    {source} -->{label} {target_pos}\n"
        
        return mermaid
    
    def _generate_fallback_nodes_and_connections(self, config: Dict) -> str:
        """Generate fallback nodes and connections when schema not available"""
        mermaid = ""
        # This would contain the original fallback logic - simplified for now
        mermaid += "    %% Fallback mode - basic agent flow\n"
        return mermaid
    
    def _generate_styling(self, config: Dict) -> str:
        """Generate Mermaid styling from config"""
        mermaid = "\n    %% Styling\n"
        
        # Get node styles from config
        node_styles = config.get('node_styles', {})
        
        # Generate class definitions
        for style_name, style_props in node_styles.items():
            if style_name != 'user':  # Skip user style for now
                fill = style_props.get('fill', '#333')
                stroke = style_props.get('stroke', '#333')
                stroke_width = style_props.get('stroke_width', '2px')
                mermaid += f"    classDef {style_name} fill:{fill},stroke:{stroke},stroke-width:{stroke_width}\n"
        
        # Apply classes to nodes based on schema
        if self.flow_schema and 'agent_definitions' in self.flow_schema:
            for agent_key, agent_def in self.flow_schema['agent_definitions'].items():
                pos = agent_def['position']
                name = agent_key.lower()
                
                # Map agent names to style classes
                for style_name in node_styles.keys():
                    if style_name in name or (style_name == 'craftbuddy' and 'buddy' in name):
                        mermaid += f"    class {pos} {style_name}\n"
                        break
        
        # Apply styles to development tools
        mermaid += f"    class MAMA_BEAR mama_bear\n"
        mermaid += f"    class HARMONY harmony\n"
        
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
            <p class="watermark">Generated: {timestamp}</p>
        </div>

        <div class="tab-container">
            <div class="tab-nav">
                <button class="tab-button active" onclick="showTab('flow')">📊 Flow</button>
                <button class="tab-button" onclick="showTab('agents')">🤖 Agents</button>
                <button class="tab-button" onclick="showTab('harmony')">🎵 Harmony</button>
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

            <!-- Harmony Tab -->
            <div id="harmony-tab" class="tab-content">
                <div class="tab-pane">
                    {self._generate_harmony_insights_html()}
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
        """Get unique position values"""
        return set(agent['position'] for agent in self.agents_data.values())
    
    def _load_harmony_insights(self) -> Optional[Dict]:
        """Load harmony ecosystem insights from JSON file"""
        insights_file = Path(__file__).parent / "harmony_ecosystem_insights.json"
        
        if insights_file.exists():
            try:
                with open(insights_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading harmony insights {insights_file}: {e}")
        else:
            print(f"⚠️ Harmony insights not found: {insights_file}")
        
        return None
    
    def _generate_harmony_insights_html(self) -> str:
        """Generate HTML for harmony insights tab with expandable sections"""
        insights = self._load_harmony_insights()
        
        if not insights or 'harmony_ecosystem_insights' not in insights:
            return "<div class='harmony-placeholder'>🎵 Harmony insights not available. Run HARMONY agent to generate ecosystem analysis.</div>"
        
        harmony_data = insights['harmony_ecosystem_insights']
        meta = harmony_data.get('meta_analysis', {})
        
        # Generate expandable sections
        sections = [
            {
                'id': 'relationships',
                'title': '🔗 Agent Relationships',
                'icon': '🔗',
                'tooltip': 'View critical agent relationships and flow patterns',
                'content': self._generate_relationship_dynamics_html(harmony_data)
            },
            {
                'id': 'architecture',
                'title': '🏢 Architecture',
                'icon': '🏢',
                'tooltip': 'System architecture analysis and design principles',
                'content': self._generate_architectural_philosophy_html(harmony_data)
            },
            {
                'id': 'innovations',
                'title': '💡 Traditional Innovations',
                'icon': '💡',
                'tooltip': 'System innovation insights and breakthrough patterns',
                'content': self._generate_innovation_insights_html(harmony_data)
            },
            {
                'id': 'cost_efficiency',
                'title': '💰 Cost Efficiency ($195K/year)',
                'icon': '💰',
                'tooltip': 'Cost reduction opportunities with concrete savings',
                'content': self._generate_innovation_analysis_html(harmony_data)
            },
            {
                'id': 'tickets',
                'title': '🎫 Implementation Tickets (5)',
                'icon': '🎫',
                'tooltip': 'Ready-to-implement tickets with file paths and ROI',
                'content': self._generate_actionable_tickets_html(harmony_data)
            },
            {
                'id': 'health',
                'title': '📊 System Health',
                'icon': '📊',
                'tooltip': 'System health indicators and performance metrics',
                'content': self._generate_system_health_html(harmony_data)
            },
            {
                'id': 'recommendations',
                'title': '🎯 Recommendations',
                'icon': '🎯',
                'tooltip': 'Harmony preservation and enhancement recommendations',
                'content': self._generate_recommendations_html(harmony_data)
            },
            {
                'id': 'philosophy',
                'title': '🤔 Philosophy',
                'icon': '🤔',
                'tooltip': 'Design philosophy and emergent system properties',
                'content': self._generate_philosophical_observations_html(harmony_data)
            }
        ]
        
        # Generate section buttons
        section_buttons = ""
        section_content = ""
        
        for section in sections:
            section_buttons += f"""
                <button class="harmony-section-btn" 
                        data-section="{section['id']}"
                        title="{section['tooltip']}">
                    <span class="section-icon">{section['icon']}</span>
                    <span class="section-title">{section['title']}</span>
                    <span class="expand-icon">▼</span>
                </button>
            """
            
            section_content += f"""
                <div class="harmony-section-content" id="{section['id']}-content" style="display: none;">
                    {section['content']}
                </div>
            """
        
        html = f"""
                    <div class="harmony-header">
                        <h2>🎵 HARMONY - Ecosystem Insights</h2>
                        <div class="harmony-meta">
                            <span class="coherence-level">{meta.get('coherence_level', 'UNKNOWN')}</span>
                            <span class="timestamp">{meta.get('timestamp', 'N/A')}</span>
                        </div>
                    </div>
                    
                    <div class="harmony-sections">
                        <div class="harmony-buttons">
                            {section_buttons}
                        </div>
                        <div class="harmony-content">
                            {section_content}
                        </div>
                    </div>
        """
        
        return html
    
    def _generate_relationship_dynamics_html(self, harmony_data: Dict) -> str:
        """Generate relationship dynamics HTML"""
        dynamics = harmony_data.get('agent_relationship_dynamics', {})
        relationships = dynamics.get('critical_relationships', [])
        
        relationships_html = ""
        for rel in relationships[:4]:  # Show top 4 relationships
            relationships_html += f"""
                <div class="relationship-item">
                    <div class="relationship-flow">{rel.get('relationship', 'N/A')}</div>
                    <div class="relationship-type">{rel.get('type', 'N/A').replace('_', ' ').title()}</div>
                    <div class="relationship-significance">{rel.get('significance', 'N/A')}</div>
                </div>
            """
        
        return f"""
            <div class="insight-card">
                <h3>🔗 Agent Relationship Dynamics</h3>
                <div class="flow-pattern">{dynamics.get('primary_flow_pattern', 'N/A')}</div>
                <div class="flow-description">{dynamics.get('flow_description', 'N/A')}</div>
                <div class="relationships-list">
                    {relationships_html}
                </div>
                <div class="elegance-score">Flow Elegance: {dynamics.get('flow_elegance_score', 'N/A')}/100</div>
            </div>
        """
    
    def _generate_architectural_philosophy_html(self, harmony_data: Dict) -> str:
        """Generate architectural philosophy HTML"""
        arch = harmony_data.get('architectural_philosophy', {})
        strengths = arch.get('design_strengths', [])
        
        strengths_html = "".join(f"<li>{strength}</li>" for strength in strengths[:5])
        
        return f"""
            <div class="insight-card">
                <h3>🏗️ Architectural Philosophy</h3>
                <div class="design-principle">{arch.get('core_design_principle', 'N/A')}</div>
                <div class="assessment-grid">
                    <div class="assessment-item">
                        <span class="label">Modularity:</span>
                        <span class="value">{arch.get('modularity_assessment', 'N/A')}</span>
                    </div>
                    <div class="assessment-item">
                        <span class="label">Scalability:</span>
                        <span class="value">{arch.get('scalability_potential', 'N/A')}</span>
                    </div>
                    <div class="assessment-item">
                        <span class="label">Maintenance:</span>
                        <span class="value">{arch.get('maintenance_complexity', 'N/A')}</span>
                    </div>
                </div>
                <div class="design-strengths">
                    <h4>Design Strengths:</h4>
                    <ul>{strengths_html}</ul>
                </div>
            </div>
        """
    
    def _generate_innovation_insights_html(self, harmony_data: Dict) -> str:
        """Generate innovation insights HTML"""
        innovations = harmony_data.get('innovation_insights', {})
        
        innovations_html = ""
        for key, innovation in innovations.items():
            if isinstance(innovation, dict):
                benefits = ", ".join(innovation.get('benefits', [])[:3])
                innovations_html += f"""
                    <div class="innovation-item">
                        <div class="innovation-name">{key.replace('_', ' ').title()}</div>
                        <div class="innovation-level level-{innovation.get('innovation_level', 'low').lower()}">
                            {innovation.get('innovation_level', 'N/A')}
                        </div>
                        <div class="innovation-desc">{innovation.get('description', 'N/A')}</div>
                        <div class="innovation-benefits">{benefits}</div>
                    </div>
                """
        
        return f"""
            <div class="insight-card">
                <h3>💡 Innovation Insights</h3>
                <div class="innovations-grid">
                    {innovations_html}
                </div>
            </div>
        """
    
    def _generate_system_health_html(self, harmony_data: Dict) -> str:
        """Generate system health HTML"""
        health = harmony_data.get('system_health_indicators', {})
        coherence = health.get('coherence_metrics', {})
        performance = health.get('performance_indicators', {})
        
        coherence_html = "".join(
            f"<div class='metric-item'><span class='metric-label'>{k.replace('_', ' ').title()}:</span><span class='metric-value'>{v}</span></div>"
            for k, v in coherence.items()
        )
        
        performance_html = "".join(
            f"<div class='metric-item'><span class='metric-label'>{k.replace('_', ' ').title()}:</span><span class='metric-value'>{v}</span></div>"
            for k, v in performance.items()
        )
        
        return f"""
            <div class="insight-card">
                <h3>📊 System Health Indicators</h3>
                <div class="health-section">
                    <h4>Coherence Metrics</h4>
                    <div class="metrics-grid">{coherence_html}</div>
                </div>
                <div class="health-section">
                    <h4>Performance Indicators</h4>
                    <div class="metrics-grid">{performance_html}</div>
                </div>
            </div>
        """
    
    def _generate_recommendations_html(self, harmony_data: Dict) -> str:
        """Generate harmony recommendations HTML"""
        recs = harmony_data.get('harmony_recommendations', {})
        preservation = recs.get('preservation_priorities', [])
        enhancements = recs.get('enhancement_opportunities', [])
        
        preservation_html = "".join(f"<li>{item}</li>" for item in preservation[:3])
        enhancements_html = "".join(f"<li>{item}</li>" for item in enhancements[:3])
        
        return f"""
            <div class="insight-card">
                <h3>🎯 Harmony Recommendations</h3>
                <div class="recommendations-grid">
                    <div class="rec-section">
                        <h4>🛡️ Preservation Priorities</h4>
                        <ul class="rec-list">{preservation_html}</ul>
                    </div>
                    <div class="rec-section">
                        <h4>🚀 Enhancement Opportunities</h4>
                        <ul class="rec-list">{enhancements_html}</ul>
                    </div>
                </div>
            </div>
        """
    
    def _generate_innovation_analysis_html(self, harmony_data: Dict) -> str:
        """Generate innovation analysis HTML"""
        innovation = harmony_data.get('innovation_analysis', {})
        
        cost_opportunities = innovation.get('cost_efficiency_opportunities', [])
        performance_recs = innovation.get('performance_enhancement_recommendations', [])
        
        cost_html = "".join(
            f"""
            <div class="opportunity-item">
                <div class="opportunity-title">{opp.get('title', 'Cost Optimization')}</div>
                <div class="opportunity-impact">Impact: {opp.get('impact', 'Medium')}</div>
                <div class="opportunity-evidence">Evidence: {opp.get('evidence', 'N/A')}</div>
                <div class="opportunity-files">Files: {', '.join(opp.get('file_paths', []))}</div>
            </div>
            """
            for opp in cost_opportunities[:3]
        )
        
        performance_html = "".join(
            f"""
            <div class="enhancement-item">
                <div class="enhancement-name">{rec.get('name', 'Performance Improvement')}</div>
                <div class="enhancement-target">Target: {rec.get('target', 'TBD')}</div>
                <div class="enhancement-roi">ROI: {rec.get('roi_estimate', 'TBD')}</div>
            </div>
            """
            for rec in performance_recs[:3]
        )
        
        return f"""
            <div class="insight-card innovation-card">
                <h3>💡 Innovation & Cost Efficiency Analysis</h3>
                <div class="innovation-content">
                    <div class="cost-efficiency-section">
                        <h4>💰 Cost Efficiency Opportunities</h4>
                        <div class="opportunities-grid">{cost_html}</div>
                    </div>
                    <div class="performance-section">
                        <h4>🚀 Performance Enhancements</h4>
                        <div class="enhancements-grid">{performance_html}</div>
                    </div>
                </div>
            </div>
        """
    
    def _generate_actionable_tickets_html(self, harmony_data: Dict) -> str:
        """Generate actionable tickets HTML"""
        tickets_data = harmony_data.get('actionable_tickets', {})
        tickets = tickets_data.get('generated_tickets', [])
        
        tickets_html = "".join(
            f"""
            <div class="ticket-item priority-{ticket.get('priority', 'medium').lower()}">
                <div class="ticket-header">
                    <span class="ticket-id">{ticket.get('id', 'TICKET-001')}</span>
                    <span class="ticket-priority">{ticket.get('priority', 'MEDIUM')}</span>
                </div>
                <div class="ticket-title">{ticket.get('title', 'Implementation Task')}</div>
                <div class="ticket-files">Files: {', '.join(ticket.get('file_paths', []))}</div>
                <div class="ticket-current">Current: {ticket.get('current_state', 'Unknown')}</div>
                <div class="ticket-desired">Desired: {ticket.get('desired_state', 'TBD')}</div>
                <div class="ticket-justification">{ticket.get('business_justification', 'No justification provided')}</div>
            </div>
            """
            for ticket in tickets[:5]
        )
        
        total_tickets = tickets_data.get('total_tickets_generated', len(tickets))
        priority_breakdown = tickets_data.get('priority_breakdown', {})
        
        return f"""
            <div class="insight-card tickets-card">
                <h3>🎫 Actionable Implementation Tickets</h3>
                <div class="tickets-summary">
                    <div class="summary-stat">Total: {total_tickets}</div>
                    <div class="summary-stat">High: {priority_breakdown.get('high', 0)}</div>
                    <div class="summary-stat">Medium: {priority_breakdown.get('medium', 0)}</div>
                    <div class="summary-stat">Low: {priority_breakdown.get('low', 0)}</div>
                </div>
                <div class="tickets-grid">{tickets_html}</div>
            </div>
        """
    
    def _generate_philosophical_observations_html(self, harmony_data: Dict) -> str:
        """Generate philosophical observations HTML"""
        philosophy = harmony_data.get('philosophical_observations', {})
        emergent = philosophy.get('emergent_properties', [])
        
        emergent_html = "".join(f"<li>{prop}</li>" for prop in emergent[:4])
        
        return f"""
            <div class="insight-card philosophy-card">
                <h3>🤔 Philosophical Observations</h3>
                <div class="philosophy-content">
                    <div class="design-philosophy">
                        <h4>Design Philosophy</h4>
                        <p>{philosophy.get('design_philosophy', 'N/A')}</p>
                    </div>
                    <div class="flow-aesthetics">
                        <h4>Flow Aesthetics</h4>
                        <p>{philosophy.get('flow_aesthetics', 'N/A')}</p>
                    </div>
                    <div class="emergent-properties">
                        <h4>Emergent Properties</h4>
                        <ul>{emergent_html}</ul>
                    </div>
                </div>
            </div>
        """
    
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
            color: #f8fafc;
            line-height: 1.6;
        }

        .container {
            padding: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }

        .header {
            text-align: center;
            padding: 30px;
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(124, 58, 237, 0.05) 100%);
            border-radius: 16px;
            backdrop-filter: blur(20px);
            border: 1px solid rgba(139, 92, 246, 0.2);
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(139, 92, 246, 0.1);
        }

        .header h1 {
            color: #8b5cf6;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 10px;
            text-shadow: 0 0 20px rgba(139, 92, 246, 0.3);
            background: linear-gradient(135deg, #8b5cf6, #7c3aed);
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .watermark {
            background: rgba(139, 92, 246, 0.1);
            color: #a78bfa;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 0.85rem;
            border: 1px solid rgba(139, 92, 246, 0.3);
            display: inline-block;
            margin-top: 12px;
            font-weight: 500;
        }

        .tab-container {
            background: rgba(255, 255, 255, 0.02);
            border-radius: 16px;
            overflow: hidden;
            border: 1px solid rgba(139, 92, 246, 0.1);
            backdrop-filter: blur(10px);
        }

        .tab-nav {
            display: flex;
            background: rgba(139, 92, 246, 0.05);
            border-bottom: 1px solid rgba(139, 92, 246, 0.1);
        }

        .tab-button {
            flex: 1;
            padding: 16px 20px;
            background: transparent;
            border: none;
            color: #94a3b8;
            cursor: pointer;
            font-size: 0.95rem;
            font-weight: 500;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
        }

        .tab-button:hover {
            background: rgba(139, 92, 246, 0.1);
            color: #a78bfa;
            transform: translateY(-1px);
        }

        .tab-button.active {
            background: rgba(139, 92, 246, 0.15);
            color: #8b5cf6;
            border-bottom: 3px solid #8b5cf6;
            font-weight: 600;
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
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(124, 58, 237, 0.05) 100%);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            border: 1px solid rgba(139, 92, 246, 0.2);
            backdrop-filter: blur(10px);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(139, 92, 246, 0.15);
            border-color: rgba(139, 92, 246, 0.3);
        }

        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            color: #8b5cf6;
            display: block;
            margin-bottom: 8px;
            background: linear-gradient(135deg, #8b5cf6, #7c3aed);
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .stat-label {
            color: #cbd5e1;
            font-size: 0.85rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .mermaid-container {
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(30, 41, 59, 0.6) 100%);
            border-radius: 16px;
            padding: 30px;
            margin: 30px 0;
            text-align: center;
            border: 1px solid rgba(139, 92, 246, 0.1);
            backdrop-filter: blur(20px);
            box-shadow: 0 8px 32px rgba(139, 92, 246, 0.1);
        }

        .agent-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
        }

        .agent-card {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.02) 0%, rgba(139, 92, 246, 0.05) 100%);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(139, 92, 246, 0.15);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            backdrop-filter: blur(10px);
        }

        .agent-card:hover {
            transform: translateY(-4px) scale(1.02);
            box-shadow: 0 12px 40px rgba(139, 92, 246, 0.2);
            border-color: rgba(139, 92, 246, 0.4);
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.08) 0%, rgba(124, 58, 237, 0.06) 100%);
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
            color: #8b5cf6;
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 4px;
            background: linear-gradient(135deg, #8b5cf6, #7c3aed);
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .role {
            color: #cbd5e1;
            font-size: 0.85rem;
            font-weight: 400;
            line-height: 1.4;
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

        /* Harmony Tab Styles */
        .harmony-header {
            text-align: center;
            padding: 30px;
            background: linear-gradient(135deg, rgba(251, 191, 36, 0.1) 0%, rgba(245, 158, 11, 0.05) 100%);
            border-radius: 16px;
            margin-bottom: 30px;
            border: 1px solid rgba(251, 191, 36, 0.2);
        }
        
        .harmony-header h2 {
            color: #fbbf24;
            font-size: 2rem;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #fbbf24, #f59e0b);
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .harmony-meta {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 15px;
        }
        
        .coherence-level {
            background: rgba(34, 197, 94, 0.2);
            color: #22c55e;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
            border: 1px solid rgba(34, 197, 94, 0.3);
        }
        
        .insights-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
        }
        
        .insight-card {
            background: linear-gradient(135deg, rgba(251, 191, 36, 0.03) 0%, rgba(245, 158, 11, 0.01) 100%);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid rgba(251, 191, 36, 0.15);
            transition: all 0.3s ease;
        }
        
        .insight-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 40px rgba(251, 191, 36, 0.1);
            border-color: rgba(251, 191, 36, 0.3);
        }
        
        .insight-card h3 {
            color: #fbbf24;
            font-size: 1.4rem;
            margin-bottom: 16px;
            font-weight: 600;
        }
        
        .flow-pattern {
            font-size: 1.1rem;
            font-weight: 600;
            color: #f59e0b;
            margin-bottom: 12px;
        }
        
        .flow-description {
            color: #e5e7eb;
            font-size: 0.9rem;
            line-height: 1.5;
            margin-bottom: 16px;
        }
        
        .relationship-item {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 8px;
            border-left: 3px solid #fbbf24;
        }
        
        .relationship-flow {
            font-weight: 600;
            color: #fbbf24;
            margin-bottom: 4px;
        }
        
        .relationship-type {
            font-size: 0.8rem;
            color: #f59e0b;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .relationship-significance {
            font-size: 0.85rem;
            color: #d1d5db;
            margin-top: 6px;
        }
        
        .elegance-score {
            background: rgba(34, 197, 94, 0.1);
            color: #22c55e;
            padding: 8px 12px;
            border-radius: 8px;
            font-weight: 600;
            text-align: center;
            margin-top: 12px;
        }
        
        .design-principle {
            background: rgba(139, 92, 246, 0.1);
            padding: 12px;
            border-radius: 8px;
            color: #a78bfa;
            font-weight: 500;
            margin-bottom: 16px;
        }
        
        .assessment-grid {
            display: grid;
            gap: 8px;
            margin-bottom: 16px;
        }
        
        .assessment-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid rgba(75, 85, 99, 0.3);
        }
        
        .assessment-item .label {
            font-weight: 500;
            color: #9ca3af;
        }
        
        .assessment-item .value {
            color: #f3f4f6;
            font-weight: 400;
        }
        
        .innovations-grid {
            display: grid;
            gap: 12px;
        }
        
        .innovation-item {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 12px;
            padding: 16px;
            border: 1px solid rgba(99, 102, 241, 0.2);
        }
        
        .innovation-name {
            font-weight: 600;
            color: #6366f1;
            margin-bottom: 6px;
        }
        
        .innovation-level {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .level-high {
            background: rgba(239, 68, 68, 0.2);
            color: #ef4444;
        }
        
        .level-medium {
            background: rgba(251, 191, 36, 0.2);
            color: #fbbf24;
        }
        
        .level-low {
            background: rgba(34, 197, 94, 0.2);
            color: #22c55e;
        }
        
        .innovation-desc {
            color: #d1d5db;
            font-size: 0.9rem;
            margin-bottom: 8px;
            line-height: 1.4;
        }
        
        .innovation-benefits {
            color: #9ca3af;
            font-size: 0.8rem;
            font-style: italic;
        }
        
        .metrics-grid {
            display: grid;
            gap: 8px;
        }
        
        .metric-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid rgba(75, 85, 99, 0.2);
        }
        
        .metric-label {
            color: #9ca3af;
            font-size: 0.9rem;
        }
        
        .metric-value {
            color: #22c55e;
            font-weight: 500;
            font-size: 0.9rem;
        }
        
        .recommendations-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        
        .rec-section h4 {
            color: #fbbf24;
            margin-bottom: 12px;
            font-size: 1.1rem;
        }
        
        .rec-list {
            list-style: none;
            padding: 0;
        }
        
        .rec-list li {
            background: rgba(0, 0, 0, 0.2);
            padding: 10px 12px;
            border-radius: 6px;
            margin-bottom: 8px;
            border-left: 3px solid #fbbf24;
            font-size: 0.9rem;
            color: #e5e7eb;
        }
        
        .philosophy-card {
            grid-column: span 2;
            background: linear-gradient(135deg, rgba(168, 85, 247, 0.05) 0%, rgba(147, 51, 234, 0.02) 100%);
            border: 1px solid rgba(168, 85, 247, 0.15);
        }
        
        .philosophy-content {
            display: grid;
            gap: 20px;
        }
        
        .design-philosophy h4,
        .flow-aesthetics h4,
        .emergent-properties h4 {
            color: #a855f7;
            margin-bottom: 8px;
        }
        
        .design-philosophy p,
        .flow-aesthetics p {
            color: #d1d5db;
            line-height: 1.6;
            font-style: italic;
        }
        
        .emergent-properties ul {
            list-style: none;
            padding: 0;
        }
        
        .emergent-properties li {
            background: rgba(168, 85, 247, 0.1);
            padding: 8px 12px;
            border-radius: 6px;
            margin-bottom: 6px;
            color: #e5e7eb;
            border-left: 2px solid #a855f7;
        }
        
        .harmony-placeholder {
            text-align: center;
            padding: 60px 20px;
            color: #6b7280;
            font-size: 1.2rem;
            background: rgba(251, 191, 36, 0.05);
            border-radius: 16px;
            border: 2px dashed rgba(251, 191, 36, 0.2);
        }
        
        /* Innovation Analysis Styles */
        .innovation-card {
            background: linear-gradient(135deg, rgba(34, 197, 94, 0.05) 0%, rgba(16, 185, 129, 0.02) 100%);
            border: 1px solid rgba(34, 197, 94, 0.15);
        }
        
        .innovation-content {
            display: grid;
            gap: 20px;
        }
        
        .cost-efficiency-section h4,
        .performance-section h4 {
            color: #22c55e;
            margin-bottom: 12px;
            font-size: 1.1rem;
        }
        
        .opportunities-grid,
        .enhancements-grid {
            display: grid;
            gap: 12px;
        }
        
        .opportunity-item,
        .enhancement-item {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            padding: 12px;
            border: 1px solid rgba(34, 197, 94, 0.2);
        }
        
        .opportunity-title,
        .enhancement-name {
            font-weight: 600;
            color: #22c55e;
            margin-bottom: 6px;
        }
        
        .opportunity-impact,
        .opportunity-evidence,
        .opportunity-files,
        .enhancement-target,
        .enhancement-roi {
            font-size: 0.9rem;
            color: #d1d5db;
            margin-bottom: 4px;
        }
        
        .opportunity-files,
        .enhancement-roi {
            font-style: italic;
            color: #9ca3af;
        }
        
        /* Actionable Tickets Styles */
        .tickets-card {
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(79, 70, 229, 0.02) 100%);
            border: 1px solid rgba(99, 102, 241, 0.15);
        }
        
        .tickets-summary {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
            padding: 12px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 8px;
        }
        
        .summary-stat {
            color: #6366f1;
            font-weight: 600;
            font-size: 0.9rem;
        }
        
        .tickets-grid {
            display: grid;
            gap: 12px;
        }
        
        .ticket-item {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            padding: 16px;
            border-left: 4px solid #6366f1;
        }
        
        .ticket-item.priority-high {
            border-left-color: #ef4444;
            background: rgba(239, 68, 68, 0.05);
        }
        
        .ticket-item.priority-medium {
            border-left-color: #f59e0b;
            background: rgba(245, 158, 11, 0.05);
        }
        
        .ticket-item.priority-low {
            border-left-color: #22c55e;
            background: rgba(34, 197, 94, 0.05);
        }
        
        .ticket-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
        }
        
        .ticket-id {
            font-weight: 600;
            color: #6366f1;
            font-family: 'Monaco', 'Courier New', monospace;
        }
        
        .ticket-priority {
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        
        .priority-high .ticket-priority {
            background: rgba(239, 68, 68, 0.2);
            color: #ef4444;
        }
        
        .priority-medium .ticket-priority {
            background: rgba(245, 158, 11, 0.2);
            color: #f59e0b;
        }
        
        .priority-low .ticket-priority {
            background: rgba(34, 197, 94, 0.2);
            color: #22c55e;
        }
        
        .ticket-title {
            font-weight: 600;
            color: #f3f4f6;
            margin-bottom: 8px;
            font-size: 1.1rem;
        }
        
        .ticket-files,
        .ticket-current,
        .ticket-desired {
            font-size: 0.9rem;
            color: #d1d5db;
            margin-bottom: 6px;
        }
        
        .ticket-files {
            font-family: 'Monaco', 'Courier New', monospace;
            color: #a78bfa;
        }
        
        .ticket-justification {
            font-size: 0.9rem;
            color: #9ca3af;
            font-style: italic;
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px solid rgba(99, 102, 241, 0.2);
        }
        
        /* Harmony Expandable Sections Styles */
        .harmony-sections {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        
        .harmony-buttons {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 12px;
            margin-bottom: 20px;
        }
        
        .harmony-section-btn {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 16px 20px;
            background: linear-gradient(135deg, rgba(251, 191, 36, 0.1) 0%, rgba(245, 158, 11, 0.05) 100%);
            border: 1px solid rgba(251, 191, 36, 0.2);
            border-radius: 12px;
            color: #f3f4f6;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .harmony-section-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(251, 191, 36, 0.15);
            border-color: rgba(251, 191, 36, 0.4);
            background: linear-gradient(135deg, rgba(251, 191, 36, 0.15) 0%, rgba(245, 158, 11, 0.08) 100%);
        }
        
        .harmony-section-btn.active {
            background: linear-gradient(135deg, rgba(251, 191, 36, 0.2) 0%, rgba(245, 158, 11, 0.1) 100%);
            border-color: rgba(251, 191, 36, 0.5);
            box-shadow: 0 4px 20px rgba(251, 191, 36, 0.2);
        }
        
        .harmony-section-btn.active .expand-icon {
            transform: rotate(180deg);
        }
        
        .section-icon {
            font-size: 1.2rem;
            margin-right: 12px;
        }
        
        .section-title {
            flex: 1;
            text-align: left;
        }
        
        .expand-icon {
            font-size: 0.8rem;
            color: #fbbf24;
            transition: transform 0.3s ease;
            margin-left: 12px;
        }
        
        .harmony-content {
            position: relative;
        }
        
        .harmony-section-content {
            animation: slideDown 0.3s ease-out;
            margin-bottom: 20px;
        }
        
        .harmony-section-content.hiding {
            animation: slideUp 0.3s ease-out;
        }
        
        @keyframes slideDown {
            from {
                opacity: 0;
                max-height: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                max-height: 2000px;
                transform: translateY(0);
            }
        }
        
        @keyframes slideUp {
            from {
                opacity: 1;
                max-height: 2000px;
                transform: translateY(0);
            }
            to {
                opacity: 0;
                max-height: 0;
                transform: translateY(-10px);
            }
        }
        
        /* Enhanced tooltip styles */
        .harmony-section-btn[title] {
            position: relative;
        }
        
        .harmony-section-btn[title]:hover::after {
            content: attr(title);
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 0, 0, 0.9);
            color: #fbbf24;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 0.85rem;
            font-weight: 400;
            white-space: nowrap;
            z-index: 1000;
            margin-bottom: 8px;
            border: 1px solid rgba(251, 191, 36, 0.3);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }
        
        .harmony-section-btn[title]:hover::before {
            content: '';
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            border: 6px solid transparent;
            border-top-color: rgba(0, 0, 0, 0.9);
            z-index: 1001;
            margin-bottom: 2px;
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
            .insights-grid {
                grid-template-columns: 1fr;
            }
            .recommendations-grid {
                grid-template-columns: 1fr;
            }
            .philosophy-card {
                grid-column: span 1;
            }
            .harmony-buttons {
                grid-template-columns: 1fr;
                gap: 8px;
            }
            .harmony-section-btn {
                padding: 12px 16px;
                font-size: 0.9rem;
            }
            .section-icon {
                font-size: 1rem;
                margin-right: 8px;
            }
            .harmony-section-btn[title]:hover::after {
                font-size: 0.8rem;
                padding: 6px 10px;
                white-space: normal;
                max-width: 250px;
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
            
            // Auto-expand Cost Efficiency section when Harmony tab is clicked
            if (tabName === 'harmony') {
                setTimeout(() => {
                    const costEfficiencyButton = document.querySelector('[data-section="cost_efficiency"]');
                    if (costEfficiencyButton && !costEfficiencyButton.classList.contains('active')) {
                        costEfficiencyButton.click();
                    }
                }, 100);
            }
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
        
        // Harmony section expansion functionality
        document.querySelectorAll('.harmony-section-btn').forEach(button => {
            button.addEventListener('click', function() {
                const sectionId = this.getAttribute('data-section');
                const contentElement = document.getElementById(sectionId + '-content');
                
                // Toggle active state on button
                this.classList.toggle('active');
                
                if (contentElement.style.display === 'none' || contentElement.style.display === '') {
                    // Show content
                    contentElement.style.display = 'block';
                    contentElement.classList.remove('hiding');
                } else {
                    // Hide content with animation
                    contentElement.classList.add('hiding');
                    setTimeout(() => {
                        contentElement.style.display = 'none';
                        contentElement.classList.remove('hiding');
                    }, 300);
                }
            });
            
            // Enhanced hover effects for harmony buttons
            button.addEventListener('mouseenter', function() {
                if (!this.classList.contains('active')) {
                    this.style.transform = 'translateY(-2px)';
                }
            });
            
            button.addEventListener('mouseleave', function() {
                if (!this.classList.contains('active')) {
                    this.style.transform = 'translateY(0)';
                }
            });
        });
        
        // Auto-expand first section (Cost Efficiency) on Harmony tab load
        document.addEventListener('DOMContentLoaded', function() {
            const harmonyTab = document.getElementById('harmony-tab');
            if (harmonyTab && harmonyTab.classList.contains('active')) {
                const firstHighValueButton = document.querySelector('[data-section="cost_efficiency"]');
                if (firstHighValueButton) {
                    firstHighValueButton.click();
                }
            }
        });
        
        """
    
    def build_documentation(self, output_file: str = None) -> str:
        """Build complete documentation and save to file"""
        if not output_file:
            output_file = str(self.docs_dir / "warpcore_agent_flow_dynamic.html")
        
        # Ensure docs directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Save schema to agents/docs directory for static availability
        self.save_schema_to_docs()
        
        # Save standalone Mermaid diagram to agents/docs directory
        self.save_mermaid_to_docs()
        
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