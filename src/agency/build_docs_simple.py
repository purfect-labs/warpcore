#!/usr/bin/env python3
"""
WARPCORE Agency Documentation Builder - Simple Version
Build script that generates documentation without external dependencies
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime


def build_documentation(agents_dir: str, output_file: str = None):
    """Build documentation using agency CLI"""
    try:
        agents_path = Path(agents_dir)
        if not agents_path.exists():
            print(f"❌ Agents directory not found: {agents_path}")
            return False
        
        print(f"🏗️ Building documentation at {datetime.now().strftime('%H:%M:%S')}...")
        print(f"📁 Agents directory: {agents_path}")
        
        # Use the agency CLI to build docs
        agency_path = agents_path.parent / "agency.py"
        
        if not agency_path.exists():
            print(f"❌ Agency CLI not found: {agency_path}")
            return False
        
        # Build command
        cmd = [sys.executable, str(agency_path), "docs", "build", "html"]
        
        print(f"🔧 Running: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=False,  # Show real-time output
            text=True,
            cwd=str(agents_path.parent)
        )
        
        if result.returncode == 0:
            print("\n✅ Documentation build successful!")
        else:
            print(f"\n❌ Documentation build failed (code {result.returncode})")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Build error: {e}")
        return False


def list_agent_files(agents_dir: str):
    """List all agent files in the directory"""
    agents_path = Path(agents_dir)
    
    if not agents_path.exists():
        print(f"❌ Agents directory not found: {agents_path}")
        return
    
    print(f"📁 Agent files in {agents_path}:")
    
    agent_files = sorted([f for f in agents_path.glob("*.json") 
                         if not f.name.startswith('.') and f.name != 'mama_bear.json'])
    
    for i, agent_file in enumerate(agent_files, 1):
        stat = agent_file.stat()
        mod_time = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        size_kb = round(stat.st_size / 1024, 1)
        print(f"  {i:2d}. {agent_file.name:<40} ({size_kb:>5.1f} KB, {mod_time})")
    
    print(f"\nTotal: {len(agent_files)} agent files")


def main():
    """Main entry point for documentation builder"""
    parser = argparse.ArgumentParser(
        description="WARPCORE Agency Documentation Builder - Simple Version",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build documentation
  python build_docs_simple.py

  # Build with custom agents directory
  python build_docs_simple.py --agents-dir /path/to/agents

  # List agent files only
  python build_docs_simple.py --list-only

  # Generate flow diagram only
  python build_docs_simple.py --flow-only
        """
    )
    
    parser.add_argument('--agents-dir', '-a', 
                        help='Path to agents directory', 
                        default=None)
    parser.add_argument('--output', '-o',
                        help='Output HTML file path',
                        default=None)
    parser.add_argument('--list-only', '-l',
                        action='store_true',
                        help='List agent files and exit')
    parser.add_argument('--flow-only', '-f',
                        action='store_true',
                        help='Generate flow diagram only')
    
    args = parser.parse_args()
    
    # Determine agents directory
    if args.agents_dir:
        agents_dir = Path(args.agents_dir)
    else:
        # Default to current script location + agents
        agents_dir = Path(__file__).parent / "agents"
    
    if not agents_dir.exists():
        print(f"❌ Agents directory not found: {agents_dir}")
        return 1
    
    print("🚀 WARPCORE Agency Documentation Builder")
    print("=" * 50)
    
    if args.list_only:
        list_agent_files(str(agents_dir))
        return 0
    
    if args.flow_only:
        print("🎨 Generating flow diagram only...")
        agency_path = agents_dir.parent / "agency.py"
        if not agency_path.exists():
            print(f"❌ Agency CLI not found: {agency_path}")
            return 1
        
        cmd = [sys.executable, str(agency_path), "docs", "flow"]
        result = subprocess.run(cmd, cwd=str(agents_dir.parent))
        return 0 if result.returncode == 0 else 1
    
    # Build documentation
    success = build_documentation(str(agents_dir), args.output)
    return 0 if success else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n👋 Documentation builder interrupted")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)