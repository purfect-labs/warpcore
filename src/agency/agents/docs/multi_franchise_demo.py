#!/usr/bin/env python3
"""
Demo script showing what multiple franchise flows would look like
"""
import subprocess
import sys
from pathlib import Path

def run_franchise_ascii(franchise_path, franchise_name):
    """Run ASCII flow for a franchise"""
    cmd = [
        sys.executable, 
        "agent_lens.py", 
        franchise_path,
        "--ascii-only",
        "--no-schemas"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)
    return result.stdout

def main():
    print("🎯 MULTI-FRANCHISE AGENT FLOW COMPARISON\n")
    print("=" * 80)
    
    # Define franchises
    franchises = [
        ("/Users/shawn_meredith/code/pets/warpcore/src/agency/agents/franchise/framer/agents", "FRAMER"),
        ("/Users/shawn_meredith/code/pets/warpcore/src/agency/agents/franchise/apex/agents", "APEX"),
        ("/Users/shawn_meredith/code/pets/warpcore/src/agency/agents/franchise/staff/agents", "STAFF")
    ]
    
    for i, (franchise_path, franchise_name) in enumerate(franchises):
        if i > 0:
            print("\n" + "─" * 80 + "\n")
        
        print(f"🏢 FRANCHISE: {franchise_name}")
        print("─" * 40)
        
        try:
            ascii_output = run_franchise_ascii(franchise_path, franchise_name)
            print(ascii_output)
        except Exception as e:
            print(f"❌ Error processing {franchise_name}: {e}")
    
    print("=" * 80)
    print("🌟 Multi-franchise comparison complete!")

if __name__ == "__main__":
    main()