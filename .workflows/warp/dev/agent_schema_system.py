#!/usr/bin/env python3

import json
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

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


class AgentSchemaFactory:
    """Factory for creating agent schemas polymorphically"""
    
    AGENT_CLASSES = {
        "bootstrap_agent": BootstrapAgentSchema,
        "workflow_orchestrator_agent": OrchestratorAgentSchema,
        "schema_coherence_reconciler_agent": SchemaReconcilerAgentSchema,
        "requirements_generator_agent": RequirementsGeneratorAgentSchema,
        "requirements_validator_agent": RequirementsValidatorAgentSchema,
        "implementation_agent": ImplementationAgentSchema,
        "gate_promote_agent": GatePromoteAgentSchema
    }
    
    @classmethod
    def create_agent_schema(cls, agent_id: str, agent_version: str = "1.0.0") -> AgentSchemaBase:
        """Create appropriate agent schema based on agent_id"""
        agent_class = cls.AGENT_CLASSES.get(agent_id)
        if not agent_class:
            raise ValueError(f"Unknown agent_id: {agent_id}. Available: {list(cls.AGENT_CLASSES.keys())}")
        
        return agent_class(agent_id, agent_version)


def update_agent_file_polymorphic(agent_file_path: str):
    """Update agent file using polymorphic schema system"""
    print(f"Processing {agent_file_path}...")
    
    try:
        # Load existing agent file
        with open(agent_file_path, 'r') as f:
            agent_data = json.load(f)
        
        agent_id = agent_data.get('agent_id')
        agent_version = agent_data.get('agent_version', '1.0.0')
        
        # Create polymorphic schema
        agent_schema = AgentSchemaFactory.create_agent_schema(agent_id, agent_version)
        
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


def main():
    """Update all agent files using polymorphic schema system"""
    agent_files = [
        '.workflows/warp/dev/gap_analysis_agent_0x_bootstrap.json',
        '.workflows/warp/dev/gap_analysis_agent_0_orchestrator.json',
        '.workflows/warp/dev/gap_analysis_agent_1_schema_reconciler.json',
        '.workflows/warp/dev/gap_analysis_agent_2_requirements_generator.json',
        '.workflows/warp/dev/gap_analysis_agent_3_requirements_validator.json',
        '.workflows/warp/dev/gap_analysis_agent_4_implementor.json',
        '.workflows/warp/dev/gap_analysis_agent_5_gate_promote.json'
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