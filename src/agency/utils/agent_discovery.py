#!/usr/bin/env python3
"""
Agent Discovery and Management Utility
Provides dynamic agent discovery using mermaid schema and file naming conventions
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import glob

class AgentDiscovery:
    """Dynamic agent discovery using authoritative sources"""
    
    def __init__(self, base_path: Path, franchise: str = "staff"):
        self.base_path = base_path
        self.franchise = franchise
        self.agents_path = self._resolve_franchise_path()
        self.mermaid_schema_path = self._resolve_schema_path()
        
        # Load authoritative sources
        self._mermaid_schema = self._load_mermaid_schema()
        self._discovered_agents = self._discover_agent_files()
    
    def _resolve_franchise_path(self) -> Path:
        """Resolve franchise-specific agent path"""
        franchise_base = self.base_path / "agents" / "franchise" / self.franchise
        
        # Check if franchise directory exists
        if not franchise_base.exists():
            # Fallback to old flat structure for backward compatibility
            print(f"⚠️ Franchise directory {franchise_base} not found, falling back to flat structure")
            return self.base_path / "agents"
        
        # Staff: agents directly in franchise/staff/agents/
        # Framer: agents in franchise/framer/agents/
        agents_dir = franchise_base / "agents"
        if agents_dir.exists():
            return agents_dir
        else:
            # Fallback to franchise base if agents subdir doesn't exist
            return franchise_base
    
    def _resolve_schema_path(self) -> Path:
        """Resolve franchise-specific schema file"""
        franchise_base = self.base_path / "agents" / "franchise" / self.franchise
        
        # Look for franchise-specific schema first
        franchise_schema = franchise_base / "docs" / "warpcore_agent_flow_schema.json"
        if franchise_schema.exists():
            return franchise_schema
        
        # Look for shared franchise docs
        shared_schema = self.base_path / "agents" / "franchise" / "docs" / "warpcore_agent_flow_schema.json"
        if shared_schema.exists():
            return shared_schema
        
        # Fallback to original location
        return self.base_path / "agents" / "docs" / "warpcore_agent_flow_schema.json"
    
    def _resolve_franchise_path(self) -> Path:
        """Resolve franchise-specific agent path"""
        franchise_base = self.base_path / "agents" / "franchise" / self.franchise
        
        # Check if franchise directory exists
        if not franchise_base.exists():
            # Fallback to old flat structure for backward compatibility
            print(f"⚠️ Franchise directory {franchise_base} not found, falling back to flat structure")
            return self.base_path / "agents"
        
        # Staff: agents directly in franchise/staff/agents/
        # Framer: agents in franchise/framer/agents/
        agents_dir = franchise_base / "agents"
        if agents_dir.exists():
            return agents_dir
        else:
            # Fallback to franchise base if agents subdir doesn't exist
            return franchise_base
    
    def _resolve_schema_path(self) -> Path:
        """Resolve franchise-specific schema file"""
        franchise_base = self.base_path / "agents" / "franchise" / self.franchise
        
        # Look for franchise-specific schema first
        franchise_schema = franchise_base / "docs" / "warpcore_agent_flow_schema.json"
        if franchise_schema.exists():
            return franchise_schema
        
        # Look for shared franchise docs
        shared_schema = self.base_path / "agents" / "franchise" / "docs" / "warpcore_agent_flow_schema.json"
        if shared_schema.exists():
            return shared_schema
        
        # Fallback to original location
        return self.base_path / "agents" / "docs" / "warpcore_agent_flow_schema.json"
        
    def _load_mermaid_schema(self) -> Dict[str, Any]:
        """Load the authoritative mermaid schema"""
        try:
            with open(self.mermaid_schema_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Could not load mermaid schema: {e}")
            return {"agent_definitions": {}}
    
    def _discover_agent_files(self) -> Dict[str, Dict[str, Any]]:
        """Dynamically discover all agent files"""
        discovered = {}
        
        if not self.agents_path.exists():
            return discovered
        
        # Find all agent JSON files
        for agent_file in self.agents_path.glob("*.json"):
            if agent_file.name.startswith("__") or agent_file.name in ["docs", "warpcorp"]:
                continue
                
            try:
                with open(agent_file, 'r') as f:
                    agent_data = json.load(f)
                
                agent_id = agent_data.get('agent_id', agent_file.stem)
                
                # Create comprehensive agent info
                discovered[agent_id] = {
                    'file_path': agent_file,
                    'file_name': agent_file.name,
                    'file_stem': agent_file.stem,
                    'agent_data': agent_data,
                    'position': agent_data.get('workflow_position', self._extract_position_from_filename(agent_file.stem)),
                    'dependencies': agent_data.get('dependencies', []),
                    'outputs_to': agent_data.get('outputs_to', [])
                }
                
            except Exception as e:
                print(f"⚠️ Could not load agent file {agent_file}: {e}")
        
        return discovered
    
    def _extract_position_from_filename(self, filename: str) -> str:
        """Extract position from filename convention"""
        # Examples: 0a_origin_... -> 0a, 1b_oracle_... -> 1b
        parts = filename.split('_')
        if len(parts) > 0:
            first_part = parts[0]
            if first_part[0].isdigit():
                return first_part
        return "unknown"
    
    def get_agent_aliases(self) -> Dict[str, str]:
        """Generate agent aliases mapping from discovered agents"""
        aliases = {}
        
        for agent_id, info in self._discovered_agents.items():
            # Use agent_id as alias, map to file_stem
            aliases[agent_id] = info['file_stem']
            
        return aliases
    
    def get_file_to_alias_mapping(self) -> Dict[str, str]:
        """Generate reverse mapping from file names to agent IDs"""
        return {info['file_stem']: agent_id for agent_id, info in self._discovered_agents.items()}
    
    def get_agent_descriptions(self) -> Dict[str, str]:
        """Generate agent descriptions from mermaid schema and discovered agents"""
        descriptions = {}
        
        mermaid_agents = self._mermaid_schema.get("agent_definitions", {})
        
        for agent_id, info in self._discovered_agents.items():
            # Get description from mermaid schema if available
            if agent_id in mermaid_agents:
                mermaid_info = mermaid_agents[agent_id]
                emoji = self._get_agent_emoji(agent_id)
                role = mermaid_info.get('role', 'Unknown Role')
                desc = mermaid_info.get('description', 'No description available')
                descriptions[agent_id] = f"{emoji} {role} - {desc}"
            else:
                # Fallback to agent file data
                descriptions[agent_id] = f"🤖 {agent_id.title()} Agent"
        
        return descriptions
    
    def _get_agent_emoji(self, agent_id: str) -> str:
        """Get appropriate emoji for agent"""
        emoji_map = {
            'origin': '🌟',
            'boss': '👑',
            'pathfinder': '🗺️',
            'architect': '📐',
            'oracle': '🔮',
            'enforcer': '💪',
            'craftsman': '🔨',
            'craftbuddy': '🎨',
            'gatekeeper': '🛡️',
            'mama_bear': '🤱',
            'harmony': '🎭'
        }
        return emoji_map.get(agent_id, '🤖')
    
    def get_agent_workflow_order(self) -> List[str]:
        """Get agents in workflow execution order"""
        ordered = []
        position_map = {}
        
        # Group by position
        for agent_id, info in self._discovered_agents.items():
            position = info['position']
            if position not in position_map:
                position_map[position] = []
            position_map[position].append(agent_id)
        
        # Sort by position
        sorted_positions = sorted(position_map.keys(), key=lambda x: (
            int(x[0]) if x[0].isdigit() else 999,  # Numeric sort
            x[1:] if len(x) > 1 else ''  # Alpha sort for sub-positions
        ))
        
        for position in sorted_positions:
            ordered.extend(position_map[position])
        
        return ordered
    
    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive info for specific agent"""
        if agent_id not in self._discovered_agents:
            return None
        
        info = self._discovered_agents[agent_id].copy()
        
        # Add mermaid schema info if available
        mermaid_agents = self._mermaid_schema.get("agent_definitions", {})
        if agent_id in mermaid_agents:
            info['mermaid_info'] = mermaid_agents[agent_id]
        
        return info
    
    def list_all_agents(self) -> List[str]:
        """List all discovered agent IDs"""
        return list(self._discovered_agents.keys())
    
    def validate_agent_chain(self, agent_chain: List[str]) -> Tuple[bool, List[str]]:
        """Validate that agent chain is valid"""
        valid = True
        errors = []
        
        for agent_id in agent_chain:
            if agent_id not in self._discovered_agents:
                valid = False
                errors.append(f"Unknown agent: {agent_id}")
        
        return valid, errors
    
    def get_agent_flow_info(self) -> Dict[str, Any]:
        """Get complete flow information from mermaid schema"""
        return {
            'flow_relationships': self._mermaid_schema.get('flow_relationships', {}),
            'schema_transformations': self._mermaid_schema.get('schema_transformations', {}),
            'flow_patterns': self._mermaid_schema.get('flow_patterns', {})
        }
    
    def refresh_discovery(self):
        """Refresh agent discovery (useful for development)"""
        self._mermaid_schema = self._load_mermaid_schema()
        self._discovered_agents = self._discover_agent_files()
        print(f"🔄 Refreshed agent discovery: {len(self._discovered_agents)} agents found")