#!/usr/bin/env python3
"""
WARPCORE Agency Documentation Builder
Automated build system that watches for agent file changes and regenerates documentation
"""

import os
import sys
import time
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class AgentDocsBuilder(FileSystemEventHandler):
    def __init__(self, agents_dir: str, docs_output: str = None, auto_build: bool = True):
        self.agents_dir = Path(agents_dir)
        self.docs_output = docs_output
        self.auto_build = auto_build
        self.last_build_time = 0
        self.build_cooldown = 2  # seconds to prevent rapid rebuilds
        
        print(f"📁 Watching agents directory: {self.agents_dir}")
        print(f"📄 Output documentation: {self.docs_output or 'default location'}")
        print(f"🔄 Auto-build enabled: {self.auto_build}")
    
    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Only react to agent JSON files
        if file_path.suffix == '.json' and file_path.parent == self.agents_dir:
            self.trigger_build(f"Agent file modified: {file_path.name}")
    
    def on_created(self, event):
        """Handle file creation events"""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Only react to agent JSON files
        if file_path.suffix == '.json' and file_path.parent == self.agents_dir:
            self.trigger_build(f"Agent file created: {file_path.name}")
    
    def on_deleted(self, event):
        """Handle file deletion events"""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Only react to agent JSON files
        if file_path.suffix == '.json' and file_path.parent == self.agents_dir:
            self.trigger_build(f"Agent file deleted: {file_path.name}")
    
    def trigger_build(self, reason: str):
        """Trigger documentation build with cooldown protection"""
        current_time = time.time()
        
        if current_time - self.last_build_time < self.build_cooldown:
            print(f"⏰ Build cooldown active, skipping: {reason}")
            return
        
        self.last_build_time = current_time
        
        if self.auto_build:
            print(f"\n🔄 {reason}")
            print(f"⚡ Triggering automatic documentation rebuild...")
            self.build_documentation()
        else:
            print(f"\n📋 {reason}")
            print(f"💡 Run 'python agency.py docs build' to regenerate documentation")
    
    def build_documentation(self):
        """Build documentation using agency CLI"""
        try:
            print(f"🏗️ Building documentation at {datetime.now().strftime('%H:%M:%S')}...")
            
            # Use the agency CLI to build docs
            agency_path = self.agents_dir.parent / "agency.py"
            
            if not agency_path.exists():
                print(f"❌ Agency CLI not found: {agency_path}")
                return False
            
            # Build command
            cmd = [sys.executable, str(agency_path), "docs", "build", "html"]
            
            print(f"🔧 Running: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.agents_dir.parent)
            )
            
            if result.returncode == 0:
                print("✅ Documentation build successful!")
                if result.stdout:
                    # Print relevant output lines
                    output_lines = result.stdout.strip().split('\n')
                    for line in output_lines:
                        if any(keyword in line for keyword in ['✅', '📄', '🌐', 'file://']):
                            print(f"  {line}")
            else:
                print(f"❌ Documentation build failed (code {result.returncode})")
                if result.stderr:
                    print(f"Error output: {result.stderr}")
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Build error: {e}")
            return False
    
    def manual_build(self):
        """Perform manual build"""
        print("\n🔨 Manual documentation build requested...")
        return self.build_documentation()


def main():
    """Main entry point for documentation builder"""
    parser = argparse.ArgumentParser(
        description="WARPCORE Agency Documentation Builder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build documentation once
  python build_docs.py --build-only

  # Watch for changes and auto-rebuild
  python build_docs.py --watch

  # Watch with custom output location
  python build_docs.py --watch --output /path/to/custom.html

  # Watch without auto-building (notification only)
  python build_docs.py --watch --no-auto-build
        """
    )
    
    parser.add_argument('--agents-dir', '-a', 
                        help='Path to agents directory', 
                        default=None)
    parser.add_argument('--output', '-o',
                        help='Output HTML file path',
                        default=None)
    parser.add_argument('--watch', '-w',
                        action='store_true',
                        help='Watch for file changes and auto-rebuild')
    parser.add_argument('--build-only', '-b',
                        action='store_true',
                        help='Build once and exit')
    parser.add_argument('--no-auto-build',
                        action='store_true',
                        help='Watch for changes but do not auto-build')
    
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
    
    # Create builder
    auto_build = not args.no_auto_build
    builder = AgentDocsBuilder(
        agents_dir=str(agents_dir),
        docs_output=args.output,
        auto_build=auto_build
    )
    
    # Build once if requested
    if args.build_only:
        success = builder.manual_build()
        return 0 if success else 1
    
    # Initial build
    print("🔨 Performing initial documentation build...")
    builder.manual_build()
    
    if args.watch:
        # Set up file system watcher
        observer = Observer()
        observer.schedule(builder, path=str(agents_dir), recursive=False)
        
        print(f"\n👀 Watching for changes in {agents_dir}")
        print("Press Ctrl+C to stop watching...")
        
        observer.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n👋 Stopping documentation watcher...")
            observer.stop()
        
        observer.join()
        print("✅ Documentation watcher stopped")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n👋 Documentation builder interrupted")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)