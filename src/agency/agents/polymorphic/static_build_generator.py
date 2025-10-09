#!/usr/bin/env python3
"""
Static Build Generator for Agent Schemas
Merges master_prompt.json into all franchise agents at build time to create self-contained static JSONs
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import uuid

from master_injector import MasterPromptInjector
from polymorphic_schema_engine import AgentSchemaFactory

class StaticBuildGenerator:
    """Generates static, fully-merged agent JSONs at build time"""
    
    def __init__(self, polymorphic_dir: str = None):
        if polymorphic_dir:
            self.polymorphic_dir = Path(polymorphic_dir)
        else:
            self.polymorphic_dir = Path(__file__).parent
        
        self.master_injector = MasterPromptInjector(str(self.polymorphic_dir))
        self.agents_dir = self.polymorphic_dir.parent
        
        # No separate build output - we replace originals in-place
        
    def generate_trace_id(self) -> str:
        """Generate a build-time trace ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_suffix = str(uuid.uuid4())[:8]
        return f"BUILD_{timestamp}_{unique_suffix}"
    
    def merge_master_prompt_static(self, agent_data: Dict[str, Any], client_dir: str, agency_dir: str) -> Dict[str, Any]:
        """Merge master prompt data statically into agent JSON"""
        
        # Start with a copy
        merged_agent = agent_data.copy()
        
        # Generate build-time trace ID
        build_trace_id = self.generate_trace_id()
        merged_agent['build_trace_id'] = build_trace_id
        merged_agent['build_timestamp'] = datetime.now().isoformat()
        
        # Inject comprehensive environment context as static data
        environment_context = self.master_injector.build_directory_context(
            client_dir, agency_dir, build_trace_id
        )
        
        # Prepend master prompt content to existing prompt
        if 'prompt' in merged_agent:
            injection_marker = self.master_injector.master_prompt_data["environment_context_template"]["injection_marker"]
            existing_prompt = merged_agent['prompt']
            
            # Remove any existing environment context to avoid duplication
            if injection_marker in existing_prompt:
                parts = existing_prompt.split(injection_marker)
                if len(parts) >= 2:
                    # Find next section or end
                    context_and_rest = parts[1]
                    next_header_pos = context_and_rest.find('\n##')
                    if next_header_pos != -1:
                        remaining_prompt = context_and_rest[next_header_pos:]
                    else:
                        remaining_prompt = ""
                    existing_prompt = parts[0] + remaining_prompt
            
            # Inject new comprehensive context
            merged_agent['prompt'] = f"{injection_marker}\n\n{environment_context}\n\n{existing_prompt}"
        
        # Enhance output schema with master prompt additions
        if 'output_schema' not in merged_agent:
            merged_agent['output_schema'] = {}
            
        schema_additions = self.master_injector.master_prompt_data["schema_enhancements"]["output_schema_additions"]
        for key, value_template in schema_additions.items():
            if key not in merged_agent['output_schema']:
                merged_agent['output_schema'][key] = value_template.format(
                    client_dir_str=client_dir,
                    agency_dir_str=agency_dir
                )
        
        # Add comprehensive caching system info to output schema
        caching_system = self.master_injector.master_prompt_data["cache_enforcement_system"].get("comprehensive_caching_system", {})
        if caching_system:
            merged_agent['output_schema']['comprehensive_caching_info'] = caching_system
        
        # Merge validation rules
        if 'validation_rules' not in merged_agent:
            merged_agent['validation_rules'] = []
            
        static_rules = self.master_injector.master_prompt_data.get("static_validation_rules", [])
        existing_rules = set(merged_agent['validation_rules'])
        new_rules = set(static_rules)
        merged_agent['validation_rules'] = list(existing_rules.union(new_rules))
        
        # Merge success criteria  
        if 'success_criteria' not in merged_agent:
            merged_agent['success_criteria'] = []
            
        static_criteria = self.master_injector.master_prompt_data.get("static_success_criteria", [])
        existing_criteria = set(merged_agent['success_criteria'])
        new_criteria = set(static_criteria)
        merged_agent['success_criteria'] = list(existing_criteria.union(new_criteria))
        
        # Apply polymorphic schema enhancements if agent_id is known
        if 'agent_id' in merged_agent:
            try:
                agent_schema = AgentSchemaFactory.create_agent_schema(
                    merged_agent['agent_id'], 
                    merged_agent.get('agent_version', '1.0.0')
                )
                
                # Apply polymorphic schema to output schema
                polymorphic_schema = agent_schema.build_output_schema()
                for key, value in polymorphic_schema.items():
                    if key not in merged_agent['output_schema']:
                        merged_agent['output_schema'][key] = value
                
                # Apply polymorphic validation rules
                polymorphic_rules = agent_schema.build_validation_rules()
                existing_rules = set(merged_agent['validation_rules'])
                new_rules = set(polymorphic_rules)
                merged_agent['validation_rules'] = list(existing_rules.union(new_rules))
                
                # Apply polymorphic success criteria
                polymorphic_criteria = agent_schema.build_success_criteria()
                existing_criteria = set(merged_agent['success_criteria'])
                new_criteria = set(polymorphic_criteria)
                merged_agent['success_criteria'] = list(existing_criteria.union(new_criteria))
                
                print(f"  🔧 Applied polymorphic schema for agent: {merged_agent['agent_id']}")
                
            except Exception as e:
                print(f"  ⚠️ Could not apply polymorphic schema: {e}")
        
        # Mark as statically built
        merged_agent['static_build_info'] = {
            "build_timestamp": datetime.now().isoformat(),
            "build_trace_id": build_trace_id,
            "master_prompt_version": self.master_injector.master_prompt_data["master_prompt_system"]["version"],
            "build_type": "STATIC_MERGED",
            "polymorphic_enhanced": True,
            "self_contained": True
        }
        
        return merged_agent
    
    def build_franchise_agents(self, franchise_name: str, client_dir: str = None, agency_dir: str = None) -> Dict[str, bool]:
        """Build static agents for a specific franchise"""
        
        if client_dir is None:
            client_dir = "/Users/shawn_meredith/code/pets/warpcore"
        if agency_dir is None:
            agency_dir = str(self.polymorphic_dir.parent.parent)
        
        results = {}
        
        franchise_dir = self.agents_dir / "franchise" / franchise_name
        if not franchise_dir.exists():
            print(f"❌ Franchise not found: {franchise_name}")
            return results
        
        agents_dir = franchise_dir / "agents"
        if not agents_dir.exists():
            print(f"❌ Agents directory not found for franchise: {franchise_name}")
            return results
        
        # Create .source directory for clean original templates
        source_dir = agents_dir / ".source"
        source_dir.mkdir(exist_ok=True)
        
        print(f"🏢 Building static agents for {franchise_name} franchise...")
        
        # Determine if this is first build or rebuild
        source_files = list(source_dir.glob("*.json"))
        is_rebuild = len(source_files) > 0
        
        if is_rebuild:
            print(f"  🔄 Rebuilding from clean sources in: {source_dir}")
            json_files = source_files
            build_source_dir = source_dir
        else:
            print(f"  🆆 First build - saving originals to: {source_dir}")
            json_files = list(agents_dir.glob("*.json"))
            build_source_dir = agents_dir
        
        for json_file in json_files:
            try:
                print(f"  🔧 Processing {json_file.name}...")
                
                # For first build, backup original to .source
                if not is_rebuild:
                    source_file = source_dir / json_file.name
                    import shutil
                    shutil.copy2(json_file, source_file)
                    print(f"    💾 Saved clean original to: {source_file}")
                
                # Load agent (from .source if rebuild, from agents/ if first build)
                with open(json_file, 'r') as f:
                    original_agent = json.load(f)
                
                # Merge with master prompt and polymorphic schema
                static_agent = self.merge_master_prompt_static(original_agent, client_dir, agency_dir)
                
                # Write built version to flat agents directory
                output_file = agents_dir / json_file.name
                with open(output_file, 'w') as f:
                    json.dump(static_agent, f, indent=2)
                
                results[json_file.name] = True
                print(f"    ✅ Built static agent: {output_file}")
                
            except Exception as e:
                print(f"    ❌ Error building {json_file.name}: {e}")
                results[json_file.name] = False
        
        return results
    
    def build_all_franchises(self, client_dir: str = None, agency_dir: str = None) -> Dict[str, Dict[str, bool]]:
        """Build static agents for all franchises"""
        
        if client_dir is None:
            client_dir = "/Users/shawn_meredith/code/pets/warpcore" 
        if agency_dir is None:
            agency_dir = str(self.polymorphic_dir.parent.parent)
        
        print(f"🚀 STATIC BUILD GENERATOR STARTING...")
        print(f"📁 Client Directory: {client_dir}")
        print(f"🏢 Agency Directory: {agency_dir}")
        print(f"📋 Master Prompt: {self.master_injector.master_prompt_file}")
        print(f"📦 Building in-place with .source backup")
        print()
        
        franchise_results = {}
        
        franchise_root = self.agents_dir / "franchise"
        if not franchise_root.exists():
            print("❌ No franchise directory found")
            return franchise_results
        
        for franchise_path in franchise_root.iterdir():
            if franchise_path.is_dir():
                franchise_results[franchise_path.name] = self.build_franchise_agents(
                    franchise_path.name, client_dir, agency_dir
                )
        
        # Summary
        total_agents = sum(len(results) for results in franchise_results.values())
        successful_agents = sum(sum(results.values()) for results in franchise_results.values())
        
        print(f"\n🎯 STATIC BUILD COMPLETE!")
        print(f"✅ Successfully built: {successful_agents}/{total_agents} agents")
        print(f"📦 Static agents saved to franchise agents directories")
        print(f"💾 Clean originals preserved in .source/ directories")
        print()
        print("📋 Built agents are fully self-contained with:")
        print("  🔧 Master prompt environment context")
        print("  💾 Comprehensive caching system")
        print("  🏗️ Polymorphic schema enhancements")
        print("  📊 Static validation rules and success criteria")
        print("  ⚡ No runtime dependencies on master_prompt.json")
        print("  📁 Same file locations - everything else keeps working!")
        
        return franchise_results
    
    def restore_from_source(self, franchise_name: str = None):
        """Restore agents from clean .source templates"""
        if franchise_name:
            franchise_dir = self.agents_dir / "franchise" / franchise_name
            agents_dir = franchise_dir / "agents"
            source_dir = agents_dir / ".source"
            
            if source_dir.exists():
                import shutil
                for source_file in source_dir.glob("*.json"):
                    original_file = agents_dir / source_file.name
                    shutil.copy2(source_file, original_file)
                    print(f"🔄 Restored {original_file} from clean source")
                print(f"✅ Restored {franchise_name} franchise from clean source templates")
            else:
                print(f"❌ No .source directory found for {franchise_name} franchise")
        else:
            print("Please specify a franchise name to restore")

def main():
    """CLI entry point for static build generation"""
    import sys
    
    builder = StaticBuildGenerator()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--help':
            print("""
Static Build Generator - Create self-contained agent JSONs

Usage:
  python static_build_generator.py [command] [options]

Commands:
  build-all        Build all franchise agents (default)
  build <name>     Build specific franchise
  restore <name>   Restore franchise from clean source templates

Options:
  --client-dir <path>    Client directory path
  --agency-dir <path>    Agency directory path

Examples:
  python static_build_generator.py
  python static_build_generator.py build patrol
  python static_build_generator.py restore patrol
  python static_build_generator.py build-all --client-dir /custom/path

Output:
  Static agents replace originals in franchise directories
  Clean originals preserved in .source/ subdirectories
  Rebuilds use clean .source templates, not modified agents
  Built agents are fully self-contained and don't need master_prompt.json at runtime
            """)
            return
        
        if sys.argv[1] == 'restore' and len(sys.argv) > 2:
            franchise_name = sys.argv[2]
            builder.restore_from_source(franchise_name)
            return
        
        if sys.argv[1].startswith('build'):
            if sys.argv[1] == 'build' and len(sys.argv) > 2:
                # Build specific franchise
                franchise_name = sys.argv[2]
                results = builder.build_franchise_agents(franchise_name)
                print(f"\n📊 Results for {franchise_name}: {results}")
            else:
                # Build all franchises
                results = builder.build_all_franchises()
                print(f"\n📊 Final Results: {results}")
            return
    
    # Default: build all
    results = builder.build_all_franchises()
    print(f"\n📊 Final Results: {results}")

if __name__ == "__main__":
    main()