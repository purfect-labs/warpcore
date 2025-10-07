#!/usr/bin/env python3
"""
WARPCORE Security Licensing Workflow Demo
Shows how to execute the full workflow with live streaming
"""

import subprocess
import sys
from pathlib import Path

def main():
    print("🚀 WARPCORE Security Licensing Workflow Demo")
    print("=" * 60)
    
    # Method 1: Direct execution via security licensing executor
    print("\n📋 Method 1: Direct Security Licensing Executor")
    print("Command: python src/agency/security_licensing_executor.py")
    print("Features:")
    print("  ✅ Real-time color-coded output streaming")
    print("  ✅ Live agent execution via Warp CLI")
    print("  ✅ Dependency-based agent chaining")
    print("  ✅ Comprehensive workflow results")
    
    # Method 2: Via main agency system
    print("\n📋 Method 2: Via WARPCORE Agency System")
    print("Command: python src/agency/agency.py 2")
    print("Features:")
    print("  ✅ Integrated with main workflow system")
    print("  ✅ Automatic fallback if Warp not available")
    print("  ✅ Consistent workflow ID generation")
    print("  ✅ Error handling and recovery")
    
    # Method 3: Custom execution with parameters
    print("\n📋 Method 3: Custom Workflow Execution")
    print("Command: python src/agency/agency.py 5")
    print("Select agents: security_licensing_bootstrap security_licensing_orchestrator")
    print("Features:")
    print("  ✅ Interactive agent selection")
    print("  ✅ Custom workflow building")
    print("  ✅ Flexible execution patterns")
    
    print("\n🔗 Live Streaming Features:")
    print("  🎨 Color-coded output per agent")
    print("    • 🟣 Bootstrap Agent (Magenta)")
    print("    • 🔵 Orchestrator Agent (Blue)")  
    print("    • 🟢 License Generator (Green)")
    print("    • 🟡 Security Validator (Yellow)")
    print("    • 🔵 Usage Monitor (Cyan)")
    print("    • 🔴 Revocation Manager (Red)")
    print("    • ⚪ Gate Promote (White)")
    
    print("\n📊 Workflow Execution Chain:")
    print("  1. 🎯 Bootstrap → Environment setup, key generation")
    print("  2. 🎯 Orchestrator → Agent coordination and sequencing")
    print("  3. 🎯 License Generator → Secure key generation system") 
    print("  4. 🎯 Security Validator → Comprehensive security testing")
    print("  5. 🎯 Usage Monitor → Analytics and anomaly detection")
    print("  6. 🎯 Revocation Manager → License revocation system")
    print("  7. 🎯 Gate Promote → Final validation and deployment")
    
    print("\n💾 Output Files Generated:")
    print("  📄 .data/licensing/{workflow_id}_workflow_results.json")
    print("  📄 .data/licensing/{workflow_id}_licensing_bootstrap_results.json")
    print("  📄 .data/licensing/{workflow_id}_licensing_orchestration.json")
    print("  📄 .data/licensing/{workflow_id}_license_generation_results.json")
    print("  📄 .data/licensing/{workflow_id}_security_validation_results.json")
    print("  📄 .data/licensing/{workflow_id}_usage_monitoring_results.json")
    print("  📄 .data/licensing/{workflow_id}_revocation_management_results.json")
    print("  📄 .data/licensing/{workflow_id}_licensing_gate_promotion_results.json")
    
    print("\n🎯 Ready to Execute!")
    print("Choose your execution method:")
    print("1. python src/agency/security_licensing_executor.py")
    print("2. python src/agency/agency.py 2") 
    print("3. python src/agency/agency.py 5 (custom)")
    
    choice = input("\nSelect method (1-3) or 'q' to quit: ").strip()
    
    if choice == '1':
        print("\n🚀 Executing direct security licensing workflow...")
        result = subprocess.run([
            sys.executable, 
            'src/agency/security_licensing_executor.py'
        ])
        return result.returncode
        
    elif choice == '2':
        print("\n🚀 Executing via agency system...")
        result = subprocess.run([
            sys.executable, 
            'src/agency/agency.py', 
            '2'
        ])
        return result.returncode
        
    elif choice == '3':
        print("\n🚀 Executing custom workflow...")
        print("Run: python src/agency/agency.py 5")
        return 0
        
    elif choice.lower() == 'q':
        print("👋 Demo ended")
        return 0
        
    else:
        print("❌ Invalid choice")
        return 1

if __name__ == "__main__":
    sys.exit(main())