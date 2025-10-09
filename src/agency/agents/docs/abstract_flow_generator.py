#!/usr/bin/env python3
"""
Abstract Flow Generator - Uses centralized agents.config.json
Eliminates redundant agent definitions and Mermaid rules.
"""
import json
import os
import argparse
from pathlib import Path
from typing import Dict, List, Any

class AbstractFlowGenerator:
    def __init__(self, config_path: str = None):
        """Initialize with centralized config"""
        if not config_path:
            # Default to docs directory config
            self.config_path = Path(__file__).parent / "agents.config.json"
        else:
            self.config_path = Path(config_path)
        
        self.config = self.load_config()
        
    def load_config(self) -> Dict[str, Any]:
        """Load the centralized agent configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"Failed to load config from {self.config_path}: {e}")
    
    def get_agents_for_franchise(self, franchise: str, include_dev: bool = False) -> Dict[str, Any]:
        """Get all agents (core + franchise-specific + optionally dev) for a franchise"""
        agents = self.config['core_agents'].copy()
        
        if franchise in self.config['franchise_agents']:
            agents.update(self.config['franchise_agents'][franchise])
        
        if include_dev:
            agents.update(self.config['dev_agents'])
        
        return agents
    
    def generate_mermaid_nodes(self, franchise: str) -> List[str]:
        """Generate Mermaid node definitions"""
        nodes = []
        agents = self.get_agents_for_franchise(franchise)
        
        for agent_key, agent_data in agents.items():
            node_def = self.config['mermaid_templates']['node_template'].format(
                id=agent_data['id'],
                name=agent_data['name'],
                role=agent_data['role']
            )
            nodes.append(f"    {node_def}")
        
        # Add UI elements
        ui = self.config['ui_elements']
        user_def = f"    USER([\"{ ui['user_input'][franchise]['icon']} { ui['user_input'][franchise]['label']}<br/>{ ui['user_input'][franchise]['sublabel']}\"])"
        complete_def = f"    COMPLETE([\"{ ui['completion'][franchise]['icon']} { ui['completion'][franchise]['label']}<br/>{ ui['completion'][franchise]['sublabel']}\"])"
        
        nodes.extend([user_def, complete_def])
        return nodes
    
    def generate_mermaid_connections(self, franchise: str, include_dev: bool = False) -> List[str]:
        """Generate Mermaid connection definitions"""
        connections = []
        flow_pattern = self.config['flow_patterns'][franchise]
        agents = self.get_agents_for_franchise(franchise, include_dev)
        
        # Create mapping from agent keys to IDs
        agent_key_to_id = {}
        for agent_key, agent_data in agents.items():
            agent_key_to_id[agent_key] = agent_data['id']
        
        for connection in flow_pattern['connections']:
            if connection.get('type') == 'conditional':
                template = self.config['mermaid_templates']['conditional_template']
            else:
                template = self.config['mermaid_templates']['connection_template']
            
            # Convert agent keys to IDs, handle special cases
            from_id = agent_key_to_id.get(connection['from'], connection['from'])
            to_id = agent_key_to_id.get(connection['to'], connection['to'])
            
            format_dict = {
                'from': from_id,
                'to': to_id,
                'label': connection['label']
            }
            conn_def = template.format(**format_dict)
            connections.append(f"    {conn_def}")
        
        # Add USER input connections from config
        if 'from_user' in flow_pattern:
            for user_conn_config in flow_pattern['from_user']:
                to_agent_key = user_conn_config['to']
                to_id = agent_key_to_id.get(to_agent_key, to_agent_key)
                label = user_conn_config['label']
                user_conn = f"    USER -->|\"{label}\"| {to_id}"
                connections.append(user_conn)
        
        return connections
    
    def generate_mermaid_styling(self, franchise: str) -> List[str]:
        """Generate Mermaid styling definitions"""
        styling = []
        agents = self.get_agents_for_franchise(franchise)
        
        # Generate classDef statements
        for agent_key, agent_data in agents.items():
            style_def = self.config['mermaid_templates']['styling_template'].format(
                agent_key=agent_key,
                fill=agent_data['styling']['fill'],
                stroke=agent_data['styling']['stroke'],
                stroke_width=agent_data['styling']['stroke_width']
            )
            styling.append(f"    {style_def}")
        
        # Complete element styling
        styling.append("    classDef complete fill:#22c55e,stroke:#16a34a,stroke-width:2px")
        
        # Generate class assignments
        styling.append("\n    %% Apply Classes")
        for agent_key, agent_data in agents.items():
            class_assign = f"    class {agent_data['id']} {agent_key}"
            styling.append(class_assign)
        
        styling.append("    class COMPLETE complete")
        return styling
    
    def generate_mermaid_flow(self, franchise: str) -> str:
        """Generate complete Mermaid flowchart"""
        flow_pattern = self.config['flow_patterns'][franchise]
        
        mermaid_parts = [
            "flowchart TD",
            f"    %% WARPCORE {franchise.title()} Agent Flow Configuration - {flow_pattern['subtitle']}",
            ""
        ]
        
        # Add nodes
        mermaid_parts.extend(self.generate_mermaid_nodes(franchise))
        mermaid_parts.append("")
        
        # Add phase comments and connections
        current_phase = ""
        for connection in flow_pattern['connections']:
            # Add phase headers for organization
            phase_comment = f"    %% {connection.get('phase', 'Flow')} Connections"
            if phase_comment not in mermaid_parts:
                mermaid_parts.append(phase_comment)
        
        mermaid_parts.extend(self.generate_mermaid_connections(franchise))
        mermaid_parts.append("")
        
        # Add styling
        mermaid_parts.append("    %% Styling")
        mermaid_parts.extend(self.generate_mermaid_styling(franchise))
        
        return "\n".join(mermaid_parts)
    
    def generate_html_dashboard(self, franchise: str, output_path: str = None) -> str:
        """Generate HTML dashboard for franchise"""
        flow_pattern = self.config['flow_patterns'][franchise]
        mermaid_flow = self.generate_mermaid_flow(franchise)
        
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎭 WARPCORE {franchise.title()} Agent Flow</title>
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
        .legend {{
            margin-top: 30px;
            padding: 20px;
            background-color: #f1f5f9;
            border-radius: 8px;
        }}
        .legend h3 {{
            color: #334155;
            margin-top: 0;
        }}
        .legend-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 4px;
            border: 2px solid;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎭 {flow_pattern['title']}</h1>
        <p class="subtitle">{flow_pattern['subtitle']}</p>
        
        <div class="mermaid">
{mermaid_flow}
        </div>

        {self.generate_legend_html(franchise)}
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
</html>"""
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(html_template)
            print(f"✅ Generated HTML dashboard: {output_path}")
        
        return html_template
    
    def generate_legend_html(self, franchise: str) -> str:
        """Generate HTML legend for agents"""
        agents = self.get_agents_for_franchise(franchise)
        legend_items = []
        
        for agent_key, agent_data in agents.items():
            item_html = f'''                <div class="legend-item">
                    <div class="legend-color" style="background-color: {agent_data['styling']['fill']}; border-color: {agent_data['styling']['stroke']};"></div>
                    <span><strong>{agent_data['name']}</strong> - {agent_data['role']}</span>
                </div>'''
            legend_items.append(item_html)
        
        legend_html = f'''        <div class="legend">
            <h3>🎨 Agent Color Legend</h3>
            <div class="legend-grid">
{chr(10).join(legend_items)}
            </div>
        </div>'''
        
        return legend_html
    
    def generate_mermaid_file(self, franchise: str, output_path: str = None) -> str:
        """Generate standalone .mermaid file"""
        mermaid_content = self.generate_mermaid_flow(franchise)
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(mermaid_content)
            print(f"✅ Generated Mermaid file: {output_path}")
        
        return mermaid_content

def main():
    parser = argparse.ArgumentParser(description="Abstract Flow Generator using centralized config")
    parser.add_argument("franchise", choices=['staff', 'framer'], help="Franchise to generate")
    parser.add_argument("--config", help="Path to agents.config.json")
    parser.add_argument("--output-dir", help="Output directory", default=".")
    parser.add_argument("--mermaid-only", action="store_true", help="Generate only .mermaid file")
    parser.add_argument("--html-only", action="store_true", help="Generate only HTML file")
    
    args = parser.parse_args()
    
    generator = AbstractFlowGenerator(args.config)
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not args.html_only:
        # Generate .mermaid file
        mermaid_path = output_dir / f"{args.franchise}_agent_flow.mermaid"
        generator.generate_mermaid_file(args.franchise, mermaid_path)
    
    if not args.mermaid_only:
        # Generate HTML dashboard
        html_path = output_dir / f"{args.franchise}_agent_flow_dynamic.html"
        generator.generate_html_dashboard(args.franchise, html_path)
    
    print(f"🎯 Generated {args.franchise} franchise documentation")

if __name__ == "__main__":
    main()