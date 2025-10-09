#!/usr/bin/env python3
"""
Agency Composition
Main orchestrator using modular utility classes
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
from .agent_discovery import AgentDiscovery
from .workflow_manager import WorkflowManager
from .agent_executor import AgentExecutor
from .cache_manager import CacheManager

class WARPCOREAgencyComposition:
    """Composed agency system using utility classes"""
    
    def __init__(self, client_dir_absolute: Optional[str] = None, franchise: str = "staff"):
        # Store franchise
        self.franchise = franchise
        
        # Agency system always stays in its location for caching/data
        self.base_path = Path(__file__).parent.parent  # Agency system location
        
        # Client directory is where analysis happens
        if client_dir_absolute:
            self.client_dir_absolute = Path(client_dir_absolute).resolve()
            print(f"🎯 Client Directory (Analysis Target): {self.client_dir_absolute}")
        else:
            self.client_dir_absolute = self.base_path.parent  # Default to warpcore root
        
        # Initialize utility components with franchise awareness
        self.agent_discovery = AgentDiscovery(self.base_path, franchise)
        self.workflow_manager = WorkflowManager(self.base_path, self.client_dir_absolute)
        
        # Cache management - DUAL CACHE ENFORCEMENT with franchise isolation
        self.primary_cache = self.client_dir_absolute.parent / ".data"
        self.secondary_cache = self.base_path / ".data"
        self.cache_manager = CacheManager(self.primary_cache, self.secondary_cache, franchise)
        
        # Agent executor with franchise support
        self.agent_executor = AgentExecutor(self.base_path, self.client_dir_absolute, self.agent_discovery)
        
        self.show_configuration()
    
    def show_configuration(self):
        """Display current agency configuration"""
        print("🚀 WARPCORE Agency System Initialized")
        print(f"🏢 Franchise: {self.franchise.title()}")
        print(f"📁 Agency System: {self.base_path}")
        print(f"🎯 Analysis Target: {self.client_dir_absolute}")
        print(f"🗂️  Primary Cache: {self.primary_cache}/franchise/{self.franchise}/")
        print(f"🗂️  Secondary Cache: {self.secondary_cache}/franchise/{self.franchise}/")
        
        if self.client_dir_absolute != self.base_path.parent:
            print(f"🔄 Custom client directory specified")
        
        # Show discovered agents count
        agents = self.agent_discovery.list_all_agents()
        print(f"🤖 Discovered {len(agents)} {self.franchise} agents: {', '.join(agents)}")
    
    # Delegate to utility classes
    def get_agent_aliases(self) -> Dict[str, str]:
        """Get agent aliases from discovery system"""
        return self.agent_discovery.get_agent_aliases()
    
    def get_file_to_alias_mapping(self) -> Dict[str, str]:
        """Get file-to-alias mapping from discovery system"""
        return self.agent_discovery.get_file_to_alias_mapping()
    
    def get_agent_descriptions(self) -> Dict[str, str]:
        """Get agent descriptions from discovery system"""
        return self.agent_discovery.get_agent_descriptions()
    
    def list_available_agents(self) -> List[str]:
        """List all available agents"""
        return self.agent_discovery.list_all_agents()
    
    def list_available_workflows(self) -> Dict[str, str]:
        """List available workflows"""
        return self.workflow_manager.list_available_workflows()
    
    def generate_workflow_id(self) -> str:
        """Generate workflow ID"""
        return self.workflow_manager.generate_workflow_id()
    
    def generate_trace_id(self) -> str:
        """Generate trace ID"""
        return self.workflow_manager.generate_trace_id()
    
    def execute_individual_agent(self, agent_alias: str, workflow_id: Optional[str] = None, 
                                user_input_or_spec: Optional[str] = None, 
                                user_input: Optional[Dict] = None) -> bool:
        """Execute individual agent"""
        return self.agent_executor.execute_individual_agent(agent_alias, workflow_id, user_input_or_spec, user_input)
    
    def render_agent_prompt(self, agent_alias: str, workflow_id: Optional[str] = None, 
                           user_input_or_spec: Optional[str] = None) -> bool:
        """Render agent prompt"""
        return self.agent_executor.render_agent_prompt(agent_alias, workflow_id, user_input_or_spec)
    
    def show_agent_help(self) -> None:
        """Show agent help"""
        return self.agent_executor.show_agent_help()
    
    def prompt_workflow_selection(self) -> str:
        """Prompt for workflow selection"""
        return self.workflow_manager.prompt_workflow_selection()
    
    def gap_analysis_workflow(self, user_input: Optional[Dict] = None) -> bool:
        """Execute gap analysis workflow"""
        return self.workflow_manager.gap_analysis_workflow(str(self.client_dir_absolute), user_input)
    
    def custom_workflow(self, agent_chain: List[str]) -> bool:
        """Execute custom workflow"""
        # Validate agent chain first
        valid, errors = self.agent_discovery.validate_agent_chain(agent_chain)
        if not valid:
            for error in errors:
                print(f"❌ {error}")
            return False
        
        return self.workflow_manager.custom_workflow(agent_chain)
    
    def execute_workflow_specification(self, workflow_spec_filename: str) -> bool:
        """Execute workflow from specification"""
        return self.workflow_manager.execute_workflow_specification(workflow_spec_filename, str(self.client_dir_absolute))
    
    def enforce_dual_cache_write(self, workflow_id: str, trace_id: str, agent_name: str, output_data: Dict[str, Any]) -> bool:
        """Enforce dual cache write"""
        return self.cache_manager.enforce_dual_cache_write(workflow_id, trace_id, agent_name, output_data)
    
    def get_shared_asset_directive(self) -> str:
        """Get shared asset directive"""
        return self.cache_manager.get_shared_asset_directive()
    
    def inject_asset_directive_into_prompt(self, agent_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Inject asset directive into prompt"""
        return self.cache_manager.inject_asset_directive_into_prompt(agent_spec)
    
    def validate_agent_asset_compliance(self, workflow_id: str, agent_name: str, trace_id: str) -> Dict[str, bool]:
        """Validate asset compliance"""
        return self.cache_manager.validate_agent_asset_compliance(workflow_id, agent_name, trace_id)
    
    def test_asset_directive_injection(self, agent_name: str = 'pathfinder') -> bool:
        """Test asset directive injection"""
        print(f"\n🧪 Testing asset directive injection with {agent_name} agent...")
        
        # Load agent info
        agent_info = self.agent_discovery.get_agent_info(agent_name)
        if not agent_info:
            print(f"❌ Could not load agent: {agent_name}")
            return False
        
        # Check original prompt length
        original_spec = agent_info['agent_data']
        original_prompt = original_spec.get('prompt', '')
        original_length = len(original_prompt)
        print(f"📏 Original prompt length: {original_length:,} characters")
        
        # Inject asset directive
        enhanced_spec = self.cache_manager.inject_asset_directive_into_prompt(original_spec)
        enhanced_prompt = enhanced_spec.get('prompt', '')
        enhanced_length = len(enhanced_prompt)
        
        print(f"📏 Enhanced prompt length: {enhanced_length:,} characters")
        print(f"➕ Added: {enhanced_length - original_length:,} characters")
        
        # Check that asset directive is present
        directive_indicators = [
            '🗂️ SHARED ASSET MANAGEMENT DIRECTIVE',
            'DUAL CACHE ASSET STORAGE REQUIREMENT',
            'PYTHON SUBPROCESS - EVADES CONSTRAINTS',
            'cleanup_agent_cruft',
            'dual_cache_write'
        ]
        
        found_indicators = []
        for indicator in directive_indicators:
            if indicator in enhanced_prompt:
                found_indicators.append(indicator)
        
        print(f"\n✅ Found {len(found_indicators)}/{len(directive_indicators)} directive indicators:")
        for indicator in found_indicators:
            print(f"  ✓ {indicator}")
        
        missing_indicators = [i for i in directive_indicators if i not in found_indicators]
        if missing_indicators:
            print(f"\n⚠️  Missing indicators:")
            for indicator in missing_indicators:
                print(f"  ❌ {indicator}")
        
        # Verify original prompt is intact
        if original_prompt in enhanced_prompt:
            print(f"\n✅ Original {agent_name} prompt preserved intact")
        else:
            print(f"\n⚠️  Original {agent_name} prompt may have been altered")
        
        success = len(found_indicators) >= 3  # Most indicators should be present
        
        if success:
            print(f"\n🎉 Asset directive injection test PASSED for {agent_name}!")
        else:
            print(f"\n❌ Asset directive injection test FAILED for {agent_name}")
        
        return success
    
    def refresh_discovery(self):
        """Refresh agent discovery (useful for development)"""
        self.agent_discovery.refresh_discovery()