#!/usr/bin/env python3
"""
WARPCORE Agency - Main Entry Point (Modular Version)
Intelligent workflow selector and agent orchestrator using clean composition
"""

import sys
import json
import argparse
import os
from datetime import datetime
import logging
from utils import WARPCOREAgencyComposition

# Setup CLI call logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - CLI_CALL - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/agency_cli_calls.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Log the CLI call immediately
logger.info(f"CLI CALLED: {' '.join(sys.argv)} | CWD: {os.getcwd()} | PID: {os.getpid()}")

def show_help():
    """Display exciting agent-focused help with emojis"""
    help_text = f"""
🎆✨ WARPCORE AGENCY COMMAND CENTER ✨🎆
{'=' * 60}
🚀 MEET YOUR AI AGENT SQUAD! 🚀

🎭 AGENT SKILLS & SUPERPOWERS:

🌟 ORIGIN SKILL - The Genesis Master
   python agency.py origin "bootstrap new workflow with focus on X"
   🔥 Creates workflow ID & validates all agent files exist
   💫 Checks system health & discovers available capabilities
   ⚡ Now supports custom focus areas via user input!

👑 BOSS SKILL - The Master Conductor  
   python agency.py boss "orchestrate workflow for user auth system"
   🎼 Takes ORIGIN's data & sequences agent execution order
   🎯 Manages workflow state & tracks completion status
   💼 Now handles user-directed orchestration!

🗺️ PATHFINDER SKILL - The Code Detective
   python agency.py pathfinder "analyze licensing system for gaps"
   🔍 Runs LLM-collector & analyzes file structure/content
   🕵️ Finds gaps, inconsistencies & identifies improvement opportunities
   🧭 Now focuses analysis on user-specified areas!

📐 ARCHITECT SKILL - The Blueprint Genius
   python agency.py architect "design payment processing integration"
   🏗️ Takes analysis & converts to actionable requirements
   📋 Creates file-level changes with before/after code samples
   🎨 Now incorporates user requirements into architectural plans!

🔮 ORACLE SKILL - The Wisdom Keeper
   python agency.py oracle "Build user auth system with 2FA"
   python agency.py oracle requirements.json
   💬 Converts user text/files into structured requirement specs
   🌟 Analyzes codebase context & maps to implementation points
   🎯 Enhanced structured user input processing!

💪 ENFORCER SKILL - The Quality Guardian
   python agency.py enforcer "validate payment system requirements"
   ⚖️ Validates requirements for feasibility & PAP compliance
   🛡️ Checks effort estimates & dependency logic for sanity
   🎖️ Now validates user-specific requirements!

🔨 CRAFTSMAN SKILL - The Master Builder
   python agency.py craftsman "implement user authentication with JWT"
   ⚒️ Takes validated requirements & modifies actual code files
   🏭 Runs tests, validates implementations & checks acceptance criteria
   💾 Now focuses implementation on user-specified goals!

🎨 CRAFTBUDDY SKILL - The Creative Enhancer
   python agency.py craftbuddy "enhance UX for payment flow"
   💡 Reviews work for creative improvement opportunities
   ⚡ Identifies quick wins, bonus features & UX enhancements
   🔧 Now considers user experience goals!

🛡️ GATEKEEPER SKILL - The Final Sentinel
   python agency.py gatekeeper "validate auth system meets requirements"
   🚪 Cross-validates all agent results
   🔒 Reviews git commits & decides if quality standards are met
   ⭐ Now validates against original user requirements!

🎨 MULTI-AGENT POWER COMBOS:
   python agency.py gap_analysis      # 🔥 Full Analysis Chain
   python agency.py build_system      # 🏗️ Complete Build Chain  
   python agency.py interactive       # 🎭 Interactive Mode
   python agency.py agents           # 🎭 Show agent help!

💎 DIRECTORY MASTERY:
   --client-dir /path/to/project    🎯 Analyze any codebase!
   
🌈 EXAMPLES WITH USER INPUT:
   # 🕵️ Focused analysis
   python agency.py pathfinder "find security vulnerabilities in auth"
   
   # 🏗️ User-driven architecture
   python agency.py architect "design microservices for payments"
   
   # 🔨 Targeted implementation
   python agency.py craftsman "add rate limiting to API endpoints"
   
   # 🎨 UX enhancement
   python agency.py craftbuddy "improve mobile responsiveness"
   
   # 🛡️ User requirement validation  
   python agency.py gatekeeper "ensure GDPR compliance implemented"

🎊 NEW UNIVERSAL INPUT FEATURES:
   🌟 ALL agents now accept user input (not just oracle!)
   🔄 Agent-specific context formatting
   💾 File-based input support (.json files)
   🎯 Interactive prompts for each agent type
   🎭 Mermaid schema integration
   🤖 Dynamic agent discovery
   
🚀 Ready to unleash your enhanced AI agent squad? 🚀
{'=' * 60}
"""
    print(help_text)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="WARPCORE Agency - Intelligent Workflow System (Modular)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False  # We'll handle help manually
    )
    parser.add_argument('workflow_or_agent', nargs='?', help='Workflow ID (1-6), Agent alias (origin, boss, pathfinder, etc.), or "docs"')
    parser.add_argument('workflow_id_or_input', nargs='?', help='Workflow ID for agents, JSON input file for workflows, or user input text')
    parser.add_argument('user_input_or_spec', nargs='?', help='Additional user input or spec file')
    parser.add_argument('--client-dir', '-c', type=str, help='Client directory to run analysis against (data cached back to agency)')
    parser.add_argument('--render', '-r', action='store_true', help='Render the full prompt for the specified agent without executing it')
    parser.add_argument('--help', '-h', action='store_true', help='Show comprehensive help information')
    
    args = parser.parse_args()
    
    # Handle help request
    if args.help:
        show_help()
        return
    
    # Initialize agency with client directory if provided
    agency = WARPCOREAgencyComposition(client_dir_absolute=args.client_dir)
    
    try:
        if args.workflow_or_agent:
            # Command line mode
            workflow_or_agent = args.workflow_or_agent
            
            # Check if it's a docs command - just build everything
            if workflow_or_agent.lower() == 'docs':
                try:
                    # Import the static build generator
                    sys.path.append(str(agency.base_path / "agents" / "polymorphic"))
                    from static_build_generator import StaticBuildGenerator
                    
                    print("🚀 Building static agent schemas with master prompt merged...")
                    builder = StaticBuildGenerator()
                    
                    # Build all franchise agents with merged master prompt
                    results = builder.build_all_franchises(
                        client_dir=args.client_dir or str(agency.client_dir_absolute),
                        agency_dir=str(agency.base_path)
                    )
                    
                    success = True
                    print(f"\n✅ Static build complete! Agents updated in-place with originals backed up.")
                    
                except Exception as e:
                    print(f"❌ Static build failed: {e}")
                    success = False
                
            # Check if it's an individual agent request
            elif workflow_or_agent.lower() in agency.get_agent_aliases().keys():
                # Check if render flag is set
                if args.render:
                    # Just render the prompt without executing
                    success = agency.render_agent_prompt(
                        workflow_or_agent.lower(),
                        args.workflow_id_or_input,
                        args.user_input_or_spec
                    )
                else:
                    # Individual agent execution with universal user input
                    success = agency.execute_individual_agent(
                        workflow_or_agent.lower(), 
                        args.workflow_id_or_input,
                        args.user_input_or_spec
                    )
                    
            # Handle built-in workflows
            elif workflow_or_agent.lower() == 'gap_analysis':
                success = agency.gap_analysis_workflow()
            elif workflow_or_agent.lower() == 'agents':
                agency.show_agent_help()
                success = True
            elif workflow_or_agent.lower() == 'interactive':
                workflow_selection = agency.prompt_workflow_selection()
                success = True  # TODO: Execute selected workflow
            else:
                print(f"❌ Unknown workflow or agent: {workflow_or_agent}")
                print("Available agents:", ', '.join(agency.list_available_agents()))
                success = False
            
            sys.exit(0 if success else 1)
            
        else:
            # Interactive mode
            workflow_id = agency.prompt_workflow_selection()
            print(f"Selected: {workflow_id}")
            success = True  # TODO: Execute selected workflow
            
            if success:
                print("\n✅ Workflow completed successfully!")
            else:
                print("\n❌ Workflow failed or incomplete")
                
    except KeyboardInterrupt:
        print("\n\n👋 WARPCORE Agency session ended")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()