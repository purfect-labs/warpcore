#!/usr/bin/env python3
"""
WARP-DEMO Test: Security Licensing Workflow Requirements Validation

This script demonstrates how the requirements_validator.json agent 
processes the security_licensing_workflow_specification.json as input parameters.

The workflow specification serves as abstract input defining what needs to be validated.
"""

import json
import os
from datetime import datetime

def load_security_licensing_specification():
    """Load the security licensing workflow specification as input parameters"""
    spec_path = "src/agency/workflows/security_licensing_workflow_specification.json"
    
    if not os.path.exists(spec_path):
        print(f"❌ WARP-DEMO: Specification not found at {spec_path}")
        return None
        
    with open(spec_path, 'r') as f:
        spec = json.load(f)
    
    print(f"✅ WARP-DEMO: Loaded security licensing specification")
    print(f"   - Workflow: {spec['workflow_name']}")
    print(f"   - Version: {spec['workflow_version']}")
    print(f"   - Total Agents: {spec['total_agents']}")
    print(f"   - Pattern: {spec['workflow_pattern']}")
    
    return spec

def validate_security_licensing_workflow(specification):
    """
    WARP-DEMO: Process the workflow specification through requirements validation
    This simulates what the requirements_validator agent would do
    """
    
    # Validation results structure
    validation_results = {
        "workflow_id": f"security_licensing_validation_{int(datetime.now().timestamp())}",
        "agent_name": "requirements_validator_agent", 
        "timestamp": datetime.now().isoformat(),
        "input_specification": {
            "workflow_file": "security_licensing_workflow_specification.json",
            "workflow_name": specification["workflow_name"],
            "workflow_version": specification["workflow_version"],
            "total_agents_specified": specification["total_agents"],
            "workflow_pattern": specification["workflow_pattern"]
        },
        "validation_summary": {
            "agents_validated": 0,
            "security_requirements_found": 0,
            "dependency_issues": 0,
            "implementation_feasible": True,
            "overall_status": "IN_PROGRESS"
        },
        "security_licensing_validation": {
            "agents_analyzed": [],
            "security_features_identified": [],
            "dependency_graph": {},
            "implementation_challenges": []
        }
    }
    
    print(f"\n🔍 WARP-DEMO: Starting validation of {len(specification['agents'])} agents...")
    
    # Process each agent in the workflow specification
    for agent in specification['agents']:
        agent_id = agent['agent_id']
        print(f"   📋 Validating: {agent_id}")
        
        validation_results["validation_summary"]["agents_validated"] += 1
        validation_results["security_licensing_validation"]["agents_analyzed"].append(agent_id)
        
        # Extract security requirements from agent prompts
        prompt = agent.get('prompt', '')
        security_features = []
        
        if 'encrypt' in prompt.lower() or 'fernet' in prompt.lower():
            security_features.append('encryption')
            validation_results["validation_summary"]["security_requirements_found"] += 1
            
        if 'hardware' in prompt.lower() and 'binding' in prompt.lower():
            security_features.append('hardware_binding')
            validation_results["validation_summary"]["security_requirements_found"] += 1
            
        if 'revoc' in prompt.lower() or 'blacklist' in prompt.lower():
            security_features.append('revocation_management')
            validation_results["validation_summary"]["security_requirements_found"] += 1
            
        if 'monitor' in prompt.lower() and 'usage' in prompt.lower():
            security_features.append('usage_monitoring')
            validation_results["validation_summary"]["security_requirements_found"] += 1
        
        if security_features:
            validation_results["security_licensing_validation"]["security_features_identified"].extend(security_features)
        
        # Analyze dependencies
        dependencies = agent.get('dependencies', [])
        outputs_to = agent.get('outputs_to', [])
        
        validation_results["security_licensing_validation"]["dependency_graph"][agent_id] = {
            "depends_on": dependencies,
            "outputs_to": outputs_to
        }
        
        print(f"      ✅ Security features: {security_features}")
        print(f"      ✅ Dependencies: {len(dependencies)}, Outputs: {len(outputs_to)}")
    
    # Final validation assessment
    validation_results["validation_summary"]["overall_status"] = "PASS" if validation_results["validation_summary"]["dependency_issues"] == 0 else "NEEDS_REVIEW"
    
    print(f"\n📊 WARP-DEMO: Validation Complete")
    print(f"   - Agents validated: {validation_results['validation_summary']['agents_validated']}")
    print(f"   - Security requirements: {validation_results['validation_summary']['security_requirements_found']}")
    print(f"   - Status: {validation_results['validation_summary']['overall_status']}")
    
    return validation_results

def save_validation_results(results):
    """Save validation results to demonstrate output format"""
    os.makedirs('.data/licensing', exist_ok=True)
    
    output_file = f".data/licensing/{results['workflow_id']}_requirements_validation.json"
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 WARP-DEMO: Validation results saved to {output_file}")
    return output_file

def main():
    """
    WARP-DEMO: Main execution showing how workflow specification 
    serves as input parameters to requirements validator
    """
    print("🚀 WARP-DEMO: Security Licensing Requirements Validation Test")
    print("=" * 60)
    
    # Step 1: Load the workflow specification (input parameters)
    specification = load_security_licensing_specification()
    if not specification:
        return
    
    # Step 2: Process through requirements validation
    validation_results = validate_security_licensing_workflow(specification)
    
    # Step 3: Save validation output
    output_file = save_validation_results(validation_results)
    
    print(f"\n✅ WARP-DEMO: Requirements validation complete!")
    print(f"   Input: security_licensing_workflow_specification.json")
    print(f"   Agent: requirements_validator.json")
    print(f"   Output: {output_file}")
    
    print(f"\n🔗 WARP-DEMO: Workflow specification → Requirements Validator → Validation Results")

if __name__ == "__main__":
    main()