#!/usr/bin/env python3
"""
🔄 DYNAMIC FRANCHISE FLOW PARSER 🔄
Parse Mermaid flowchart files to build agent routing dynamically
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class FlowParser:
    def __init__(self, mermaid_file: str):
        self.mermaid_file = Path(mermaid_file)
        self.agents = {}
        self.flows = {}
        self.loops = {}
        
    def parse_mermaid(self) -> Dict:
        """Parse Mermaid flowchart and extract agent routing"""
        if not self.mermaid_file.exists():
            raise FileNotFoundError(f"Mermaid file not found: {self.mermaid_file}")
        
        content = self.mermaid_file.read_text()
        
        # Extract agent definitions
        self._extract_agents(content)
        
        # Extract flow connections
        self._extract_flows(content)
        
        # Build routing configuration
        return self._build_routing_config()
    
    def _extract_agents(self, content: str):
        """Extract agent definitions from Mermaid"""
        # Match: AGENT_NAME["position<br/>NAME"]
        agent_pattern = r'(\w+)\[\"([^\"]+)\"\]'
        
        for match in re.finditer(agent_pattern, content):
            agent_id = match.group(1).lower()
            label_content = match.group(2)
            
            # Extract position and name from label
            if '<br/>' in label_content:
                position, name = label_content.split('<br/>')
            else:
                position = label_content
                name = agent_id.upper()
            
            self.agents[agent_id] = {
                'name': name,
                'position': position,
                'id': agent_id
            }
    
    def _extract_flows(self, content: str):
        """Extract flow connections from Mermaid"""
        # Match: AGENT1 -->|"flow_name"| AGENT2
        # Match: AGENT1 <-->|"flow_name"| AGENT2 (bidirectional)
        flow_patterns = [
            r'(\w+)\s+-->\|\s*\"([^\"]+)\"\s*\|\s+(\w+)',  # One-way
            r'(\w+)\s+<-->\|\s*\"([^\"]+)\"\s*\|\s+(\w+)', # Two-way (loop)
            r'(\w+)\s+-->\s+(\w+)'  # Simple arrow without label
        ]
        
        for pattern in flow_patterns:
            for match in re.finditer(pattern, content):
                if len(match.groups()) == 3:
                    from_agent = match.group(1).lower()
                    flow_label = match.group(2)
                    to_agent = match.group(3).lower()
                    is_loop = '<-->' in match.group(0)
                elif len(match.groups()) == 2:
                    from_agent = match.group(1).lower()
                    to_agent = match.group(2).lower()
                    flow_label = f"{from_agent}_to_{to_agent}"
                    is_loop = False
                
                if from_agent not in self.flows:
                    self.flows[from_agent] = []
                
                self.flows[from_agent].append({
                    'to': to_agent,
                    'label': flow_label,
                    'is_loop': is_loop
                })
                
                # Handle bidirectional flows
                if is_loop:
                    if to_agent not in self.flows:
                        self.flows[to_agent] = []
                    self.flows[to_agent].append({
                        'to': from_agent,
                        'label': flow_label,
                        'is_loop': True
                    })
    
    def _build_routing_config(self) -> Dict:
        """Build routing configuration for agency system"""
        config = {
            'franchise_name': self.mermaid_file.parent.name,
            'agents': self.agents,
            'routing': {},
            'loops': [],
            'entry_points': [],
            'completion_points': []
        }
        
        # Build routing table
        for from_agent, connections in self.flows.items():
            config['routing'][from_agent] = []
            
            for conn in connections:
                config['routing'][from_agent].append({
                    'target': conn['to'],
                    'condition': conn['label'],
                    'type': 'loop' if conn['is_loop'] else 'flow'
                })
                
                # Track loops
                if conn['is_loop']:
                    loop_pair = sorted([from_agent, conn['to']])
                    if loop_pair not in config['loops']:
                        config['loops'].append(loop_pair)
        
        # Find entry points (agents with no incoming flows)
        all_targets = set()
        for connections in self.flows.values():
            for conn in connections:
                all_targets.add(conn['to'])
        
        config['entry_points'] = [
            agent for agent in self.agents.keys() 
            if agent not in all_targets and agent in self.flows
        ]
        
        # Find completion points (agents with no outgoing flows)
        config['completion_points'] = [
            agent for agent in self.agents.keys() 
            if agent not in self.flows
        ]
        
        return config
    
    def get_next_agents(self, current_agent: str, config: Dict) -> List[str]:
        """Get possible next agents from current position"""
        if current_agent not in config['routing']:
            return []
        
        return [conn['target'] for conn in config['routing'][current_agent]]
    
    def is_loop_partner(self, agent1: str, agent2: str, config: Dict) -> bool:
        """Check if two agents are loop partners"""
        pair = sorted([agent1.lower(), agent2.lower()])
        return pair in config['loops']
    
    def export_config(self, output_file: str, config: Dict):
        """Export configuration to JSON file"""
        with open(output_file, 'w') as f:
            json.dump(config, f, indent=2)

def generate_flow_config(mermaid_file: str, output_file: Optional[str] = None) -> Dict:
    """Generate flow configuration from Mermaid file"""
    parser = FlowParser(mermaid_file)
    config = parser.parse_mermaid()
    
    if output_file:
        parser.export_config(output_file, config)
        print(f"✅ Flow configuration exported to: {output_file}")
    
    return config

def parse_mermaid_file(mermaid_file: str) -> Dict:
    """Parse Mermaid file directly and return config (no file output)"""
    return generate_flow_config(mermaid_file)

if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python flow_parser.py <mermaid_file> [output_file]")
        sys.exit(1)
    
    mermaid_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        config = generate_flow_config(mermaid_file, output_file)
        
        print(f"🔄 Parsed {len(config['agents'])} agents")
        print(f"📊 Found {len(config['loops'])} loop pairs")
        print(f"🚀 Entry points: {', '.join(config['entry_points'])}")
        print(f"🎯 Completion points: {', '.join(config['completion_points'])}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)