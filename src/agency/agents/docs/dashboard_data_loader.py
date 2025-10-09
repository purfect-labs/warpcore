#!/usr/bin/env python3
"""
WARPCORE Agent Dashboard Data Loader
Loads actual agent JSON files and polymorphic schema mappings for the dashboard.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import datetime

class DashboardDataLoader:
    def __init__(self, base_path: str = None):
        """Initialize the data loader with the base path to the agency directory."""
        if base_path is None:
            # Default to the current directory structure
            self.base_path = Path(__file__).parent.parent
        else:
            self.base_path = Path(base_path)
        
        self.polymorphic_mappings = self._get_polymorphic_mappings()
    
    def _get_polymorphic_mappings(self) -> Dict[str, str]:
        """Get the polymorphic mappings for all agents."""
        return {
            # Staff franchise (legacy)
            "bootstrap_agent": "BootstrapAgentSchema",
            "workflow_orchestrator_agent": "OrchestratorAgentSchema", 
            "schema_coherence_reconciler_agent": "SchemaReconcilerAgentSchema",
            "requirements_generator_agent": "RequirementsGeneratorAgentSchema",
            "requirements_validator_agent": "RequirementsValidatorAgentSchema",
            "implementation_agent": "ImplementationAgentSchema",
            "gate_promote_agent": "GatePromoteAgentSchema",
            "user_input_requirements_translator": "UserInputTranslatorAgentSchema",
            
            # Framer franchise mappings
            "origin": "BootstrapAgentSchema",
            "boss": "OrchestratorAgentSchema",
            "pathfinder": "SchemaReconcilerAgentSchema",
            "oracle": "UserInputTranslatorAgentSchema",
            "architect": "RequirementsGeneratorAgentSchema",
            "enforcer": "RequirementsValidatorAgentSchema",
            "craftsman_implementation": "ImplementationAgentSchema",
            "craftbuddy": "RequirementsGeneratorAgentSchema",
            "gatekeeper": "GatePromoteAgentSchema",
            "ghostwriter": "RequirementsGeneratorAgentSchema",
            "alice": "RequirementsValidatorAgentSchema",
            "flux": "ImplementationAgentSchema",
            "mama_bear": "GatePromoteAgentSchema",
            "harmony": "SchemaReconcilerAgentSchema",
            
            # PATROL franchise mappings
            "deep": "RequirementsGeneratorAgentSchema",
            "cipher": "RequirementsValidatorAgentSchema",
            "glitch": "ImplementationAgentSchema",
            "zero": "GatePromoteAgentSchema"
        }
    
    def load_all_franchise_data(self) -> Dict[str, Any]:
        """Load agent data for all franchises."""
        franchise_data = {}
        
        # Look for franchise directories
        franchise_base = self.base_path / "franchise"
        
        if franchise_base.exists():
            for franchise_dir in franchise_base.iterdir():
                if franchise_dir.is_dir() and not franchise_dir.name.startswith('.'):
                    franchise_name = franchise_dir.name
                    agents_data = self._load_franchise_agents(franchise_name, franchise_dir)
                    if agents_data:
                        franchise_data[franchise_name] = agents_data
        
        # Also check for build output directory
        build_output_dir = self.base_path / "build_output"
        if build_output_dir.exists():
            for franchise_dir in build_output_dir.iterdir():
                if franchise_dir.is_dir() and not franchise_dir.name.startswith('.'):
                    franchise_name = franchise_dir.name
                    if franchise_name not in franchise_data:
                        agents_data = self._load_franchise_agents(franchise_name, franchise_dir, is_build_output=True)
                        if agents_data:
                            franchise_data[franchise_name] = agents_data
        
        return franchise_data
    
    def _load_franchise_agents(self, franchise_name: str, franchise_dir: Path, is_build_output: bool = False) -> List[Dict[str, Any]]:
        """Load all agents for a specific franchise."""
        agents = []
        
        # Look for agents directory or JSON files directly
        agents_dir = franchise_dir / "agents" if not is_build_output else franchise_dir
        
        if not agents_dir.exists():
            agents_dir = franchise_dir  # Try the franchise directory directly
        
        if agents_dir.exists():
            for agent_file in agents_dir.glob("*.json"):
                try:
                    agent_data = self._load_agent_file(agent_file, franchise_name)
                    if agent_data:
                        agents.append(agent_data)
                except Exception as e:
                    print(f"Warning: Could not load {agent_file}: {e}")
        
        return sorted(agents, key=lambda x: x.get('name', ''))
    
    def _load_agent_file(self, agent_file: Path, franchise_name: str) -> Optional[Dict[str, Any]]:
        """Load a single agent JSON file."""
        try:
            with open(agent_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Extract agent ID from filename or JSON
            agent_id = self._extract_agent_id(agent_file.name, json_data)
            agent_name = agent_id.replace('_', ' ').title()
            
            # Get polymorphic schema info
            polymorphic_schema = self._get_polymorphic_schema_info(agent_id)
            
            return {
                'name': agent_name,
                'id': agent_id,
                'file': agent_file.name,
                'json_data': json_data,
                'polymorphic_schema': polymorphic_schema,
                'franchise': franchise_name,
                'file_path': str(agent_file),
                'file_size': agent_file.stat().st_size,
                'last_modified': datetime.datetime.fromtimestamp(agent_file.stat().st_mtime).isoformat()
            }
            
        except Exception as e:
            print(f"Error loading {agent_file}: {e}")
            return None
    
    def _extract_agent_id(self, filename: str, json_data: Dict[str, Any]) -> str:
        """Extract agent ID from filename or JSON data."""
        # Try to get from JSON first
        if 'agent_id' in json_data:
            return json_data['agent_id']
        
        # Extract from filename patterns
        filename = filename.replace('.json', '')
        
        # Handle numbered prefixes like "1_commander_from_user_to_tactician"
        if '_' in filename and filename[0].isdigit():
            parts = filename.split('_')
            # Look for the agent name part
            for i, part in enumerate(parts):
                if part in ['from', 'to']:
                    return '_'.join(parts[1:i])
            # If no 'from' found, take everything after the first number
            return '_'.join(parts[1:])
        
        return filename
    
    def _get_polymorphic_schema_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get polymorphic schema information for an agent."""
        mapping = self.polymorphic_mappings.get(agent_id)
        if not mapping:
            return None
        
        return {
            'schema_class': mapping,
            'base_features': [
                "Data compression tracking",
                "Bonus contributions identification", 
                "Base execution metrics",
                "Universal validation rules",
                "Shared success criteria"
            ],
            'specific_features': self._get_schema_specific_features(mapping)
        }
    
    def _get_schema_specific_features(self, schema_class: str) -> List[str]:
        """Get specific features for a schema class."""
        features = {
            "BootstrapAgentSchema": [
                "System health validation",
                "Agent discovery results",
                "Bootstrap configuration",
                "Orchestrator preparation"
            ],
            "OrchestratorAgentSchema": [
                "Agent sequencing",
                "Workflow coordination",
                "Agent lifecycle management",
                "Orchestration success tracking"
            ],
            "SchemaReconcilerAgentSchema": [
                "File analysis summary",
                "Coherence issue detection",
                "PAP compliance scoring",
                "Detailed findings reporting"
            ],
            "RequirementsGeneratorAgentSchema": [
                "Requirements enumeration",
                "Priority classification",
                "Implementation phases",
                "Dependency mapping"
            ],
            "RequirementsValidatorAgentSchema": [
                "Requirements validation",
                "PAP compliance checking",
                "Feasibility assessment",
                "Implementation readiness"
            ],
            "ImplementationAgentSchema": [
                "Code implementation",
                "Test execution",
                "File modifications",
                "Git preparation"
            ],
            "GatePromoteAgentSchema": [
                "Cross-agent validation",
                "Git operations",
                "Gate decision making",
                "Workflow completion"
            ],
            "UserInputTranslatorAgentSchema": [
                "Input processing",
                "Requirements extraction",
                "Translation accuracy",
                "Structured output generation"
            ]
        }
        
        return features.get(schema_class, ["Generic polymorphic features"])
    
    def generate_dashboard_json(self) -> str:
        """Generate JSON data file for the dashboard."""
        data = self.load_all_franchise_data()
        
        # Add metadata
        output = {
            'metadata': {
                'generated_at': datetime.datetime.now().isoformat(),
                'total_franchises': len(data),
                'total_agents': sum(len(agents) for agents in data.values()),
                'polymorphic_mappings_count': len(self.polymorphic_mappings)
            },
            'franchises': data,
            'polymorphic_mappings': self.polymorphic_mappings
        }
        
        return json.dumps(output, indent=2, ensure_ascii=False)
    
    def save_dashboard_data(self, output_file: str = None) -> str:
        """Save dashboard data to a JSON file."""
        if output_file is None:
            output_file = str(Path(__file__).parent / "dashboard_data.json")
        
        data_json = self.generate_dashboard_json()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(data_json)
        
        print(f"Dashboard data saved to: {output_file}")
        return output_file


def main():
    """Main function to generate dashboard data."""
    loader = DashboardDataLoader()
    
    # Generate and save the dashboard data
    output_file = loader.save_dashboard_data()
    
    # Print summary
    data = loader.load_all_franchise_data()
    print(f"\nGenerated dashboard data:")
    print(f"- Total franchises: {len(data)}")
    for franchise, agents in data.items():
        print(f"  - {franchise}: {len(agents)} agents")
    print(f"- Polymorphic mappings: {len(loader.polymorphic_mappings)}")
    print(f"- Output file: {output_file}")


if __name__ == "__main__":
    main()