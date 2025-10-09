#!/usr/bin/env python3
"""
Franchise Context Injection Utility
Uses only JSON file data and agent_ids - no complex parsing
"""

from pathlib import Path
from typing import Dict, Any, Optional
import os
import json

class FranchiseContextInjector:
    """Injects franchise-specific context into agent prompts"""
    
    def __init__(self, franchise: str = "staff", base_path: Optional[Path] = None):
        self.franchise = franchise
        self.base_path = base_path or Path(__file__).parent.parent
        self.franchise_base = self.base_path / "agents" / "franchise"
        
        # Auto-discover franchises from filesystem
        self.discovered_franchises = self._discover_franchises()
        self.context_templates = self._generate_context_templates()
    
    def _discover_franchises(self) -> Dict[str, Dict[str, Any]]:
        """Auto-discover franchise directories and agent info from JSON files"""
        franchises = {}
        
        if not self.franchise_base.exists():
            return franchises
        
        for franchise_dir in self.franchise_base.glob("*/"):
            if franchise_dir.name in ['docs', '__pycache__', '.git']:
                continue
            
            franchise_name = franchise_dir.name
            agents_dir = franchise_dir / "agents"
            
            if agents_dir.exists():
                agent_files = list(agents_dir.glob("*.json"))
                agent_names = []
                
                for agent_file in agent_files:
                    try:
                        with open(agent_file, 'r') as f:
                            agent_data = json.load(f)
                        agent_id = agent_data.get('agent_id', agent_file.stem)
                        agent_names.append(agent_id)
                    except Exception:
                        pass
                
                franchises[franchise_name] = {
                    'name': franchise_name,
                    'display_name': franchise_name.title(),
                    'path': franchise_dir,
                    'agents_dir': agents_dir,
                    'agent_count': len(agent_files),
                    'agent_names': agent_names,
                    'focus': 'Software Development' if franchise_name == 'staff' else 'Content Intelligence'
                }
        
        return franchises
    
    def _generate_context_templates(self) -> Dict[str, str]:
        """Generate simple context templates"""
        templates = {}
        
        for franchise_name, info in self.discovered_franchises.items():
            templates[franchise_name] = f'''
## {info['display_name'].upper()} FRANCHISE CONTEXT ({info['focus'].upper()})

**Current Working Directory**: {{client_dir_absolute}}
**Franchise**: {info['display_name']} ({info['focus']})
**Agent**: {{agent_id}}
**Total Agents**: {info['agent_count']}

### FRANCHISE CACHE ISOLATION
**Primary Cache**: {{primary_cache}}/franchise/{franchise_name}/
**Secondary Cache**: {{secondary_cache}}/franchise/{franchise_name}/

### AVAILABLE AGENTS
{', '.join(info['agent_names'])}

### MISSION
Transform requirements into high-quality {info['focus'].lower()} implementations.
'''
        
        return templates
    
    def inject_context(self, agent_spec: Dict[str, Any], **context_vars) -> Dict[str, Any]:
        """Inject franchise-specific context into agent prompt"""
        if self.franchise not in self.context_templates:
            return agent_spec
        
        enhanced_spec = agent_spec.copy()
        
        # Default context variables
        default_vars = {
            'client_dir_absolute': context_vars.get('client_dir_absolute', os.getcwd()),
            'agent_id': context_vars.get('agent_id', 'unknown'),
            'primary_cache': context_vars.get('primary_cache', '.data'),
            'secondary_cache': context_vars.get('secondary_cache', '.data')
        }
        
        all_vars = {**default_vars, **context_vars}
        
        # Format and inject context
        try:
            context_header = self.context_templates[self.franchise].format(**all_vars)
            original_prompt = enhanced_spec.get('prompt', '')
            enhanced_spec['prompt'] = context_header + '\n\n' + original_prompt
        except KeyError:
            pass  # Skip context injection if formatting fails
        
        return enhanced_spec
    
    def get_franchise_info(self) -> Dict[str, Any]:
        """Get franchise information"""
        if self.franchise in self.discovered_franchises:
            data = self.discovered_franchises[self.franchise]
            return {
                "name": f"{data['display_name']} Franchise",
                "focus": data['focus'],
                "agent_count": data['agent_count'],
                "agent_names": data['agent_names'],
                "path": str(data['path'])
            }
        
        return {"name": f"{self.franchise.title()} Franchise", "focus": "Unknown", "agent_count": 0}
    
    def list_available_franchises(self) -> Dict[str, Dict[str, Any]]:
        """List discovered franchises"""
        return self.discovered_franchises.copy()
    
    def validate_franchise(self, franchise: str) -> bool:
        """Check if franchise is supported"""
        return franchise in self.context_templates