#!/usr/bin/env python3
"""
Universal Agent Scanner - Pure Directory-Driven System with Polymorphic Schema Integration
Completely franchise-agnostic. Drop it on any /agents/ directory and it works.
Zero configuration, zero hardcoded names, pure filesystem discovery.
Includes polymorphic schema system for consistent agent structure.
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import argparse
import sys
sys.path.append(str(Path(__file__).parent.parent / 'polymorphic'))
from universal_schema import UniversalAgentSchema, EnvironmentContext
from mermaid_ascii_parser import parse_mermaid_to_ascii

class UniversalAgentScanner:
    def __init__(self, agents_directory: str):
        self.agents_path = Path(agents_directory).resolve()
        self.franchise_name = self._detect_franchise_name()
        self.docs_path = self.agents_path.parent / "docs"
        
    def _detect_franchise_name(self) -> str:
        """Auto-detect franchise name from directory path"""
        # Look for franchise directory name in path like /path/franchise/framer/agents/
        path_parts = self.agents_path.parts
        if "franchise" in path_parts:
            franchise_index = path_parts.index("franchise")
            if franchise_index + 1 < len(path_parts):
                return path_parts[franchise_index + 1]
        
        # Look for parent directory name (e.g., /path/framer/agents/ -> "framer")
        if "agents" in path_parts:
            agents_index = path_parts.index("agents")
            if agents_index > 0:
                return path_parts[agents_index - 1]
        
        # Fallback to parent directory name
        return self.agents_path.parent.name
    
    def scan_agents(self) -> List[Dict[str, Any]]:
        """Scan agents directory and parse all agent files"""
        agents = []
        
        if not self.agents_path.exists():
            raise FileNotFoundError(f"Agents directory not found: {self.agents_path}")
        
        # Find all JSON files that match agent patterns
        json_files = list(self.agents_path.glob("*.json"))
        
        for json_file in json_files:
            try:
                agent_info = self._parse_agent_file(json_file)
                if agent_info:
                    agents.append(agent_info)
            except Exception as e:
                print(f"⚠️  Warning: Could not parse {json_file.name}: {e}")
        
        return sorted(agents, key=lambda x: x.get('sort_key', x['name']))
    
    def _parse_agent_file(self, json_file: Path) -> Optional[Dict[str, Any]]:
        """Parse individual agent JSON file"""
        filename = json_file.stem
        
        # Parse filename pattern: ID_NAME_from_X_to_Y.json
        # Examples: 
        # - 0a_origin_from_none_to_boss.json
        # - 4a_craftsman_from_enforcer_gatekeeper_to_craftbuddy.json
        # - harmony_from_user.json
        
        # Try standard pattern first
        pattern = r'^([^_]+)_([^_]+)_from_(.+?)(?:_to_(.+))?$'
        match = re.match(pattern, filename)
        
        if match:
            agent_id, agent_name, from_agents, to_agents = match.groups()
        else:
            # Handle special cases like "harmony_from_user"
            special_pattern = r'^([^_]+)_from_(.+)$'
            special_match = re.match(special_pattern, filename)
            if special_match:
                agent_name, from_agents = special_match.groups()
                agent_id = agent_name.upper()[:3]  # Generate ID from name
                to_agents = None
            else:
                print(f"⚠️  Filename doesn't match expected pattern: {filename}")
                return None
        
        # Parse from/to agents
        from_list = [f.strip() for f in from_agents.split('_')] if from_agents else []
        to_list = [t.strip() for t in to_agents.split('_')] if to_agents else []
        
        # Load JSON content
        try:
            with open(json_file, 'r') as f:
                agent_data = json.load(f)
        except Exception as e:
            print(f"⚠️  Could not load JSON from {json_file}: {e}")
            agent_data = {}
        
        # Extract styling info if available
        styling = self._extract_styling(agent_data)
        
        return {
            'id': agent_id,
            'name': agent_name.upper(),
            'filename': filename,
            'from_agents': from_list,
            'to_agents': to_list,
            'json_data': agent_data,
            'styling': styling,
            'sort_key': self._generate_sort_key(agent_id, agent_name)
        }
    
    def _extract_styling(self, agent_data: Dict) -> Dict[str, str]:
        """Extract or generate styling for agent - completely dynamic"""
        # Try to get from JSON data first
        if 'styling' in agent_data:
            return agent_data['styling']
        
        # Generate dynamic color based on agent name hash - no hardcoding
        agent_key = agent_data.get('name', '').lower()
        hash_val = hash(agent_key) % 360
        
        # Use HSL for consistent, pleasant colors
        return {
            'fill': f'hsl({hash_val}, 70%, 50%)',
            'stroke': f'hsl({hash_val}, 70%, 40%)',
            'stroke_width': '2px'
        }
    
    def _generate_sort_key(self, agent_id: str, agent_name: str) -> str:
        """Generate sorting key for agents"""
        # Handle numeric IDs (0a, 1b, etc.)
        if agent_id[0].isdigit():
            return f"{agent_id[0].zfill(2)}{agent_id[1:]}"
        return f"99_{agent_name}"
    
    def build_flow_graph(self, agents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build flow graph from agent connections"""
        nodes = {}
        connections = []
        
        # Build nodes
        for agent in agents:
            nodes[agent['name'].lower()] = {
                'id': agent['id'],
                'name': agent['name'],
                'styling': agent['styling'],
                'description': agent['json_data'].get('description', f"{agent['name']} Agent")
            }
        
        # Build connections
        for agent in agents:
            agent_key = agent['name'].lower()
            
            # Add outgoing connections
            for to_agent in agent['to_agents']:
                if to_agent != 'none' and to_agent in nodes:
                    connections.append({
                        'from': agent['id'],
                        'to': nodes[to_agent]['id'],
                        'label': f"{agent_key}_to_{to_agent}"
                    })
            
            # Add external connections (from user, etc.)
            if 'user' in agent['from_agents']:
                connections.append({
                    'from': 'USER',
                    'to': agent['id'], 
                    'label': f"user_to_{agent_key}"
                })
        
        return {
            'franchise': self.franchise_name,
            'nodes': nodes,
            'connections': connections
        }
    
    def generate_mermaid(self, flow_graph: Dict[str, Any]) -> str:
        """Generate Mermaid flowchart from flow graph"""
        lines = []
        lines.append("flowchart TD")
        lines.append(f"    %% {flow_graph['franchise'].title()} Agent Flow - Auto-generated from directory structure")
        lines.append("")
        
        # Add nodes
        for node_key, node in flow_graph['nodes'].items():
            node_def = f'    {node["id"]}["{node["id"]}<br/>{node["name"]}"]'
            lines.append(node_def)
        
        # Add USER node
        lines.append(f'    USER(["USER"])')
        lines.append(f'    COMPLETE(["COMPLETE"])')
        lines.append("")
        
        # Add connections  
        for conn in flow_graph['connections']:
            conn_line = f'    {conn["from"]} -->|"{conn["label"]}"| {conn["to"]}'
            lines.append(conn_line)
        
        lines.append("")
        
        # Add styling
        lines.append("    %% Styling")
        for node_key, node in flow_graph['nodes'].items():
            class_name = node_key
            style = node['styling']
            style_line = f'    classDef {class_name} fill:{style["fill"]},stroke:{style["stroke"]},stroke-width:{style["stroke_width"]}'
            lines.append(style_line)
        
        lines.append("    classDef complete fill:#22c55e,stroke:#16a34a,stroke-width:2px")
        lines.append("")
        
        # Apply classes
        lines.append("    %% Apply Classes")
        for node_key, node in flow_graph['nodes'].items():
            lines.append(f'    class {node["id"]} {node_key}')
        lines.append("    class COMPLETE complete")
        
        return "\\n".join(lines)
    
    def get_mermaid_ascii(self, mermaid_content: str, flow_graph: Dict[str, Any]) -> str:
        """Generate ASCII art from Mermaid using abstract parser"""
        franchise_title = flow_graph['franchise'].title()
        title = f"{franchise_title} AGENT FLOW"
        return parse_mermaid_to_ascii(mermaid_content, title)

    def generate_html_dashboard(self, flow_graph: Dict[str, Any], mermaid_content: str) -> str:
        """Generate HTML dashboard"""
        franchise_title = flow_graph['franchise'].title()
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎭 {franchise_title} Agent Flow</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f8fafc;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
            padding: 30px;
        }}
        h1 {{
            color: #1e293b;
            text-align: center;
            margin-bottom: 10px;
        }}
        .subtitle {{
            color: #64748b;
            text-align: center;
            margin-bottom: 30px;
            font-size: 16px;
        }}
        .mermaid {{
            display: flex;
            justify-content: center;
            margin: 20px 0;
        }}
        .info {{
            margin-top: 20px;
            padding: 15px;
            background-color: #f1f5f9;
            border-radius: 8px;
            font-size: 14px;
            color: #475569;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎭 {franchise_title} Agent Flow</h1>
        <p class="subtitle">Auto-generated from directory structure</p>
        
        <div class="mermaid">
{mermaid_content}
        </div>
        
        <div class="info">
            <strong>🔄 Auto-generated from:</strong> {self.agents_path}<br>
            <strong>📊 Agents discovered:</strong> {len(flow_graph['nodes'])}<br>
            <strong>🔗 Connections mapped:</strong> {len(flow_graph['connections'])}<br>
            <strong>⚡ Franchise:</strong> {franchise_title}
        </div>
    </div>

    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            flowchart: {{
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'basis'
            }}
        }});
    </script>
</body>
</html>'''
        return html
    
    def apply_universal_schemas(self, agents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply universal schema system to all agents (franchise-agnostic)"""
        print(f"🌟 Applying universal schema system to {len(agents)} agents...")
        
        updated_agents = []
        for agent in agents:
            try:
                # Get agent data
                agent_data = agent['json_data'].copy()
                
                # Apply universal schema enhancements
                enhanced_data = UniversalAgentSchema.enhance_agent(agent_data)
                
                # Add environment context if not present
                if ('prompt' in enhanced_data and 
                    "## ENVIRONMENT CONTEXT" not in enhanced_data['prompt']):
                    env_context = EnvironmentContext.generate()
                    enhanced_data['prompt'] = env_context + "\n\n" + enhanced_data['prompt']
                
                # Write back to file
                agent_file_path = self.agents_path / f"{agent['filename']}.json"
                with open(agent_file_path, 'w') as f:
                    json.dump(enhanced_data, f, indent=2)
                
                # Update agent info
                agent['json_data'] = enhanced_data
                updated_agents.append(agent)
                print(f"  ✅ Enhanced {agent['name']}")
                
            except Exception as e:
                print(f"  ⚠️ Could not enhance {agent.get('name', 'unknown')}: {e}")
                updated_agents.append(agent)  # Keep original if enhancement fails
        
        print(f"🌟 Universal schema system applied to {len(updated_agents)} agents")
        return updated_agents
    
    def generate_all_docs(self, apply_schemas: bool = True):
        """Generate all documentation from directory structure with optional schema application"""
        print(f"🔍 Scanning agents in: {self.agents_path}")
        print(f"🏷️  Detected franchise: {self.franchise_name}")
        
        # Ensure docs directory exists
        self.docs_path.mkdir(exist_ok=True)
        
        # Scan agents
        agents = self.scan_agents()
        print(f"📊 Found {len(agents)} agents")
        
        # Apply universal schemas if requested
        if apply_schemas:
            agents = self.apply_universal_schemas(agents)
        
        # Build flow graph
        flow_graph = self.build_flow_graph(agents)
        
        # Generate Mermaid
        mermaid_content = self.generate_mermaid(flow_graph)
        
        # Write Mermaid file
        mermaid_file = self.docs_path / f"{self.franchise_name}_agent_flow.mermaid"
        with open(mermaid_file, 'w') as f:
            f.write(mermaid_content)
        print(f"✅ Generated: {mermaid_file}")
        
        # Generate HTML dashboard
        html_content = self.generate_html_dashboard(flow_graph, mermaid_content)
        
        # Write HTML file
        html_file = self.docs_path / f"{self.franchise_name}_agent_flow_dynamic.html"
        with open(html_file, 'w') as f:
            f.write(html_content)
        print(f"✅ Generated: {html_file}")
        
        return {
            'franchise': self.franchise_name,
            'agents_count': len(agents),
            'mermaid_file': mermaid_file,
            'html_file': html_file
        }

def main():
    parser = argparse.ArgumentParser(description="Universal Agent Scanner with Polymorphic Schema Integration")
    parser.add_argument("agents_dir", help="Path to agents directory")
    parser.add_argument("--no-schemas", action="store_true", help="Skip polymorphic schema application")
    parser.add_argument("--schemas-only", action="store_true", help="Only apply schemas, skip doc generation")
    parser.add_argument("--print-flow", action="store_true", help="Print Mermaid flow diagram to shell")
    parser.add_argument("--flow-only", action="store_true", help="Only print flow, skip everything else")
    parser.add_argument("--ascii-flow", action="store_true", help="Render beautiful ASCII art flow in shell")
    parser.add_argument("--ascii-only", action="store_true", help="Only show ASCII flow, skip everything else")
    
    args = parser.parse_args()
    
    try:
        scanner = UniversalAgentScanner(args.agents_dir)
        
        if args.flow_only:
            # Only print flow diagram
            agents = scanner.scan_agents()
            flow_graph = scanner.build_flow_graph(agents)
            mermaid_content = scanner.generate_mermaid(flow_graph)
            
            print(f"\n🎭 {flow_graph['franchise'].title()} Agent Flow:")
            print("=" * 60)
            print(mermaid_content)
            print("=" * 60)
            
        elif args.ascii_only:
            # Only show ASCII flow, skip everything else
            agents = scanner.scan_agents()
            flow_graph = scanner.build_flow_graph(agents)
            mermaid_content = scanner.generate_mermaid(flow_graph)
            ascii_art = scanner.get_mermaid_ascii(mermaid_content, flow_graph)
            
            print(ascii_art)
            
        elif args.schemas_only:
            # Only apply universal schemas
            agents = scanner.scan_agents()
            scanner.apply_universal_schemas(agents)
            print(f"\n🌟 Applied universal schemas to {len(agents)} agents")
            
        else:
            # Generate docs (with optional schema application)
            apply_schemas = not args.no_schemas
            result = scanner.generate_all_docs(apply_schemas=apply_schemas)
            
            # Print flow if requested
            if args.print_flow:
                agents = scanner.scan_agents()
                flow_graph = scanner.build_flow_graph(agents)
                mermaid_content = scanner.generate_mermaid(flow_graph)
                
                print(f"\n🎭 {flow_graph['franchise'].title()} Agent Flow:")
                print("=" * 60)
                print(mermaid_content)
                print("=" * 60)
            
            # Show ASCII flow if requested
            if args.ascii_flow:
                agents = scanner.scan_agents()
                flow_graph = scanner.build_flow_graph(agents)
                mermaid_content = scanner.generate_mermaid(flow_graph)
                ascii_art = scanner.get_mermaid_ascii(mermaid_content, flow_graph)
                
                print("\n")
                print(ascii_art)
            
            print(f"\n🎯 Success! Generated {result['franchise']} documentation:")
            print(f"   📄 {result['mermaid_file']}")
            print(f"   🌐 {result['html_file']}")
            print(f"   📊 {result['agents_count']} agents processed")
            if apply_schemas:
                print(f"   🌟 Universal schemas applied")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())