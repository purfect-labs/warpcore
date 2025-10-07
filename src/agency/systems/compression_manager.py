#!/usr/bin/env python3

import json
import os
import sys

# Standard data compression schema to add to all agents
data_compression_schema = {
    "compressed_past_workflows": "boolean",
    "compression_ratio": "number (0-1)", 
    "archived_workflow_count": "number",
    "storage_saved_mb": "number",
    "compression_method": "gzip|json_minify|archive"
}

# Standard bonus contributions schema to add to all agents  
bonus_contributions_schema = {
    "extra_analysis_performed": "boolean",
    "additional_requirements_discovered": "number",
    "enhanced_validation_checks": "array of strings",
    "proactive_improvements_suggested": "number", 
    "cross_workflow_insights": "array of insight objects",
    "contribution_value_score": "number (0-100)"
}

def update_agent_file(agent_file):
    """Add consistent compression and bonus tracking to agent file"""
    print(f"Processing {agent_file}...")
    
    with open(agent_file, 'r') as f:
        agent_data = json.load(f)
    
    # Add to output_schema after performance_metrics
    if 'output_schema' in agent_data:
        output_schema = agent_data['output_schema']
        
        # Add data_compression after performance_metrics
        if 'performance_metrics' in output_schema and 'data_compression' not in output_schema:
            # Insert after performance_metrics
            keys = list(output_schema.keys())
            perf_index = keys.index('performance_metrics')
            
            # Create new ordered dict
            new_schema = {}
            for i, key in enumerate(keys):
                new_schema[key] = output_schema[key]
                if i == perf_index:
                    new_schema['data_compression'] = data_compression_schema
                    new_schema['bonus_contributions'] = bonus_contributions_schema
            
            agent_data['output_schema'] = new_schema
        
        # Update validation rules
        if 'validation_rules' in agent_data:
            agent_data['validation_rules'].extend([
                "data compression must be attempted for storage optimization",
                "bonus contributions must be identified and quantified"
            ])
        
        # Update success criteria  
        if 'success_criteria' in agent_data:
            agent_data['success_criteria'].extend([
                "Historical workflow data compressed for storage efficiency",
                "Bonus contributions identified and tracked for system improvement"
            ])
    
    # Write back to file
    with open(agent_file, 'w') as f:
        json.dump(agent_data, f, indent=2)
    
    print(f"✅ Updated {agent_file}")

def main():
    # Process all agent files except the already updated Agent 3
    agent_files = [
        '.workflows/warp/dev/gap_analysis_agent_0x_bootstrap.json',
        '.workflows/warp/dev/gap_analysis_agent_0_orchestrator.json', 
        '.workflows/warp/dev/gap_analysis_agent_1_schema_reconciler.json',
        '.workflows/warp/dev/gap_analysis_agent_2_requirements_generator.json',
        '.workflows/warp/dev/gap_analysis_agent_4_implementor.json',
        '.workflows/warp/dev/gap_analysis_agent_5_gate_promote.json'
    ]
    
    for agent_file in agent_files:
        if os.path.exists(agent_file):
            try:
                update_agent_file(agent_file)
            except Exception as e:
                print(f"❌ Error updating {agent_file}: {e}")
        else:
            print(f"⚠️ File not found: {agent_file}")
    
    print("\n🎯 All agents updated with consistent compression and bonus tracking!")

if __name__ == "__main__":
    main()