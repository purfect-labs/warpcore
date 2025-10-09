#!/usr/bin/env python3
"""
Universal Franchise-Agnostic Schema System
Simple, elegant, and capable of supporting all franchises (existing and new)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path
import json

class UniversalAgentSchema:
    """Universal schema that works for any agent in any franchise"""
    
    # Core shared components across ALL agents in ALL franchises
    UNIVERSAL_BASE = {
        "workflow_id": "string (from context)",
        "agent_id": "string (agent identifier)", 
        "timestamp": "string (ISO_TIMESTAMP)",
        "execution_metrics": {
            "start_time": "string (ISO_TIMESTAMP)",
            "end_time": "string (ISO_TIMESTAMP)",
            "duration_seconds": "number",
            "memory_usage_mb": "number",
            "cpu_usage_percent": "number"
        },
        "performance_metrics": {
            "output_quality_score": "number (0-100)",
            "efficiency_rating": "EXCELLENT|GOOD|FAIR|POOR"
        },
        "data_compression": {
            "compressed_past_workflows": "boolean",
            "compression_ratio": "number (0-1)",
            "archived_workflow_count": "number", 
            "storage_saved_mb": "number",
            "compression_method": "gzip|json_minify|archive"
        },
        "bonus_contributions": {
            "extra_analysis_performed": "boolean",
            "additional_requirements_discovered": "number",
            "enhanced_validation_checks": "array of strings",
            "proactive_improvements_suggested": "number",
            "cross_workflow_insights": "array of insight objects",
            "contribution_value_score": "number (0-100)"
        }
    }
    
    UNIVERSAL_VALIDATION_RULES = [
        "workflow_id must be properly validated",
        "data compression must be attempted for storage optimization",
        "bonus contributions must be identified and quantified"
    ]
    
    UNIVERSAL_SUCCESS_CRITERIA = [
        "Historical workflow data compressed for storage efficiency",
        "Bonus contributions identified and tracked for system improvement"
    ]
    
    @classmethod
    def enhance_agent(cls, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance any agent from any franchise with universal schema components"""
        enhanced = agent_data.copy()
        
        # Ensure output_schema has universal base
        if 'output_schema' not in enhanced:
            enhanced['output_schema'] = {}
        
        # Add universal base components
        for key, value in cls.UNIVERSAL_BASE.items():
            if key not in enhanced['output_schema']:
                enhanced['output_schema'][key] = value
        
        # Enhance validation rules
        if 'validation_rules' not in enhanced:
            enhanced['validation_rules'] = []
        
        existing_rules = set(enhanced['validation_rules'])
        new_rules = set(cls.UNIVERSAL_VALIDATION_RULES)
        enhanced['validation_rules'] = list(existing_rules.union(new_rules))
        
        # Enhance success criteria
        if 'success_criteria' not in enhanced:
            enhanced['success_criteria'] = []
            
        existing_criteria = set(enhanced['success_criteria'])
        new_criteria = set(cls.UNIVERSAL_SUCCESS_CRITERIA)
        enhanced['success_criteria'] = list(existing_criteria.union(new_criteria))
        
        return enhanced

class EnvironmentContext:
    """Generate universal environment context for any franchise"""
    
    @staticmethod
    def generate(target_directory: Optional[str] = None) -> str:
        """Generate environment context that works for any franchise/agent"""
        import os, platform
        from datetime import datetime
        
        if target_directory:
            working_dir = str(Path(target_directory).resolve())
        else:
            working_dir = "/Users/shawn_meredith/code/pets/warpcore"
        
        return f"""
## ENVIRONMENT CONTEXT (DO NOT DISCOVER - USE THIS INFO)

**Current Working Directory**: {working_dir}
**Platform**: {platform.system()}
**Shell**: {os.environ.get('SHELL', 'unknown')}
**Python**: {platform.python_version()}
**Home**: {os.environ.get('HOME', '~')}
**Timestamp**: {datetime.now().isoformat()}

### PROJECT STRUCTURE (DYNAMIC - DO NOT SCAN)
```
{working_dir}/
├── .data/                     # Workflow cache and results
├── .config/                   # Configuration files
├── src/agency/                # Main agency system
│   ├── agents/               # Agent JSON specifications
│   │   ├── franchise/        # Franchise-specific agents
│   │   ├── polymorphic/      # Universal schema system
│   │   └── docs/             # Documentation system
│   ├── systems/              # Schema and system management
│   ├── workflows/            # Workflow specifications
│   └── agency.py             # Main orchestrator
├── src/api/                   # PAP architecture implementation
├── docs/                     # Documentation
└── llm-collector/            # LLM collection utility
```

### AVAILABLE TOOLS AND PRIMITIVES
**File Operations**: read_files, write_files, file_glob, find_files
**Execution**: run_command, subprocess, shell scripting
**Git**: Full git repository with version control
**Database**: SQLite available, existing licensing database
**Config**: Hierarchical config system (.config/warpcore.config)
**Logging**: Background logging to /tmp/ for non-blocking operations
**Testing**: Playwright, pytest, multi-layer validation

**IMPORTANT**: Use this context - do NOT waste time discovering what you already know!
"""

class FranchiseSchemaManager:
    """Simple manager that works with any franchise structure"""
    
    @staticmethod
    def enhance_franchise_agents(agents_directory: Path) -> int:
        """Enhance all agents in a franchise directory with universal schema"""
        count = 0
        
        # Find all JSON files in the directory
        for json_file in agents_directory.glob("*.json"):
            try:
                # Load agent data
                with open(json_file, 'r') as f:
                    agent_data = json.load(f)
                
                # Apply universal enhancements
                enhanced_data = UniversalAgentSchema.enhance_agent(agent_data)
                
                # Add environment context if prompt exists and doesn't have it
                if ('prompt' in enhanced_data and 
                    "## ENVIRONMENT CONTEXT" not in enhanced_data['prompt']):
                    env_context = EnvironmentContext.generate()
                    enhanced_data['prompt'] = env_context + "\n\n" + enhanced_data['prompt']
                
                # Write back enhanced data
                with open(json_file, 'w') as f:
                    json.dump(enhanced_data, f, indent=2)
                
                count += 1
                print(f"✅ Enhanced {json_file.name}")
                
            except Exception as e:
                print(f"⚠️ Could not enhance {json_file.name}: {e}")
        
        return count
    
    @staticmethod
    def scan_all_franchises(agents_root: Path) -> Dict[str, int]:
        """Scan and enhance all franchises in the agents directory"""
        results = {}
        
        # Look for franchise directories
        franchise_dir = agents_root / "franchise"
        if not franchise_dir.exists():
            return results
        
        for franchise_path in franchise_dir.iterdir():
            if franchise_path.is_dir():
                agents_path = franchise_path / "agents"
                if agents_path.exists():
                    count = FranchiseSchemaManager.enhance_franchise_agents(agents_path)
                    results[franchise_path.name] = count
                    print(f"🏢 {franchise_path.name} franchise: {count} agents enhanced")
        
        return results

# Simple, elegant API
def enhance_agents(agents_directory: str) -> int:
    """Simple function to enhance any agents directory"""
    return FranchiseSchemaManager.enhance_franchise_agents(Path(agents_directory))

def enhance_all_franchises(agents_root: str = None) -> Dict[str, int]:
    """Simple function to enhance all franchises"""
    if not agents_root:
        agents_root = Path(__file__).parent.parent
    return FranchiseSchemaManager.scan_all_franchises(Path(agents_root))