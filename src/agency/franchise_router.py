#!/usr/bin/env python3
"""
🎯 FRANCHISE ROUTING ENGINE 🎯
Dynamic agent routing based on franchise flow configurations
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from flow_parser import generate_flow_config

class FranchiseRouter:
    def __init__(self, franchise_path: str):
        self.franchise_path = Path(franchise_path)
        self.config = None
        self.current_agent = None
        self.execution_history = []
        
        # Try to load existing config or generate from Mermaid
        self._load_or_generate_config()
    
    def _load_or_generate_config(self):
        """Parse config directly from Mermaid file"""
        mermaid_file = self.franchise_path / "docs" / "agent_flow.mermaid"
        
        if mermaid_file.exists():
            # Parse config directly from Mermaid (no cache file)
            from flow_parser import parse_mermaid_file
            self.config = parse_mermaid_file(str(mermaid_file))
            print(f"🎯 Parsed flow directly from Mermaid")
        else:
            raise FileNotFoundError(f"No Mermaid file found: {mermaid_file}")
    
    def get_available_agents(self) -> List[str]:
        """Get list of all available agents"""
        return list(self.config['agents'].keys())
    
    def get_agent_info(self, agent_id: str) -> Optional[Dict]:
        """Get detailed info for a specific agent"""
        return self.config['agents'].get(agent_id.lower())
    
    def get_entry_points(self) -> List[str]:
        """Get valid entry point agents"""
        return self.config.get('entry_points', [])
    
    def get_completion_points(self) -> List[str]:
        """Get workflow completion agents"""
        return self.config.get('completion_points', [])
    
    def get_next_agents(self, current_agent: str) -> List[Dict]:
        """Get possible next agents from current position"""
        agent_id = current_agent.lower()
        
        if agent_id not in self.config['routing']:
            return []
        
        next_agents = []
        for route in self.config['routing'][agent_id]:
            agent_info = self.get_agent_info(route['target'])
            next_agents.append({
                'agent_id': route['target'],
                'agent_name': agent_info['name'] if agent_info else route['target'].upper(),
                'condition': route['condition'],
                'type': route['type'],
                'is_loop': route['type'] == 'loop'
            })
        
        return next_agents
    
    def can_transition_to(self, from_agent: str, to_agent: str) -> bool:
        """Check if transition from one agent to another is valid"""
        from_id = from_agent.lower()
        to_id = to_agent.lower()
        
        if from_id not in self.config['routing']:
            return False
        
        valid_targets = [route['target'] for route in self.config['routing'][from_id]]
        return to_id in valid_targets
    
    def is_loop_pair(self, agent1: str, agent2: str) -> bool:
        """Check if two agents form a loop pair"""
        pair = sorted([agent1.lower(), agent2.lower()])
        return pair in self.config['loops']
    
    def get_workflow_path(self, start_agent: str, end_agent: str) -> List[str]:
        """Find a path from start to end agent using BFS"""
        start_id = start_agent.lower()
        end_id = end_agent.lower()
        
        if start_id == end_id:
            return [start_id]
        
        # BFS to find shortest path
        queue = [(start_id, [start_id])]
        visited = {start_id}
        
        while queue:
            current, path = queue.pop(0)
            
            if current not in self.config['routing']:
                continue
            
            for route in self.config['routing'][current]:
                target = route['target']
                
                if target == end_id:
                    return path + [target]
                
                if target not in visited:
                    visited.add(target)
                    queue.append((target, path + [target]))
        
        return []  # No path found
    
    def execute_agent(self, agent_id: str, workflow_id: str = None) -> Dict:
        """Execute an agent (placeholder for actual execution)"""
        agent_info = self.get_agent_info(agent_id)
        
        if not agent_info:
            return {
                'success': False,
                'error': f'Agent not found: {agent_id}'
            }
        
        # Record execution
        execution = {
            'agent_id': agent_id,
            'agent_name': agent_info['name'],
            'workflow_id': workflow_id,
            'timestamp': str(pd.Timestamp.now()),
            'next_agents': self.get_next_agents(agent_id)
        }
        
        self.execution_history.append(execution)
        self.current_agent = agent_id
        
        return {
            'success': True,
            'agent_id': agent_id,
            'agent_name': agent_info['name'],
            'position': agent_info['position'],
            'next_agents': execution['next_agents']
        }
    
    def get_workflow_summary(self) -> Dict:
        """Get a summary of the workflow configuration"""
        return {
            'franchise_name': self.config.get('franchise_name', 'Unknown'),
            'total_agents': len(self.config['agents']),
            'total_routes': sum(len(routes) for routes in self.config['routing'].values()),
            'loop_pairs': len(self.config['loops']),
            'entry_points': self.config['entry_points'],
            'completion_points': self.config['completion_points'],
            'agents': {
                agent_id: {
                    'name': info['name'],
                    'position': info['position'],
                    'has_outgoing': agent_id in self.config['routing'],
                    'route_count': len(self.config['routing'].get(agent_id, []))
                }
                for agent_id, info in self.config['agents'].items()
            }
        }
    
    def validate_workflow(self) -> List[str]:
        """Validate workflow configuration and return any issues"""
        issues = []
        
        # Check for unreachable agents
        reachable = set(self.config['entry_points'])
        for agent_routes in self.config['routing'].values():
            for route in agent_routes:
                reachable.add(route['target'])
        
        unreachable = set(self.config['agents'].keys()) - reachable
        if unreachable:
            issues.append(f"Unreachable agents: {', '.join(unreachable)}")
        
        # Check for dead ends (except completion points)
        completion_points = set(self.config['completion_points'])
        for agent_id in self.config['agents']:
            if (agent_id not in self.config['routing'] and 
                agent_id not in completion_points):
                issues.append(f"Dead end agent (not a completion point): {agent_id}")
        
        # Check for broken references
        all_agents = set(self.config['agents'].keys())
        for from_agent, routes in self.config['routing'].items():
            for route in routes:
                if route['target'] not in all_agents:
                    issues.append(f"Broken reference: {from_agent} -> {route['target']}")
        
        return issues

def load_franchise_router(franchise_name: str) -> FranchiseRouter:
    """Load router for a specific franchise"""
    base_path = Path(__file__).parent / "agents" / "franchise" / franchise_name
    
    if not base_path.exists():
        raise FileNotFoundError(f"Franchise not found: {franchise_name}")
    
    return FranchiseRouter(str(base_path))

if __name__ == "__main__":
    # Example usage
    try:
        # Load Framer franchise
        router = load_franchise_router("framer")
        
        print("🎯 FRANCHISE ROUTING ENGINE")
        print("=" * 40)
        
        summary = router.get_workflow_summary()
        print(f"📊 Franchise: {summary['franchise_name']}")
        print(f"🤖 Agents: {summary['total_agents']}")
        print(f"🔀 Routes: {summary['total_routes']}")
        print(f"🔄 Loops: {summary['loop_pairs']}")
        print(f"🚀 Entry: {', '.join(summary['entry_points'])}")
        print(f"🎯 End: {', '.join(summary['completion_points'])}")
        
        # Validate workflow
        issues = router.validate_workflow()
        if issues:
            print(f"\n⚠️ Issues found:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"\n✅ Workflow validation passed")
        
        # Show routing example
        print(f"\n🔀 Example routing from ORIGIN:")
        next_agents = router.get_next_agents("origin")
        for agent in next_agents:
            print(f"  -> {agent['agent_name']} ({agent['condition']})")
            
    except Exception as e:
        print(f"❌ Error: {e}")

# Add pandas import for timestamp
try:
    import pandas as pd
except ImportError:
    from datetime import datetime
    class pd:
        @staticmethod
        class Timestamp:
            @staticmethod
            def now():
                return datetime.now()