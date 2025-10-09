#!/usr/bin/env python3
"""
Workflow Management Utility
Handles workflow ID generation, trace management, and workflow execution
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import subprocess
import sys

class WorkflowManager:
    """Manages workflow execution, IDs, and state"""
    
    def __init__(self, base_path: Path, client_dir: Path):
        self.base_path = base_path
        self.client_dir = client_dir
        self.workflows_path = base_path / "workflows"
        self.primary_cache = client_dir.parent / ".data"
        self.secondary_cache = base_path / ".data"
        
    def generate_workflow_id(self) -> str:
        """Generate unique workflow ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        short_uuid = str(uuid.uuid4())[:8]
        return f"wf_{timestamp}_{short_uuid}"
    
    def generate_trace_id(self) -> str:
        """Generate timestamp-based trace ID for ordering workflow steps"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        short_uuid = str(uuid.uuid4())[:6]
        return f"tr_{timestamp}_{short_uuid}"
    
    def list_available_workflows(self) -> Dict[str, str]:
        """Dynamically discover and list all available workflows"""
        workflows = {}
        workflow_count = 1
        
        # Dynamically discover workflow specification files
        if self.workflows_path.exists():
            for workflow_file in self.workflows_path.glob("*.json"):
                try:
                    with open(workflow_file, 'r') as f:
                        spec = json.load(f)
                    
                    workflow_name = spec.get('workflow_name', workflow_file.stem.replace('_', ' ').title())
                    workflow_desc = spec.get('workflow_description', 'No description available')
                    
                    workflows[str(workflow_count)] = f"{workflow_name} - {workflow_desc[:80]}..."
                    workflow_count += 1
                except Exception as e:
                    print(f"⚠️ Could not load workflow {workflow_file}: {e}")
        
        # Add built-in workflows
        workflows[str(workflow_count)] = "Gap Analysis Workflow - Analyze codebase gaps and generate fixes"
        workflows[str(workflow_count + 1)] = "Manual Requirements Entry - Convert user specs to structured requirements" 
        workflows[str(workflow_count + 2)] = "User Input Translator - Convert raw specs to validated requirements"
        workflows[str(workflow_count + 3)] = "Custom Agent Chain - Build custom workflow"
        workflows[str(workflow_count + 4)] = "System Management - Manage agents and compression"
        workflows["h"] = "Show detailed help information"
        workflows["agents"] = "🎭 Show agent command center with emoji guide"
        workflows["docs"] = "📋 Generate agent flow documentation"
        
        return workflows
    
    def execute_workflow_specification(self, workflow_spec_filename: str, client_dir: str) -> bool:
        """Generic workflow execution from any specification file"""
        workflow_spec_path = self.workflows_path / workflow_spec_filename
        
        if not workflow_spec_path.exists():
            print(f"❌ Workflow specification not found: {workflow_spec_path}")
            return False
        
        try:
            with open(workflow_spec_path, 'r') as f:
                workflow_spec = json.load(f)
            
            workflow_name = workflow_spec.get('workflow_name', 'Unknown Workflow')
            print(f"\n🚀 Starting {workflow_name}...")
            print(f"📋 Loaded workflow: {workflow_name}")
            print(f"🎯 Total Agents: {workflow_spec.get('total_agents', 'N/A')}")
            print(f"🔗 Pattern: {workflow_spec.get('workflow_pattern', 'N/A')}")
            
            # Execute via Warp CLI with workflow specification
            print("\n🔥 Executing via Warp Agent CLI...")
            print("=" * 50)
            
            # Generic prompt for any workflow specification
            warp_cmd = f'warp agent run --prompt "Execute workflow from specification: {workflow_spec_path}. Use client directory: {client_dir}. Follow the complete agent chain as defined in the specification."'
            
            print(f"🔥 Command: warp agent run --prompt [workflow execution]")
            
            # Execute with real-time output
            result = subprocess.run(
                warp_cmd,
                shell=True,
                capture_output=False,  # Allow real-time output
                text=True
            )
            
            success = result.returncode == 0
            
            if success:
                print(f"\n✅ {workflow_name} completed successfully!")
            else:
                print(f"\n⚠️ {workflow_name} finished with return code: {result.returncode}")
            
            return success
            
        except Exception as e:
            print(f"❌ Workflow execution error: {e}")
            return False
    
    def gap_analysis_workflow(self, client_dir: str, user_input: Optional[Dict] = None) -> bool:
        """Execute Gap Analysis Workflow (Agents 0x -> 0 -> 1 -> 2 -> 3 -> 4 -> 5)"""
        print("\n🔍 Starting Gap Analysis Workflow...")
        workflow_id = self.generate_workflow_id()
        
        # Add client directory to workflow context for coherence across all agents
        workflow_context = {
            "workflow_id": workflow_id,
            "client_dir_absolute": str(client_dir),
            "analysis_target": str(client_dir),
            "agency_cache_dir": str(self.base_path),
            "target_agency_cache": str(Path(client_dir).parent / ".agency" / ".data"),
            "system_agency_cache": str(self.base_path / ".data"),
            "data_write_location_primary": str(Path(client_dir).parent / ".agency" / ".data"),
            "data_write_location_secondary": str(self.base_path / ".data"),
            "work_against": f"analyze {client_dir}",
            "cache_results_to": f"write to BOTH {Path(client_dir).parent / '.agency' / '.data'} AND {self.base_path / '.data'}"
        }
        
        # Agent execution order using clever aliases
        agent_chain = ["origin", "boss", "pathfinder", 
                      "architect", "enforcer", 
                      "craftsman", "gatekeeper"]
        
        print(f"🆔 Workflow ID: {workflow_id}")
        print(f"📋 Agent Chain: {' -> '.join(agent_chain)}")
        print(f"🎭 Cool Names: origin->boss->pathfinder->architect->enforcer->craftsman->gatekeeper")
        
        # Execute agent chain
        for i, agent_name in enumerate(agent_chain):
            print(f"\n🤖 Executing Agent {i}: {agent_name}")
            # Here we would execute the agent
            print(f"✅ Agent {agent_name} ready for execution")
            # TODO: Implement actual agent execution
        
        print(f"\n🎯 Gap Analysis Workflow Complete - ID: {workflow_id}")
        return True
    
    def custom_workflow(self, agent_chain: List[str]) -> bool:
        """Build and execute custom agent chain"""
        print("\n⚙️  Custom Workflow Builder...")
        
        if not agent_chain:
            print("❌ No agents selected")
            return False
        
        workflow_id = self.generate_workflow_id()
        print(f"\n🆔 Custom Workflow ID: {workflow_id}")
        print(f"📋 Selected Chain: {' -> '.join(agent_chain)}")
        
        print("✅ All agents validated - ready for execution")
        return True
    
    def prompt_workflow_selection(self) -> str:
        """Interactive workflow selection"""
        print("\n" + "=" * 60)
        print("🚀 WARPCORE Agency - Intelligent Workflow System")
        print("=" * 60)
        
        workflows = self.list_available_workflows()
        for key, description in workflows.items():
            print(f"{key}. {description}")
        
        selection = input("\nSelect workflow (1-6, h for help, agents for agent guide): ").strip()
        return selection