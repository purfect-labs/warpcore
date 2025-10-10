#!/usr/bin/env python3

import json
import os
import glob
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path

class AgentSchemaBase(ABC):
    """Base schema structure that all agents inherit from"""
    
    # Standard schemas shared by all agents
    DATA_COMPRESSION_SCHEMA = {
        "compressed_past_workflows": "boolean",
        "compression_ratio": "number (0-1)", 
        "archived_workflow_count": "number",
        "storage_saved_mb": "number",
        "compression_method": "gzip|json_minify|archive"
    }
    
    BONUS_CONTRIBUTIONS_SCHEMA = {
        "extra_analysis_performed": "boolean",
        "additional_requirements_discovered": "number",
        "enhanced_validation_checks": "array of strings",
        "proactive_improvements_suggested": "number", 
        "cross_workflow_insights": "array of insight objects",
        "contribution_value_score": "number (0-100)"
    }
    
    BASE_EXECUTION_METRICS = {
        "start_time": "string (ISO_TIMESTAMP)",
        "end_time": "string (ISO_TIMESTAMP)",
        "duration_seconds": "number",
        "memory_usage_mb": "number",
        "cpu_usage_percent": "number"
    }
    
    BASE_VALIDATION_RULES = [
        "workflow_id must be properly validated",
        "data compression must be attempted for storage optimization",
        "bonus contributions must be identified and quantified"
    ]
    
    BASE_SUCCESS_CRITERIA = [
        "Historical workflow data compressed for storage efficiency",
        "Bonus contributions identified and tracked for system improvement"
    ]
    
    def __init__(self, agent_id: str, agent_version: str = "1.0.0"):
        self.agent_id = agent_id
        self.agent_version = agent_version
    
    @abstractmethod
    def get_agent_specific_context(self) -> Dict[str, Any]:
        """Each agent defines its specific context and role"""
        pass
    
    @abstractmethod
    def get_performance_metrics_schema(self) -> Dict[str, Any]:
        """Each agent defines its specific performance metrics"""
        pass
    
    def get_extended_validation_rules(self) -> List[str]:
        """Override to add agent-specific validation rules"""
        return []
    
    def get_extended_success_criteria(self) -> List[str]:
        """Override to add agent-specific success criteria"""
        return []
    
    def build_output_schema(self) -> Dict[str, Any]:
        """Build the complete output schema with polymorphic structure"""
        base_schema = {
            "workflow_id": "string (from context)",
            "client_dir_absolute": "string (CLIENT_ANALYSIS_TARGET)",
            "analysis_target": "string (CLIENT_DIR_TO_ANALYZE)",
            "agency_cache_dir": "string (AGENCY_SYSTEM_LOCATION)",
            "data_write_location": "string (CACHE_DATA_HERE)",
            "work_against": "string (ANALYZE_THIS_DIR)",
            "cache_results_to": "string (WRITE_RESULTS_HERE)",
            "agent_name": self.agent_id,
            "timestamp": "string (ISO_TIMESTAMP)",
            "execution_metrics": self.BASE_EXECUTION_METRICS,
            "performance_metrics": self.get_performance_metrics_schema(),
            "data_compression": self.DATA_COMPRESSION_SCHEMA,
            "bonus_contributions": self.BONUS_CONTRIBUTIONS_SCHEMA
        }
        
        # Add agent-specific schema extensions
        agent_context = self.get_agent_specific_context()
        base_schema.update(agent_context)
        
        return base_schema
    
    def build_validation_rules(self) -> List[str]:
        """Combine base and agent-specific validation rules"""
        return self.BASE_VALIDATION_RULES + self.get_extended_validation_rules()
    
    def build_success_criteria(self) -> List[str]:
        """Combine base and agent-specific success criteria"""
        return self.BASE_SUCCESS_CRITERIA + self.get_extended_success_criteria()


class BootstrapAgentSchema(AgentSchemaBase):
    """Agent 0x - Bootstrap Agent Schema"""
    
    def get_agent_specific_context(self) -> Dict[str, Any]:
        return {
            "bootstrap_mode": "fresh_start|full_steam_continue|emergency_restart",
            "system_health": {
                "warpcore_directory_valid": "boolean",
                "all_agents_discovered": "boolean", 
                "agent_discovery_results": "object",
                "overall_health_status": "HEALTHY|DEGRADED|CRITICAL"
            },
            "agent_0_launch": {
                "orchestrator_config_loaded": "boolean",
                "bootstrap_input_prepared": "boolean",
                "agent_0_execution_success": "boolean"
            }
        }
    
    def get_performance_metrics_schema(self) -> Dict[str, Any]:
        return {
            "output_quality_score": "number (0-100)",
            "efficiency_rating": "EXCELLENT|GOOD|FAIR|POOR",
            "bootstrap_success_rate": "number (0-100)",
            "agent_discovery_accuracy": "number (0-100)",
            "system_readiness_score": "number (0-100)"
        }


class OrchestratorAgentSchema(AgentSchemaBase):
    """Agent 0 - Orchestrator Agent Schema"""
    
    def get_agent_specific_context(self) -> Dict[str, Any]:
        return {
            "orchestration_results": {
                "agents_sequenced": "number",
                "agents_launched": "array of agent_ids", 
                "agents_completed": "array of agent_ids",
                "workflow_status": "IN_PROGRESS|COMPLETED|FAILED"
            },
            "agent_coordination": {
                "current_active_agent": "string",
                "pending_agents": "array of agent_ids",
                "failed_agents": "array of agent_ids"
            }
        }
    
    def get_performance_metrics_schema(self) -> Dict[str, Any]:
        return {
            "output_quality_score": "number (0-100)",
            "efficiency_rating": "EXCELLENT|GOOD|FAIR|POOR",
            "orchestration_success_rate": "number (0-100)",
            "agent_coordination_accuracy": "number (0-100)",
            "workflow_completion_rate": "number (0-100)"
        }


class SchemaReconcilerAgentSchema(AgentSchemaBase):
    """Agent 1 - Schema Reconciler Agent Schema"""
    
    def get_agent_specific_context(self) -> Dict[str, Any]:
        return {
            "analysis_summary": {
                "total_files_analyzed": "number",
                "coherence_issues_found": "number",
                "fake_demo_markers_total": "number",
                "pap_compliance_score": "string (percentage)"
            },
            "detailed_findings": "array of issue objects",
            "pap_layer_compliance": "object with layer breakdown"
        }
    
    def get_performance_metrics_schema(self) -> Dict[str, Any]:
        return {
            "output_quality_score": "number (0-100)",
            "efficiency_rating": "EXCELLENT|GOOD|FAIR|POOR",
            "issues_identified": "number",
            "files_analyzed": "number",
            "compliance_score": "number (0-100)"
        }


class RequirementsGeneratorAgentSchema(AgentSchemaBase):
    """Agent 2 - Requirements Generator Agent Schema"""
    
    def get_agent_specific_context(self) -> Dict[str, Any]:
        return {
            "requirements_summary": {
                "total_requirements": "number (max 30)",
                "critical_count": "number",
                "high_count": "number",
                "medium_count": "number",
                "low_count": "number"
            },
            "implementation_phases": "object with phase breakdown",
            "dependency_graph": "object with dependency mapping"
        }
    
    def get_performance_metrics_schema(self) -> Dict[str, Any]:
        return {
            "output_quality_score": "number (0-100)",
            "efficiency_rating": "EXCELLENT|GOOD|FAIR|POOR",
            "requirements_generated": "number",
            "complexity_score": "number (0-100)",
            "dependency_accuracy": "number (0-100)"
        }


class RequirementsValidatorAgentSchema(AgentSchemaBase):
    """Agent 3 - Requirements Validator Agent Schema"""
    
    def get_agent_specific_context(self) -> Dict[str, Any]:
        return {
            "validation_summary": {
                "requirements_validated": "number",
                "pap_compliant": "number",
                "feasible": "number", 
                "implementation_ready": "number",
                "overall_status": "PASS|NEEDS_REVISION|FAIL"
            },
            "validated_requirements": {
                "approved_for_implementation": "array of requirement objects",
                "requires_revision": "array of requirement objects",
                "rejected": "array of requirement objects"
            }
        }
    
    def get_performance_metrics_schema(self) -> Dict[str, Any]:
        return {
            "output_quality_score": "number (0-100)",
            "efficiency_rating": "EXCELLENT|GOOD|FAIR|POOR",
            "requirements_validated": "number",
            "approval_rate": "number (0-100)",
            "validation_accuracy": "number (0-100)"
        }


class ImplementationAgentSchema(AgentSchemaBase):
    """Agent 4 - Implementation Agent Schema"""
    
    def get_agent_specific_context(self) -> Dict[str, Any]:
        return {
            "implementation_summary": {
                "requirements_implemented": "number",
                "files_modified": "number",
                "tests_executed": "number",
                "tests_passed": "number",
                "acceptance_criteria_met": "number"
            },
            "detailed_implementation_results": "array of implementation objects",
            "git_preparation": {
                "files_staged_for_commit": "array of strings",
                "ready_for_gate_promotion": "boolean"
            }
        }
    
    def get_performance_metrics_schema(self) -> Dict[str, Any]:
        return {
            "output_quality_score": "number (0-100)",
            "efficiency_rating": "EXCELLENT|GOOD|FAIR|POOR",
            "requirements_implemented": "number",
            "implementation_success_rate": "number (0-100)",
            "code_quality_score": "number (0-100)"
        }


class GatePromoteAgentSchema(AgentSchemaBase):
    """Agent 5 - Gate Promote Agent Schema"""
    
    def get_agent_specific_context(self) -> Dict[str, Any]:
        return {
            "cross_agent_validation": "object with validation results",
            "git_operations": {
                "commit_operations": "object",
                "staging_operations": "object"
            },
            "gate_promotion_decision": {
                "overall_validation_score": "string (percentage)",
                "gate_decision": "PASS|CONDITIONAL_PASS|FAIL",
                "workflow_completion_status": "COMPLETE|REPEAT_CYCLE"
            }
        }
    
    def get_performance_metrics_schema(self) -> Dict[str, Any]:
        return {
            "output_quality_score": "number (0-100)",
            "efficiency_rating": "EXCELLENT|GOOD|FAIR|POOR",
            "validation_success_rate": "number (0-100)",
            "gate_decision_accuracy": "number (0-100)",
            "cycle_improvement_score": "number (0-100)"
        }


class UserInputTranslatorAgentSchema(AgentSchemaBase):
    """User Input Translator Agent Schema"""
    
    def get_agent_specific_context(self) -> Dict[str, Any]:
        return {
            "translation_summary": {
                "raw_input_processed": "boolean",
                "structured_requirements_generated": "number",
                "translation_confidence": "number (0-100)",
                "input_complexity_score": "number (0-100)"
            },
            "translation_results": {
                "processed_input": "string",
                "extracted_requirements": "array of requirement objects",
                "validation_status": "VALID|NEEDS_REVIEW|INVALID"
            }
        }
    
    def get_performance_metrics_schema(self) -> Dict[str, Any]:
        return {
            "output_quality_score": "number (0-100)",
            "efficiency_rating": "EXCELLENT|GOOD|FAIR|POOR",
            "translation_accuracy": "number (0-100)",
            "requirements_extracted": "number",
            "processing_success_rate": "number (0-100)"
        }


class AgentSchemaFactory:
    """Factory for creating agent schemas polymorphically"""
    
    AGENT_CLASSES = {
        # Staff franchise (legacy)
        "bootstrap_agent": BootstrapAgentSchema,
        "workflow_orchestrator_agent": OrchestratorAgentSchema,
        "schema_coherence_reconciler_agent": SchemaReconcilerAgentSchema,
        "requirements_generator_agent": RequirementsGeneratorAgentSchema,
        "requirements_validator_agent": RequirementsValidatorAgentSchema,
        "implementation_agent": ImplementationAgentSchema,
        "gate_promote_agent": GatePromoteAgentSchema,
        "user_input_requirements_translator": UserInputTranslatorAgentSchema,
        
        # Framer franchise mappings
        "origin": BootstrapAgentSchema,
        "boss": OrchestratorAgentSchema,
        "pathfinder": SchemaReconcilerAgentSchema,
        "oracle": UserInputTranslatorAgentSchema,
        "architect": RequirementsGeneratorAgentSchema,
        "enforcer": RequirementsValidatorAgentSchema,
        "craftsman": ImplementationAgentSchema,
        "craftbuddy": RequirementsGeneratorAgentSchema,  # Creative enhancer, similar to requirements gen
        "gatekeeper": GatePromoteAgentSchema,
        "ghostwriter": RequirementsGeneratorAgentSchema,  # Content creator, similar functionality
        "alice": RequirementsValidatorAgentSchema,       # Decision maker, validation role
        "flux": ImplementationAgentSchema,               # Output executor, implementation role
        "mama_bear": GatePromoteAgentSchema,             # QA role, similar to gate promotion
        "harmony": SchemaReconcilerAgentSchema,          # Meta-coherence, schema analysis role
        
        # PATROL franchise mappings
        "deep": RequirementsGeneratorAgentSchema,        # Enumeration = requirements gathering
        "cipher": RequirementsValidatorAgentSchema,      # Vuln validation = requirements validation  
        "glitch": ImplementationAgentSchema,             # Exploitation = implementation
        "zero": GatePromoteAgentSchema                   # Mission debrief = gate promotion
    }
    
    @classmethod
    def create_agent_schema(cls, agent_id: str, agent_version: str = "1.0.0") -> AgentSchemaBase:
        """Create appropriate agent schema based on agent_id"""
        agent_class = cls.AGENT_CLASSES.get(agent_id)
        if not agent_class:
            raise ValueError(f"Unknown agent_id: {agent_id}. Available: {list(cls.AGENT_CLASSES.keys())}")
        
        return agent_class(agent_id, agent_version)


def generate_environment_context(target_directory=None):
    """Generate comprehensive environment context for agent prompts"""
    import os
    import platform
    from datetime import datetime
    from pathlib import Path
    
    # Use target_directory if provided, otherwise current working directory
    if target_directory:
        target_path = Path(target_directory).resolve()
        working_dir = str(target_path)
    else:
        working_dir = "/Users/shawn_meredith/code/pets/warpcore"
        target_path = Path(working_dir)
    
    return f"""
## ENVIRONMENT CONTEXT (DO NOT DISCOVER - USE THIS INFO)

**CLIENT_DIR_ABSOLUTE**: {working_dir}
**ANALYSIS_TARGET**: {working_dir}
**AGENCY_CACHE_DIR**: /Users/shawn_meredith/code/pets/warpcore/src/agency
**DATA_WRITE_LOCATION**: /Users/shawn_meredith/code/pets/warpcore/src/agency/.data
**WORK_AGAINST**: {working_dir} (analyze this directory)
**CACHE_RESULTS_TO**: /Users/shawn_meredith/code/pets/warpcore/src/agency/.data (write data back here)

### DIRECTORY OPERATION DIRECTIVES:
- **ANALYZE**: All file operations, code analysis, and discovery work against CLIENT_DIR_ABSOLUTE
- **CACHE**: All output data, results, and cache files written to AGENCY_CACHE_DIR/.data
- **READ INPUT**: Input specifications and workflows from AGENCY_CACHE_DIR/workflows
- **COHERENCE**: Once workflow chain starts, all agents maintain same client_dir_absolute
**Platform**: MacOS (Darwin)
**Shell**: zsh 5.9
**Python**: {platform.python_version()}
**Home**: /Users/shawn_meredith
**Timestamp**: {datetime.now().isoformat()}

### PROJECT STRUCTURE (KNOWN - DO NOT SCAN)
```
/Users/shawn_meredith/code/pets/warpcore/
├── .data/                     # Workflow cache and results
├── .config/                   # Configuration files
├── .workflows/warp/dev/       # Legacy workflow files
├── src/agency/                # Main agency system
│   ├── agents/               # Agent JSON specifications (8 files)
│   ├── systems/              # Schema and system management
│   ├── workflows/            # Workflow specifications
│   ├── web/                  # Web dashboard
│   └── agency.py             # Main orchestrator
├── src/api/                   # PAP architecture implementation
│   ├── controllers/          # Business logic controllers
│   ├── providers/            # Data/service providers
│   ├── orchestrators/        # Workflow orchestrators
│   └── middleware/           # Cross-cutting concerns
├── src/testing/              # Multi-layer testing framework
├── docs/                     # Documentation
├── native/                   # Native desktop applications
├── sales/                    # Sales and marketing site
└── llm-collector/            # LLM collection utility
```

### AVAILABLE TOOLS AND PRIMITIVES
**File Operations**: read_files, write_files, file_glob, find_files
**Execution**: run_command, subprocess, shell scripting
**Git**: Full git repository with version control
**Database**: SQLite available, existing licensing database
**Crypto**: Python cryptography library available
**Config**: Hierarchical config system (.config/warpcore.config)
**Logging**: Background logging to /tmp/ for non-blocking operations
**Web**: Flask/FastAPI servers, web dashboard
**Testing**: Playwright, pytest, multi-layer validation

### EXISTING LICENSING INFRASTRUCTURE
**Routes**: /api/license/* endpoints implemented
**Controllers**: license_controller.py with PAP compliance
**Providers**: license_provider.py with database integration
**Config**: license_config.py with environment loading
**Tests**: Comprehensive licensing test suite
**Native**: Desktop license integration
**Database**: Existing license tables and schemas

### AGENT EXECUTION CONTEXT
**Available Agents**: bootstrap, orchestrator, schema_reconciler, requirements_generator, requirements_validator, implementor, gate_promote, user_input_translator
**Workflow System**: Polymorphic schema system with shared base classes
**Data Management**: Compression, archival, bonus contribution tracking
**Cache Patterns**: {{workflow_id}}_{{agent_name}}_results.json
**Dependencies**: Automatic dependency resolution and chaining

**IMPORTANT**: Use this context - do NOT waste time discovering what you already know!
"""

def update_agent_file_polymorphic(agent_file_path: str, add_environment_context: bool = False):
    """Update agent file using polymorphic schema system and optionally add environment context"""
    print(f"Processing {agent_file_path}...")
    
    try:
        # Load existing agent file
        with open(agent_file_path, 'r') as f:
            agent_data = json.load(f)
        
        agent_id = agent_data.get('agent_id')
        agent_version = agent_data.get('agent_version', '1.0.0')
        
        # Create polymorphic schema
        agent_schema = AgentSchemaFactory.create_agent_schema(agent_id, agent_version)
        
        # Add environment context to prompt if requested
        if add_environment_context and 'prompt' in agent_data:
            env_context = generate_environment_context()
            existing_prompt = agent_data['prompt']
            
            # Check if environment context already exists
            if "## ENVIRONMENT CONTEXT" not in existing_prompt:
                # Prepend environment context to existing prompt
                agent_data['prompt'] = env_context + "\n\n" + existing_prompt
                print(f"  ✅ Added environment context to prompt")
            else:
                print(f"  ℹ️  Environment context already exists in prompt")
        
        # Update output_schema with polymorphic structure
        if 'output_schema' in agent_data:
            # Preserve existing unique fields, but ensure base structure
            existing_schema = agent_data['output_schema']
            new_schema = agent_schema.build_output_schema()
            
            # Merge: preserve existing unique fields, add/update base fields
            for key, value in new_schema.items():
                if key not in existing_schema or key in ['data_compression', 'bonus_contributions']:
                    existing_schema[key] = value
            
            agent_data['output_schema'] = existing_schema
        
        # Update validation rules polymorphically
        if 'validation_rules' in agent_data:
            existing_rules = set(agent_data['validation_rules'])
            new_rules = set(agent_schema.build_validation_rules())
            agent_data['validation_rules'] = list(existing_rules.union(new_rules))
        
        # Update success criteria polymorphically
        if 'success_criteria' in agent_data:
            existing_criteria = set(agent_data['success_criteria'])
            new_criteria = set(agent_schema.build_success_criteria())
            agent_data['success_criteria'] = list(existing_criteria.union(new_criteria))
        
        # Write back to file
        with open(agent_file_path, 'w') as f:
            json.dump(agent_data, f, indent=2)
        
        print(f"✅ Updated {agent_file_path} using polymorphic schema")
        
    except Exception as e:
        print(f"❌ Error updating {agent_file_path}: {e}")


def inject_environment_context_to_all_agents():
    """Inject comprehensive environment context into all agent prompts permanently"""
    # Get current directory and find agent files
    current_dir = os.path.dirname(os.path.abspath(__file__))
    agency_dir = os.path.dirname(current_dir)
    agents_dir = os.path.join(agency_dir, 'agents')
    
    agent_files = [
        os.path.join(agents_dir, 'bootstrap.json'),
        os.path.join(agents_dir, 'orchestrator.json'), 
        os.path.join(agents_dir, 'schema_reconciler.json'),
        os.path.join(agents_dir, 'requirements_generator.json'),
        os.path.join(agents_dir, 'requirements_validator.json'),
        os.path.join(agents_dir, 'implementor.json'),
        os.path.join(agents_dir, 'gate_promote.json'),
        os.path.join(agents_dir, 'user_input_translator.json')
    ]
    
    print("🌍 Injecting environment context into all agent prompts...")
    print("📝 This will permanently update agent JSON files with environment primitives")
    
    updated_count = 0
    for agent_file in agent_files:
        if os.path.exists(agent_file):
            print(f"\n🔧 Processing {os.path.basename(agent_file)}...")
            update_agent_file_polymorphic(agent_file, add_environment_context=True)
            updated_count += 1
        else:
            print(f"⚠️ File not found: {agent_file}")
    
    print(f"\n🎯 Environment Context Injection Complete!")
    print(f"✅ Updated {updated_count}/{len(agent_files)} agent files")
    print("\n📋 Environment context now includes:")
    print("  🏠 Working directory and platform info")
    print("  📁 Complete project structure map")
    print("  🛠️  Available tools and primitives")
    print("  🗄️  Existing licensing infrastructure")
    print("  🤖 Agent execution context and dependencies")
    print("  ⚠️  'DO NOT DISCOVER' instructions to prevent time waste")
    
def main():
    """Update all agent files using polymorphic schema system"""
    import sys
    
    # Check if environment context injection is requested
    if len(sys.argv) > 1 and sys.argv[1] == '--inject-environment':
        inject_environment_context_to_all_agents()
        return
    
    # Get current directory and find agent files
    current_dir = os.path.dirname(os.path.abspath(__file__))
    agency_dir = os.path.dirname(current_dir)
    agents_dir = os.path.join(agency_dir, 'agents')
    
    agent_files = [
        os.path.join(agents_dir, 'bootstrap.json'),
        os.path.join(agents_dir, 'orchestrator.json'), 
        os.path.join(agents_dir, 'schema_reconciler.json'),
        os.path.join(agents_dir, 'requirements_generator.json'),
        os.path.join(agents_dir, 'requirements_validator.json'),
        os.path.join(agents_dir, 'implementor.json'),
        os.path.join(agents_dir, 'gate_promote.json'),
        os.path.join(agents_dir, 'user_input_translator.json')
    ]
    
    print("🎯 Starting polymorphic agent schema update...")
    
    for agent_file in agent_files:
        if os.path.exists(agent_file):
            update_agent_file_polymorphic(agent_file)
        else:
            print(f"⚠️ File not found: {agent_file}")
    
    print("\n🚀 Polymorphic schema system applied to all agents!")
    print("\n📋 Benefits achieved:")
    print("  ✅ Shared base structure across all agents")
    print("  ✅ Agent-specific context preserved and extended")
    print("  ✅ Consistent data compression and bonus tracking")
    print("  ✅ Polymorphic inheritance with override capabilities")
    print("  ✅ Type safety and validation through base class")


if __name__ == "__main__":
    main()