#!/usr/bin/env python3
"""
Agent Execution Utility
Handles individual agent execution, prompt rendering, and shell command interface
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from .agent_discovery import AgentDiscovery

class AgentExecutor:
    """Handles agent execution and shell interface"""
    
    def __init__(self, base_path: Path, client_dir: Path, agent_discovery: AgentDiscovery):
        self.base_path = base_path
        self.client_dir = client_dir
        self.agent_discovery = agent_discovery
    
    def execute_individual_agent(self, agent_alias: str, workflow_id: Optional[str] = None, 
                                user_input_or_spec: Optional[str] = None, 
                                user_input: Optional[Dict] = None) -> bool:
        """Execute individual agent with workflow ID or input"""
        print(f"\n🤖 Executing {agent_alias} agent...")
        
        # Get agent info from discovery system
        agent_info = self.agent_discovery.get_agent_info(agent_alias)
        if not agent_info:
            print(f"❌ Could not find agent: {agent_alias}")
            return False
        
        # Handle user input for ALL agents - not just oracle
        processed_user_input = None
        if user_input_or_spec or user_input:
            processed_user_input = self._handle_universal_user_input(agent_alias, workflow_id, user_input_or_spec, user_input)
        
        # Auto-generate workflow_id if not provided
        if not workflow_id:
            from .workflow_manager import WorkflowManager
            wm = WorkflowManager(self.base_path, self.client_dir)
            workflow_id = wm.generate_workflow_id()
            print(f"🆆 Auto-generated workflow ID: {workflow_id}")
        
        # Load the agent specification
        agent_spec = agent_info['agent_data']
        agent_description = self.agent_discovery.get_agent_descriptions().get(agent_alias, f"{agent_alias} agent")
        print(f"✅ Loaded {agent_description}")
        
        if workflow_id:
            print(f"🆔 Workflow ID: {workflow_id}")
        
        # Execute agent via Warp CLI using agent's actual prompt
        print(f"🔥 Executing {agent_alias} via Warp Agent CLI...")
        print("=" * 50)
        
        # Use the agent's actual prompt from the JSON specification
        agent_prompt = agent_spec.get('prompt', f'Execute {agent_alias} agent')
        
        # Inject user input into prompt for ALL agents
        if processed_user_input:
            if agent_alias == 'oracle':
                # Oracle gets structured user input in its standard format
                agent_prompt = self._inject_oracle_context(agent_prompt, processed_user_input)
            else:
                # All other agents get user input as additional context
                user_context = self._format_user_context_for_agent(agent_alias, processed_user_input, user_input_or_spec)
                agent_prompt = f"{agent_prompt}\n\n{user_context}"
            print(f"💬 Injected user input for {agent_alias} agent")
        
        # Build the warp command to execute the agent with its prompt
        warp_cmd = ['warp', 'agent', 'run', '--prompt', agent_prompt]
        
        print(f"🔥 Command: warp agent run --prompt [agent execution]")
        
        # Execute with real-time output
        result = subprocess.run(
            warp_cmd,
            capture_output=False,  # Allow real-time output
            text=True,
            cwd=str(self.client_dir)  # Run from client directory
        )
        
        success = result.returncode == 0
        
        if success:
            print(f"\n✅ {agent_alias} completed successfully!")
        else:
            print(f"\n⚠️ {agent_alias} finished with return code: {result.returncode}")
        
        return success
    
    def _handle_universal_user_input(self, agent_alias: str, workflow_id: Optional[str], 
                                     user_input_or_spec: Optional[str], user_input: Optional[Dict]) -> Dict[str, Any]:
        """Handle user input processing for all agents"""
        if user_input:
            # Direct user_input passed from workflow
            print(f"💬 Using provided user input for {agent_alias}")
            return user_input
            
        elif user_input_or_spec:
            if user_input_or_spec.endswith('.json') or user_input_or_spec.startswith('/'):
                # It's a file path
                try:
                    with open(user_input_or_spec, 'r') as f:
                        user_input = json.load(f)
                    print(f"📁 Loaded spec file: {user_input_or_spec}")
                    return user_input
                except Exception as e:
                    print(f"❌ Error loading spec file: {e}")
                    return {}
            else:
                # It's direct user input
                from .workflow_manager import WorkflowManager
                wm = WorkflowManager(self.base_path, self.client_dir)
                wf_id = workflow_id or wm.generate_workflow_id()
                
                user_input = {
                    "workflow_id": wf_id,
                    "user_specifications": {
                        "title": "Direct User Input",
                        "description": user_input_or_spec,
                        "requirements_text": user_input_or_spec,
                        "timeline": "TBD",
                        "priorities": ["high"]
                    }
                }
                print(f"💬 Processing user input: {user_input_or_spec[:50]}...")
                return user_input
        else:
            # Interactive input for any agent
            input_prompt = "Enter requirements (or file path): " if agent_alias == 'oracle' else f"Enter input for {agent_alias} (or file path): "
            user_requirements = input(input_prompt).strip()
            if user_requirements.endswith('.json') or user_requirements.startswith('/'):
                try:
                    with open(user_requirements, 'r') as f:
                        user_input = json.load(f)
                    print(f"📁 Loaded spec file: {user_requirements}")
                    return user_input
                except Exception as e:
                    print(f"❌ Error loading file: {e}")
                    return {}
            else:
                from .workflow_manager import WorkflowManager
                wm = WorkflowManager(self.base_path, self.client_dir)
                wf_id = workflow_id or wm.generate_workflow_id()
                
                user_input = {
                    "workflow_id": wf_id,
                    "user_specifications": {
                        "title": "Interactive User Input",
                        "description": user_requirements,
                        "requirements_text": user_requirements,
                        "timeline": "TBD",
                        "priorities": ["high"]
                    }
                }
                return user_input
    
    def _inject_oracle_context(self, agent_prompt: str, user_input_data: Dict[str, Any]) -> str:
        """Inject structured user input context for oracle agent"""
        user_specs = user_input_data.get('user_specifications', {})
        requirements_text = user_specs.get('requirements_text', 'No requirements provided')
        
        oracle_context = f"""

## 🎯 USER INPUT CONTEXT
**User Requirements**: {requirements_text}
**Input Title**: {user_specs.get('title', 'User Input')}
**Description**: {user_specs.get('description', 'No description')}
**Timeline**: {user_specs.get('timeline', 'TBD')}
**Priorities**: {', '.join(user_specs.get('priorities', ['medium']))}

Process these user requirements and convert them into structured analysis following your standard output schema.
"""
        return agent_prompt + oracle_context
    
    def _format_user_context_for_agent(self, agent_alias: str, user_input_data: Dict[str, Any], 
                                       original_input: Optional[str]) -> str:
        """Format user input context appropriate for each agent type"""
        
        # Extract relevant information from user input
        if isinstance(user_input_data, dict) and 'user_specifications' in user_input_data:
            user_specs = user_input_data['user_specifications']
            title = user_specs.get('title', 'User Request')
            description = user_specs.get('description', original_input or 'No description')
            requirements = user_specs.get('requirements_text', original_input or 'No specific requirements')
        else:
            title = 'User Request'
            description = original_input or str(user_input_data) if user_input_data else 'No description'
            requirements = description
        
        # Customize context based on agent role
        agent_contexts = {
            'pathfinder': f"""
## 🎯 USER-DRIVEN ANALYSIS REQUEST
**Focus Area**: {title}
**User Description**: {description}
**Analysis Requirements**: {requirements}

PERFORM YOUR STANDARD CODEBASE ANALYSIS while giving special attention to the user's focus area. 
Ensure your gap analysis addresses the specific requirements mentioned above.
""",
            
            'architect': f"""
## 🏗️ USER REQUIREMENTS INTEGRATION
**User Request**: {title}
**Requirements**: {requirements}
**Context**: {description}

INCORPORATE these user requirements into your standard architectural analysis. 
Generate implementation requirements that address both codebase gaps AND user needs.
""",
            
            'enforcer': f"""
## ⚖️ USER REQUIREMENTS VALIDATION
**User Request**: {title}
**Requirements to Validate**: {requirements}
**Context**: {description}

VALIDATE the generated requirements ensuring they address the user's specific needs while maintaining PAP compliance and feasibility.
""",
            
            'craftsman': f"""
## 🔨 USER-FOCUSED IMPLEMENTATION
**Implementation Goal**: {title}
**User Requirements**: {requirements}
**Context**: {description}

IMPLEMENT the validated requirements with special focus on fulfilling the user's stated needs. 
Ensure your implementation directly addresses the user requirements above.
""",
            
            'craftbuddy': f"""
## 🎨 USER EXPERIENCE ENHANCEMENT
**User Goal**: {title}
**Requirements**: {requirements}
**Context**: {description}

REVIEW the implementation considering the user's original intent. 
Suggest creative enhancements that would better serve the user's needs.
""",
            
            'gatekeeper': f"""
## 🛡️ USER REQUIREMENTS VALIDATION
**Original User Request**: {title}
**Requirements**: {requirements}
**Context**: {description}

VALIDATE that the complete workflow chain has successfully addressed the user's original requirements. 
Ensure quality standards are met AND user needs are fulfilled.
"""
        }
        
        # Return agent-specific context or generic context
        return agent_contexts.get(agent_alias, f"""
## 👤 USER REQUEST CONTEXT
**Request**: {title}
**Details**: {description}
**Requirements**: {requirements}

Address this user request while executing your standard responsibilities for the {agent_alias} agent.
""")
    
    def render_agent_prompt(self, agent_alias: str, workflow_id: Optional[str] = None,
                           user_input_or_spec: Optional[str] = None) -> bool:
        """Render the full prompt for the specified agent without executing it"""
        print(f"\n🎨 Rendering prompt for {agent_alias} agent...")
        
        # Get agent info from discovery system
        agent_info = self.agent_discovery.get_agent_info(agent_alias)
        if not agent_info:
            print(f"❌ Could not find agent: {agent_alias}")
            return False
        
        agent_description = self.agent_discovery.get_agent_descriptions().get(agent_alias, f"{agent_alias} agent")
        print(f"✅ Loaded {agent_description}")
        
        if workflow_id:
            print(f"🆔 Workflow ID: {workflow_id}")
        
        # Get the agent's prompt from the JSON specification
        agent_spec = agent_info['agent_data']
        agent_prompt = agent_spec.get('prompt', f'No prompt found for {agent_alias} agent')
        
        print(f"\n{'='*80}")
        print(f"🔮 FULL PROMPT FOR {agent_alias.upper()} AGENT")
        print(f"{'='*80}")
        print(agent_prompt)
        print(f"{'='*80}")
        
        return True
    
    def show_agent_help(self) -> None:
        """Display rich emoji-driven help for all agents"""
        print("\n" + "=" * 80)
        print("🎆 WARPCORE AGENCY - Agent Command Center 🎆")
        print("=" * 80)
        
        print("🎭 Agent Roster:")
        print()
        
        # Get agents in workflow order from discovery system
        workflow_order = self.agent_discovery.get_agent_workflow_order()
        agent_descriptions = self.agent_discovery.get_agent_descriptions()
        
        for i, agent_id in enumerate(workflow_order):
            if agent_id in ["mama_bear", "harmony"]:
                continue  # Skip dev tools for main roster
            description = agent_descriptions.get(agent_id, f"{agent_id} - Description not available")
            position = agent_id.upper()
            print(f"  {position:>12}. {description}")
        
        print("\n" + "-" * 80)
        print("🔄 Workflow Patterns:")
        print()
        
        # Show flow from mermaid schema
        flow_info = self.agent_discovery.get_agent_flow_info()
        linear_flow = flow_info.get('flow_relationships', {}).get('linear_flow', [])
        
        if linear_flow:
            flow_chain = []
            for flow in linear_flow:
                if flow['from'] not in [f['to'] for f in flow_chain]:
                    flow_chain.append(f"{flow['from']} → {flow['to']}")
            
            print("🗺️ Main Analysis Chain:")
            print("  " + " → ".join([f['from'] for f in linear_flow[:3]] + [linear_flow[-1]['to']]))
        
        print("\n🛠️ Development Tools (Standalone):")
        for agent_id in ["mama_bear", "harmony"]:
            if agent_id in agent_descriptions:
                print(f"  {agent_descriptions[agent_id]}")
        
        print("\n" + "-" * 80)
        print("📝 Usage Examples:")
        print("  python agency.py pathfinder  # Run the schema analysis")
        print("  python agency.py oracle      # Process user input")
        print("  python agency.py craftsman   # Execute implementation")
        print("  python agency.py agents      # Show this help")
        
        print("\n" + "=" * 80)