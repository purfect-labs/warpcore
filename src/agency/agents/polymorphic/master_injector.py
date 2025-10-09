#!/usr/bin/env python3
"""
Master Prompt Injection Engine
Uses master_prompt.json to inject comprehensive pre-prompt content into all agents
Extracted from legacy agency.py commit f3babb0
"""

import json
import os
import glob
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

class MasterPromptInjector:
    """Injects master prompt content into all agent JSON files"""
    
    def __init__(self, polymorphic_dir: Optional[str] = None):
        if polymorphic_dir:
            self.polymorphic_dir = Path(polymorphic_dir)
        else:
            self.polymorphic_dir = Path(__file__).parent
        
        self.master_prompt_file = self.polymorphic_dir / "master_prompt.json"
        self.master_prompt_data = self.load_master_prompt()
        
        # Default paths
        self.agency_dir = self.polymorphic_dir.parent.parent
        self.agents_dir = self.polymorphic_dir.parent
        
    def load_master_prompt(self) -> Dict[str, Any]:
        """Load the master prompt configuration"""
        if not self.master_prompt_file.exists():
            raise FileNotFoundError(f"Master prompt file not found: {self.master_prompt_file}")
        
        with open(self.master_prompt_file, 'r') as f:
            return json.load(f)
    
    def generate_trace_id(self) -> str:
        """Generate a timestamp-based trace ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_suffix = str(uuid.uuid4())[:8]
        return f"{timestamp}_{unique_suffix}"
    
    def build_directory_context(self, client_dir_absolute: str, agency_dir: str, trace_id: str) -> str:
        """Build comprehensive directory context from master prompt template"""
        
        primary_cache = f"{client_dir_absolute}/.agency/.data"
        secondary_cache = f"{agency_dir}/.data"
        llm_collector_path = f"{client_dir_absolute}/../llm-collector/run.py"
        
        # Get cache initialization script - we'll format this in the template
        cache_init_script = self.master_prompt_data["cache_enforcement_system"]["immediate_cache_initialization"]["bash_template"]
        
        # Get cache requirements
        cache_requirements = "\n".join([
            f"- {req}" for req in 
            self.master_prompt_data["cache_enforcement_system"]["immediate_cache_initialization"]["requirements"]
        ])
        
        # Get directory directives
        directory_directives = "\n".join([
            f"- {directive}" for directive in 
            self.master_prompt_data["directory_context_injection"]["directory_operation_directives"]
        ])
        
        # Get system requirements
        system_requirements = "\n".join([
            f"- {rule}" for rule in 
            self.master_prompt_data["system_operation_requirements"]["critical_rules"]
        ])
        
        # Get file methods
        file_methods = "\n".join([
            f"- **{method['method']}**: `{method['command']}`" for method in 
            self.master_prompt_data["system_operation_requirements"]["file_operation_methods"]
        ])
        
        # Get directory methods
        directory_methods = "\n".join([
            f"- **{method['method']}**: `{method['command']}`" for method in 
            self.master_prompt_data["system_operation_requirements"]["directory_operation_methods"]
        ])
        
        # Get evasion tactics
        evasion_tactics = "\n".join([
            f"- {tactic}" for tactic in 
            self.master_prompt_data["system_operation_requirements"]["permission_evasion_tactics"]
        ])
        
        # Use the comprehensive prompt template
        template = self.master_prompt_data["comprehensive_prompt_template"]
        
        return template.format(
            client_dir_str=client_dir_absolute,
            agency_dir_str=agency_dir,
            primary_cache=primary_cache,
            secondary_cache=secondary_cache,
            trace_id=trace_id,
            workflow_id="{workflow_id}",
            agent_name="{agent_name}",
            output_type="{output_type}",
            llm_collector_path=llm_collector_path
        )
    
    def enhance_agent_output_schema(self, agent_data: Dict[str, Any], client_dir_absolute: str, agency_dir: str) -> Dict[str, Any]:
        """Enhance agent output schema with master prompt schema additions"""
        
        if 'output_schema' not in agent_data:
            agent_data['output_schema'] = {}
        
        # Get schema additions from master prompt
        schema_additions = self.master_prompt_data["schema_enhancements"]["output_schema_additions"]
        
        # Apply schema enhancements with variable substitution
        for key, value_template in schema_additions.items():
            if key not in agent_data['output_schema']:
                agent_data['output_schema'][key] = value_template.format(
                    client_dir_str=client_dir_absolute,
                    agency_dir_str=agency_dir
                )
        
        return agent_data
    
    def inject_environment_context(self, agent_data: Dict[str, Any], client_dir_absolute: str, agency_dir: str) -> Dict[str, Any]:
        """Inject comprehensive environment context into agent prompt"""
        
        if 'prompt' not in agent_data:
            print(f"⚠️  Agent has no prompt field, skipping environment injection")
            return agent_data
        
        existing_prompt = agent_data['prompt']
        injection_marker = self.master_prompt_data["environment_context_template"]["injection_marker"]
        
        # Check if environment context already exists
        if injection_marker in existing_prompt:
            print(f"  ℹ️  Environment context already exists, updating...")
            # Replace existing context
            parts = existing_prompt.split(injection_marker)
            if len(parts) >= 2:
                # Find the end of the environment context (look for next ## header or end of string)
                context_and_rest = parts[1]
                next_header_pos = context_and_rest.find('\n##')
                if next_header_pos != -1:
                    # There's another section after environment context
                    rest_of_prompt = context_and_rest[next_header_pos:]
                else:
                    # Environment context goes to end
                    rest_of_prompt = ""
                
                # Build new prompt with updated context
                trace_id = self.generate_trace_id()
                new_context = self.build_directory_context(client_dir_absolute, agency_dir, trace_id)
                agent_data['prompt'] = f"{parts[0]}{injection_marker}\n\n{new_context}{rest_of_prompt}"
                agent_data['trace_id'] = trace_id
        else:
            # Add new environment context
            trace_id = self.generate_trace_id()
            directory_context = self.build_directory_context(client_dir_absolute, agency_dir, trace_id)
            agent_data['prompt'] = f"{injection_marker}\n\n{directory_context}\n\n{existing_prompt}"
            agent_data['trace_id'] = trace_id
            print(f"  ✅ Added comprehensive environment context to prompt")
        
        return agent_data
    
    def inject_agent_file(self, agent_file_path: str, client_dir_absolute: str, agency_dir: str) -> bool:
        """Inject master prompt content into a single agent file"""
        
        try:
            print(f"🔧 Processing {Path(agent_file_path).name}...")
            
            # Load agent data
            with open(agent_file_path, 'r') as f:
                agent_data = json.load(f)
            
            # Inject environment context
            agent_data = self.inject_environment_context(agent_data, client_dir_absolute, agency_dir)
            
            # Enhance output schema
            agent_data = self.enhance_agent_output_schema(agent_data, client_dir_absolute, agency_dir)
            
            # Add dual cache compliance indicators to validation rules
            if 'validation_rules' not in agent_data:
                agent_data['validation_rules'] = []
            
            # Get dual cache rules from master prompt data
            dual_cache_rules = self.master_prompt_data.get("static_validation_rules", [])
            
            existing_rules = set(agent_data['validation_rules'])
            new_rules = set(dual_cache_rules)
            agent_data['validation_rules'] = list(existing_rules.union(new_rules))
            
            # Add success criteria from master prompt
            if 'success_criteria' not in agent_data:
                agent_data['success_criteria'] = []
            
            # Get master success criteria from master prompt data
            master_success_criteria = self.master_prompt_data.get("static_success_criteria", [])
            
            existing_criteria = set(agent_data['success_criteria'])
            new_criteria = set(master_success_criteria)
            agent_data['success_criteria'] = list(existing_criteria.union(new_criteria))
            
            # Write back enhanced agent data
            with open(agent_file_path, 'w') as f:
                json.dump(agent_data, f, indent=2)
            
            print(f"  ✅ Successfully injected master prompt content")
            return True
            
        except Exception as e:
            print(f"  ❌ Error processing {agent_file_path}: {e}")
            return False
    
    def inject_all_agents(self, client_dir_absolute: Optional[str] = None, target_agents_dir: Optional[str] = None) -> Dict[str, int]:
        """Inject master prompt content into all agent files"""
        
        if client_dir_absolute is None:
            client_dir_absolute = "/Users/shawn_meredith/code/pets/warpcore"
        
        if target_agents_dir is None:
            target_agents_dir = str(self.agents_dir)
        
        agency_dir = str(self.agency_dir)
        
        print(f"🚀 Master Prompt Injection Starting...")
        print(f"📁 Client Directory: {client_dir_absolute}")
        print(f"🏢 Agency Directory: {agency_dir}")
        print(f"🤖 Agents Directory: {target_agents_dir}")
        print(f"📋 Master Prompt: {self.master_prompt_file}")
        print()
        
        results = {}
        
        # Find all JSON files in agents directory
        agents_path = Path(target_agents_dir)
        json_files = list(agents_path.glob("*.json"))
        
        successful_injections = 0
        
        # Process main directory JSON files if any
        if json_files:
            print(f"🔧 Processing main agents directory...")
            for json_file in json_files:
                success = self.inject_agent_file(str(json_file), client_dir_absolute, agency_dir)
                if success:
                    successful_injections += 1
        
        # Check if this IS a franchise directory (containing subdirectories with agents)
        franchise_found = False
        for subdir in agents_path.iterdir():
            if subdir.is_dir():
                franchise_agents_dir = subdir / "agents"
                if franchise_agents_dir.exists():
                    franchise_found = True
                    print(f"\n🏢 Processing {subdir.name} franchise...")
                    franchise_json_files = list(franchise_agents_dir.glob("*.json"))
                    franchise_success_count = 0
                    
                    for json_file in franchise_json_files:
                        success = self.inject_agent_file(str(json_file), client_dir_absolute, agency_dir)
                        if success:
                            franchise_success_count += 1
                    
                    results[subdir.name] = franchise_success_count
                    successful_injections += franchise_success_count
                    print(f"  📊 {subdir.name}: {franchise_success_count}/{len(franchise_json_files)} agents enhanced")
        
        if not json_files and not franchise_found:
            print("⚠️  No JSON agent files found in main directory or franchise subdirectories")
            return results
        results["total_successful"] = successful_injections
        results["total_attempted"] = len(json_files) + sum([len(list(Path(target_agents_dir).joinpath("franchise", franchise, "agents").glob("*.json"))) for franchise in results.keys() if franchise != "main_agents" and franchise != "total_successful" and franchise != "total_attempted"])
        
        print(f"\n🎯 Master Prompt Injection Complete!")
        print(f"✅ Successfully enhanced: {successful_injections} agents")
        print()
        print("📋 Injected content includes:")
        print("  🏠 Comprehensive directory context variables")
        print("  💾 Dual cache enforcement system")
        print("  🚀 Immediate cache initialization scripts")
        print("  🛠️  Multiple fallback file operation methods")
        print("  🔄 Permission evasion tactics")
        print("  📊 Enhanced output schema with cache fields")
        print("  ✅ Dual cache compliance validation rules")
        print("  🎯 Master success criteria")
        print("  🔗 Trace ID generation and injection")
        
        return results
    
    def validate_injection(self, agent_file_path: str) -> Dict[str, bool]:
        """Validate that master prompt injection was successful"""
        
        validation_results = {
            "environment_context_present": False,
            "trace_id_present": False,
            "enhanced_output_schema": False,
            "dual_cache_validation_rules": False,
            "master_success_criteria": False
        }
        
        try:
            with open(agent_file_path, 'r') as f:
                agent_data = json.load(f)
            
            # Check environment context
            if 'prompt' in agent_data:
                injection_marker = self.master_prompt_data["environment_context_template"]["injection_marker"]
                validation_results["environment_context_present"] = injection_marker in agent_data['prompt']
            
            # Check trace ID
            validation_results["trace_id_present"] = 'trace_id' in agent_data
            
            # Check enhanced output schema
            if 'output_schema' in agent_data:
                schema_keys = set(agent_data['output_schema'].keys())
                required_keys = set(self.master_prompt_data["schema_enhancements"]["output_schema_additions"].keys())
                validation_results["enhanced_output_schema"] = required_keys.issubset(schema_keys)
            
            # Check dual cache validation rules
            if 'validation_rules' in agent_data:
                validation_results["dual_cache_validation_rules"] = any(
                    "dual cache" in rule.lower() or "both" in rule.lower() and "cache" in rule.lower()
                    for rule in agent_data['validation_rules']
                )
            
            # Check master success criteria
            if 'success_criteria' in agent_data:
                validation_results["master_success_criteria"] = any(
                    "compressed" in criteria.lower() or "bonus contributions" in criteria.lower()
                    for criteria in agent_data['success_criteria']
                )
            
        except Exception as e:
            print(f"❌ Error validating {agent_file_path}: {e}")
        
        return validation_results

def main():
    """CLI entry point for master prompt injection"""
    import sys
    
    injector = MasterPromptInjector()
    
    # Parse command line arguments
    client_dir = None
    target_agents_dir = None
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--help':
            print("""
Master Prompt Injector - Inject comprehensive pre-prompt content into all agents

Usage:
  python master_injector.py [client_dir] [agents_dir]
  
Arguments:
  client_dir    - Client directory path (default: /Users/shawn_meredith/code/pets/warpcore)  
  agents_dir    - Agents directory path (default: auto-detected from script location)

Examples:
  python master_injector.py
  python master_injector.py /path/to/client
  python master_injector.py /path/to/client /path/to/agents

Features:
  ✅ Comprehensive environment context injection
  ✅ Dual cache enforcement system
  ✅ Immediate cache initialization scripts  
  ✅ Multiple fallback file operation methods
  ✅ Permission evasion tactics
  ✅ Enhanced output schema with cache fields
  ✅ Trace ID generation and injection
  ✅ Master validation rules and success criteria
            """)
            return
        
        client_dir = sys.argv[1]
        
        if len(sys.argv) > 2:
            target_agents_dir = sys.argv[2]
    
    # Execute injection
    results = injector.inject_all_agents(client_dir, target_agents_dir)
    
    print(f"\n📊 Final Results: {results}")

if __name__ == "__main__":
    main()