# WARPCORE Directory Restructure Plan

## 🎯 **Current State - Scattered Structure**
```
warpcore/
├── .workflows/warp/dev/           # Agent specs & scripts scattered
├── src/                           # Some core code
├── llm-collector/                 # Utility scripts
└── Various root files             # Configuration, docs, etc.
```

## 🏗️ **Proposed New Structure - Clean & Organized**
```
warpcore/
├── src/
│   ├── agency/                    # Main agency system
│   │   ├── __init__.py
│   │   ├── agency.py              # Main entry point - workflow selector
│   │   ├── agents/                # All agent specifications
│   │   │   ├── __init__.py
│   │   │   ├── bootstrap.json
│   │   │   ├── orchestrator.json
│   │   │   ├── schema_reconciler.json
│   │   │   ├── requirements_generator.json
│   │   │   ├── requirements_validator.json
│   │   │   ├── implementor.json
│   │   │   ├── gate_promote.json
│   │   │   └── user_input_translator.json
│   │   ├── systems/               # Agent management systems
│   │   │   ├── __init__.py
│   │   │   ├── agent_schema_system.py
│   │   │   ├── compression_manager.py
│   │   │   ├── workflow_orchestrator.py
│   │   │   └── data_manager.py
│   │   ├── workflows/             # Workflow definitions
│   │   │   ├── __init__.py
│   │   │   ├── gap_analysis_workflow.py
│   │   │   └── security_licensing_workflow.py
│   │   ├── web/                   # Web dashboard (moved from .workflows)
│   │   │   ├── static/
│   │   │   │   ├── css/
│   │   │   │   ├── js/
│   │   │   │   └── images/
│   │   │   ├── templates/
│   │   │   ├── api/
│   │   │   └── server.py
│   │   └── utils/                 # Shared utilities
│   │       ├── __init__.py
│   │       ├── file_manager.py
│   │       ├── git_operations.py
│   │       └── validation.py
│   ├── api/                       # Existing API code
│   ├── data/                      # Existing data layer
│   ├── web/                       # Existing web layer
│   └── testing/                   # Existing testing
├── .data/                         # Data management (new structure)
│   ├── compressed/                # Git-tracked summaries
│   ├── full/                      # Local complete data (gitignored)
│   ├── current/                   # Active workflows (gitignored)
│   └── archive/                   # Old workflows (gitignored)
├── llm-collector/                 # Keep as is
├── config/                        # Configuration files
└── docs/                          # Documentation
```

## 🔄 **Migration Steps**

### Step 1: Create New Structure
```bash
# Create main agency structure
mkdir -p src/agency/{agents,systems,workflows,web,utils}
mkdir -p .data/{compressed,full,current,archive}

# Create __init__.py files
touch src/agency/__init__.py
touch src/agency/{agents,systems,workflows,utils}/__init__.py
```

### Step 2: Move Agent Files
```bash
# Move agent specifications to clean names
mv .workflows/warp/dev/gap_analysis_agent_0x_bootstrap.json src/agency/agents/bootstrap.json
mv .workflows/warp/dev/gap_analysis_agent_0_orchestrator.json src/agency/agents/orchestrator.json
mv .workflows/warp/dev/gap_analysis_agent_1_schema_reconciler.json src/agency/agents/schema_reconciler.json
mv .workflows/warp/dev/gap_analysis_agent_2_requirements_generator.json src/agency/agents/requirements_generator.json
mv .workflows/warp/dev/gap_analysis_agent_3_requirements_validator.json src/agency/agents/requirements_validator.json
mv .workflows/warp/dev/gap_analysis_agent_4_implementor.json src/agency/agents/implementor.json
mv .workflows/warp/dev/gap_analysis_agent_5_gate_promote.json src/agency/agents/gate_promote.json
mv .workflows/warp/dev/user_input_requirements_translator.json src/agency/agents/user_input_translator.json
```

### Step 3: Move System Files
```bash
# Move system management scripts
mv .workflows/warp/dev/agent_schema_system.py src/agency/systems/
mv .workflows/warp/dev/add_compression_to_agents.py src/agency/systems/compression_manager.py
```

### Step 4: Move Web Dashboard
```bash
# Move web dashboard to agency
mv .workflows/warp/dev/web src/agency/web
```

### Step 5: Update References
- Update all file paths in agent specifications
- Update imports in system files
- Update web dashboard asset paths
- Update documentation

## 🎯 **Entry Point - agency.py**

```python
#!/usr/bin/env python3
"""
WARPCORE Agency - Main Entry Point
Workflow selector and agent orchestrator
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional

class WARPCOREAgency:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.agents_path = self.base_path / "agents"
        self.workflows_path = self.base_path / "workflows"
    
    def list_available_workflows(self):
        """List all available workflows"""
        workflows = {
            "1": "Gap Analysis Workflow - Analyze codebase gaps and generate fixes",
            "2": "Security Licensing Workflow - Implement license management system", 
            "3": "Manual Requirements Entry - Convert user specs to structured requirements",
            "4": "Custom Workflow - Build custom agent chain"
        }
        return workflows
    
    def prompt_workflow_selection(self):
        """Interactive workflow selection"""
        print("🚀 WARPCORE Agency - Intelligent Workflow System")
        print("=" * 50)
        
        workflows = self.list_available_workflows()
        for key, description in workflows.items():
            print(f"{key}. {description}")
        
        selection = input("\nSelect workflow (1-4): ").strip()
        return selection
    
    def execute_workflow(self, workflow_id: str, user_input: Optional[Dict] = None):
        """Execute selected workflow"""
        workflow_map = {
            "1": self.gap_analysis_workflow,
            "2": self.security_licensing_workflow,
            "3": self.manual_requirements_workflow,
            "4": self.custom_workflow
        }
        
        workflow_func = workflow_map.get(workflow_id)
        if workflow_func:
            return workflow_func(user_input)
        else:
            print(f"❌ Unknown workflow: {workflow_id}")
            return False

def main():
    agency = WARPCOREAgency()
    
    if len(sys.argv) > 1:
        # Command line mode
        workflow_id = sys.argv[1]
        agency.execute_workflow(workflow_id)
    else:
        # Interactive mode
        workflow_id = agency.prompt_workflow_selection()
        agency.execute_workflow(workflow_id)

if __name__ == "__main__":
    main()
```

## 📋 **Benefits of New Structure**

1. **Clean Organization**: Everything in logical nested structure
2. **Easy Navigation**: Clear separation of agents, systems, workflows
3. **Importable Modules**: Proper Python package structure
4. **Scalable**: Easy to add new agents, workflows, utilities
5. **Maintainable**: Related code grouped together
6. **Professional**: Industry-standard Python project layout

## 🔄 **Next Steps After Restructure**

1. Update all file references in agent specifications
2. Create proper Python imports throughout system
3. Update web dashboard to use new paths
4. Complete the manual spec generator agent
5. Implement the agency.py entry point
6. Update documentation and README files

**This restructure will transform WARPCORE from scattered files into a professional, maintainable agency system!**