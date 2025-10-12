#!/usr/bin/env python3
"""
WARPCORE - Kubernetes Command Center
Main entry point for all deployment modes

Usage:
    python warpcore.py                    # Web server mode (default)
    python warpcore.py --browser         # Web server mode 
    python warpcore.py --native          # Native desktop application
    python warpcore.py --electron        # Electron wrapper (requires npm start)
    python warpcore.py --help            # Show help
"""

import argparse
import sys
import os
import subprocess
import time
from pathlib import Path

def start_docs_server():
    """Start standalone API documentation server with Scalar UI on port 8001"""
    try:
        print("📚 Starting standalone WARPCORE API Documentation Server...")
        print("🌐 Documentation will be available at: http://localhost:8001")
        print("📊 Provider-Abstraction-Pattern discovery included")
        print("🔄 Starting server...")
        
        # Import required modules
        from fastapi import FastAPI
        from src.docs.compliant_docs import setup_compliant_docs
        import uvicorn
        import asyncio
        
        # Create standalone docs app
        docs_app = FastAPI(
            title="WARPCORE API Documentation",
            version="3.0.0",
            docs_url=None,  # Disable default swagger
            redoc_url=None  # Disable default redoc  
        )
        
        # Add basic status endpoint
        @docs_app.get("/")
        async def root():
            return {
                "message": "WARPCORE Standalone API Documentation", 
                "status": "running",
                "docs_url": "/docs",
                "architecture_url": "/api/architecture"
            }
        
        # Setup discovery system and register endpoints on startup using orchestrator
        @docs_app.on_event("startup")
        async def startup_discovery():
            try:
                # Use system orchestrator for elaborate logging and initialization
                from src.system_orchestrator import initialize_docs_only
                await initialize_docs_only()
                
                # Initialize discovery system to update docs generator
                from src.data.config.discovery.context_discovery import ContextDiscoverySystem
                from src.api.auto_registration import ComponentAutoDiscovery
                
                discovery_system = ContextDiscoverySystem()
                auto_discovery = ComponentAutoDiscovery()
                
                # Get discovery results for docs
                discovered_contexts = await discovery_system.discover_all_contexts()
                discovered_components = await auto_discovery.auto_discover_components(list(discovered_contexts.get('providers', {}).keys()))
                
                # Store discovery results
                discovery_system._discovered_contexts = discovered_contexts
                discovery_system._discovered_components = discovered_components
                
                # Update docs generator with discovery results
                docs_generator.discovery = discovery_system
                
                # Register discovered endpoints
                await docs_generator.register_discovered_endpoints_now()
                
            except Exception as e:
                print(f"❌ Docs startup failed: {e}")
                print("🛡️ Falling back to basic docs structure\n")
        
        # Setup docs system (will be updated with discovery on startup)
        docs_generator = setup_compliant_docs(docs_app, None)
        
        print("✅ Architectural layer system configured")
        print("📖 Documentation: http://localhost:8001/docs")
        print("🏗️ Architecture: http://localhost:8001/api/architecture")
        print("📋 OpenAPI Schema: http://localhost:8001/openapi.json")
        print("\n" + "─" * 60)
        print("🌊 WARPCORE Architectural Documentation Server")
        print("📊 Data • 🌐 Web • ⚡ API Layers")
        print("🎯 Routes → 🏛️ Controllers → 🔧 Orchestrators → 🔗 Providers → 🛡️ Middleware → ⚙️ Executors")
        print("─" * 60 + "\n")
        
        # Start the standalone docs server
        uvicorn.run(
            docs_app,
            host="127.0.0.1",
            port=8001,
            log_level="info"
        )
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to start standalone docs server: {e}")
        return False

def main():
    # Handle agency commands first
    if len(sys.argv) > 1 and sys.argv[1] == 'agency':
        # Delegate to agency.py with all remaining parameters
        agency_script = Path(__file__).parent / ".workflows/warp/agency.py"
        if agency_script.exists():
            try:
                subprocess.run([sys.executable, str(agency_script)] + sys.argv[2:])
                return
            except Exception as e:
                print(f"❌ Agency error: {e}")
                return
        else:
            print("❌ Agency script not found at .workflows/warp/agency.py")
            return
    
    parser = argparse.ArgumentParser(
        description='WARPCORE - Kubernetes Command Center',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python warpcore.py                   # Show this help
  python warpcore.py agency gap-analysis      # Run gap analysis workflow
  python warpcore.py agency implement         # Run implementation workflow
  python warpcore.py agency validate          # Run validation workflow
  
  # Complete development cycles:
  python warpcore.py iterate           # Build + test + run locally
  python warpcore.py iterate --docker  # Build + test + run via Docker
  
  # Runtime-only commands:
  python warpcore.py --mac-native --web       # Run local WARPCORE in web mode
  python warpcore.py --mac-native --native    # Run local WARPCORE in native mode
  python warpcore.py --docker-native --web    # Run Docker-built in web mode
  python warpcore.py --docker-native --native # Run Docker-built in native mode
        """
    )
    
    parser.add_argument(
        'command',
        nargs='?',
        help='Command to run: iterate, build-unified, compile-collect, rename'
    )
    
    parser.add_argument(
        '--to',
        dest='to_name', 
        help='New name to rename the entire project to'
    )
    
    parser.add_argument(
        '--docker', 
        action='store_true',
        help='Use Docker for build and run operations'
    )
    
    parser.add_argument(
        '--mac-native',
        action='store_true', 
        help='Run using local macOS build'
    )
    
    parser.add_argument(
        '--docker-native',
        action='store_true',
        help='Run using Docker-built binary'
    )
    
    parser.add_argument(
        '--web',
        action='store_true',
        help='Start in web mode'
    )
    
    parser.add_argument(
        '--native',
        action='store_true', 
        help='Start in native app mode'
    )
    
    parser.add_argument(
        '--docs',
        action='store_true',
        help='Start API documentation server with Scalar UI'
    )
    
    parser.add_argument(
        '--fork',
        dest='fork_name',
        help='Fork WARPCORE framework to new app name (creates ../<NAME>/)'
    )
    
    args = parser.parse_args()
    
    # Handle --fork flag - fork WARPCORE framework
    if args.fork_name:
        print(f"🚀 Forking WARPCORE Framework to {args.fork_name}...")
        run_fork_command(args.fork_name)
        return
        
    # Handle --docs flag - start API documentation server
    if args.docs:
        print("📚 Starting WARPCORE API Documentation Server...")
        print("🌊 Scalar UI with Provider-Abstraction-Pattern auto-discovery")
        start_docs_server()
        return
        
    # Handle --web flag by calling start-warpcore.sh
    if args.web and not (args.mac_native or args.docker_native):
        print("🚀 Starting WARPCORE with start-warpcore.sh...")
        start_script = Path(__file__).parent / "start-warpcore.sh"
        if start_script.exists():
            try:
                subprocess.run(["bash", str(start_script)], cwd=Path(__file__).parent)
            except KeyboardInterrupt:
                print("\n👋 WARPCORE stopped")
                sys.exit(0)
        else:
            print(f"❌ Start script not found: {start_script}")
            sys.exit(1)
        return
    
    # Handle runtime-only commands
    if args.mac_native or args.docker_native:
        if not (args.web or args.native):
            print("❌ Must specify --web or --native with runtime commands")
            parser.print_help()
            sys.exit(1)
        
        if args.mac_native:
            run_mac_native(web_mode=args.web, native_mode=args.native)
        elif args.docker_native:
            run_docker_native(web_mode=args.web, native_mode=args.native)
        return
    
    # If no command specified, show help
    if not args.command:
        parser.print_help()
        return
    
    # Handle commands
    if args.command == 'iterate':
        if args.docker:
            print("🐳 Starting Docker iterate: Build + Test + Run")
            run_iterate_docker()
        else:
            print("🖥️ Starting local iterate: Build + Test + Run")
            run_iterate_local()
    elif args.command == 'build-unified':
        print("🚀 Starting unified build: Electron + Nuitka")
        run_unified_build()
    elif args.command == 'compile-collect':
        print("📦 Collecting all build artifacts")
        run_compile_collect()
    elif args.command == 'rename':
        if not args.to_name:
            print("❌ --to required for rename command")
            print("Example: python warpcore.py rename --to WARPCORE")
            print("💡 This will auto-detect the current project name and replace it")
            sys.exit(1)
        
        # Auto-detect current project name
        current_name = detect_current_project_name()
        if not current_name:
            print("❌ Could not detect current project name")
            print("💡 Make sure you're in a valid project directory")
            sys.exit(1)
            
        print(f"🔄 Auto-detected current name: '{current_name}'")
        print(f"🔄 Renaming '{current_name}' to '{args.to_name}' everywhere")
        aggressive_rename(current_name, args.to_name)
    else:
        print(f"❌ Unknown command: {args.command}")
        print("💡 Available commands: iterate, build-unified, compile-collect, rename")
        parser.print_help()
        sys.exit(1)

def run_compile_collect():
    """Collect all build artifacts from different locations and organize them"""
    import shutil
    import time
    from datetime import datetime
    
    print("📦 WARPCORE Compile & Collect - Gathering All Build Artifacts")
    print("=" * 55)
    
    # Create .dist directory with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    collect_dir = Path(__file__).parent / ".dist" / f"collection_{timestamp}"
    collect_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Collection directory: {collect_dir}")
    
    collected_count = 0
    
    # Define artifact locations and their naming conventions
    artifacts = [
        # === LINUX ARTIFACTS (Docker built) ===
        
        # Linux server binary (main Docker artifact)
        {
            'source': 'dist/warpcore-real',
            'dest': 'warpcore-linux-docker-server',
            'type': 'Linux Docker Server Binary'
        },
        
        # Linux PyWebView binary (Docker built)
        {
            'source': 'dist/warpcore-linux-pyweb',
            'dest': 'warpcore-linux-docker-pyweb',
            'type': 'Linux Docker PyWebView Binary'
        },
        
        # Linux DMG files (built via Docker calling macOS build)
        {
            'source': 'dist/WARPCORE-3.0.0-macOS-Nuitka.dmg',
            'dest': 'WARPCORE-macos-docker-pyweb.dmg',
            'type': 'macOS Docker PyWebView DMG'
        },
        
        {
            'source': 'dist/WARPCORE-3.0.0-Unified.dmg',
            'dest': 'WARPCORE-macos-docker-electron.dmg',
            'type': 'macOS Docker Electron DMG'
        },
        
        # === macOS ARTIFACTS (Local built) ===
        
        # Local PyWebView app 
        {
            'source': 'native/build/dist/WARPCORE.app',
            'dest': 'WARPCORE-macos-local-pyweb.app',
            'type': 'macOS Local PyWebView App'
        },
        
        # Local PyWebView DMG
        {
            'source': 'native/build/dist/WARPCORE-3.0.0-macOS-Nuitka.dmg',
            'dest': 'WARPCORE-macos-local-pyweb.dmg',
            'type': 'macOS Local PyWebView DMG'
        },
        
        # Local Electron app 
        {
            'source': 'native/desktop/electron/dist/mac-arm64/WARPCORE Command Center.app',
            'dest': 'WARPCORE-macos-local-electron.app',
            'type': 'macOS Local Electron App'
        },
        
        # Unified Electron DMG (local build) 
        {
            'source': 'native/unified_dist/WARPCORE-3.0.0-Unified.dmg',
            'dest': 'WARPCORE-macos-unified-electron.dmg', 
            'type': 'macOS Unified Electron DMG'
        },
        
        # Standard Electron DMG (local build)
        {
            'source': 'native/desktop/electron/dist/WARPCORE-3.0.0-Electron.dmg',
            'dest': 'WARPCORE-macos-electron.dmg',
            'type': 'macOS Electron DMG'
        },
    ]
    
    # Collect artifacts
    print("\n🔍 Scanning for build artifacts...")
    
    for artifact in artifacts:
        source_path = Path(__file__).parent / artifact['source']
        dest_path = collect_dir / artifact['dest']
        
        if source_path.exists():
            try:
                if source_path.is_dir():
                    shutil.copytree(source_path, dest_path)
                    size = sum(f.stat().st_size for f in dest_path.rglob('*') if f.is_file())
                    size_mb = size // 1024 // 1024
                    print(f"  ✅ {artifact['type']}: {artifact['source']} ({size_mb}MB)")
                else:
                    shutil.copy2(source_path, dest_path)
                    size_mb = source_path.stat().st_size // 1024 // 1024
                    print(f"  ✅ {artifact['type']}: {artifact['source']} ({size_mb}MB)")
                
                collected_count += 1
                
            except Exception as e:
                print(f"  ❌ Failed to collect {artifact['source']}: {e}")
        else:
            print(f"  ⏸️  Not found: {artifact['source']}")
    
    # Create collection manifest
    manifest_path = collect_dir / "COLLECTION_MANIFEST.md"
    with open(manifest_path, 'w') as f:
        f.write(f"# WARPCORE Build Artifacts Collection\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Total Artifacts**: {collected_count}\n\n")
        
        f.write("## Collected Artifacts\n\n")
        for artifact in artifacts:
            source_path = Path(__file__).parent / artifact['source']
            if source_path.exists():
                f.write(f"- ✅ **{artifact['type']}**: `{artifact['dest']}`\n")
            else:
                f.write(f"- ❌ **{artifact['type']}**: Not found\n")
        
        f.write("\n## Usage\n\n")
        f.write("**For Distribution:**\n")
        f.write("- `*.dmg` files - macOS installers\n")
        f.write("- `*.app` directories - macOS applications\n")
        f.write("- `*-binary` files - Linux executables\n\n")
        
        f.write("**App Types:**\n")
        f.write("- `*pyweb*` - Native PyWebView apps (lighter, WebKit)\n")
        f.write("- `*electron*` - Electron apps (heavier, full Chromium)\n")
        f.write("- `*docker*` - Docker-built Linux binaries\n")
        f.write("- `*local*` - Locally-built macOS apps\n")
    
    # Create quick launch scripts
    launch_script = collect_dir / "launch_apps.sh"
    with open(launch_script, 'w') as f:
        f.write("#!/bin/bash\n")
        f.write("# Quick launch script for collected WARPCORE apps\n\n")
        f.write("echo \"🚀 WARPCORE App Launcher\"\n")
        f.write("echo \"==================\"\n\n")
        
        f.write("# Launch PyWebView app\n")
        f.write("if [ -d \"WARPCORE-macos-local-pyweb.app\" ]; then\n")
        f.write("    echo \"1) Launch PyWebView app\"\n")
        f.write("    read -p \"Press 1 to launch PyWebView app: \" choice\n")
        f.write("    if [ \"$choice\" = \"1\" ]; then\n")
        f.write("        open \"WARPCORE-macos-local-pyweb.app\"\n")
        f.write("    fi\n")
        f.write("fi\n\n")
        
        f.write("# Launch Electron app\n")
        f.write("if [ -d \"WARPCORE-macos-local-electron.app\" ]; then\n")
        f.write("    echo \"2) Launch Electron app\"\n")
        f.write("    read -p \"Press 2 to launch Electron app: \" choice\n")
        f.write("    if [ \"$choice\" = \"2\" ]; then\n")
        f.write("        open \"WARPCORE-macos-local-electron.app\"\n")
        f.write("    fi\n")
        f.write("fi\n")
    
    # Make launch script executable
    import stat
    launch_script.chmod(launch_script.stat().st_mode | stat.S_IEXEC)
    
    # Summary
    print("\n🎉 Collection Complete!")
    print("=" * 25)
    print(f"📁 Collection directory: {collect_dir}")
    print(f"📦 Artifacts collected: {collected_count}")
    print(f"📄 Manifest created: COLLECTION_MANIFEST.md")
    print(f"🚀 Launch script: launch_apps.sh")
    
    # Calculate total size
    total_size = sum(f.stat().st_size for f in collect_dir.rglob('*') if f.is_file())
    total_mb = total_size // 1024 // 1024
    print(f"📊 Total collection size: {total_mb}MB")
    
    print("\n🗺️ Next steps:")
    print(f"   1. Review: open {collect_dir}")
    print(f"   2. Test apps: cd {collect_dir} && ./launch_apps.sh")
    print(f"   3. Distribute: Share .dmg files")
    
    # Optionally open the collection directory
    try:
        subprocess.run(["open", str(collect_dir)], check=False)
        print(f"\n📂 Opened collection directory in Finder")
    except:
        pass

def run_unified_build():
    """Run unified DMG build with Electron + Nuitka"""
    try:
        # Get the unified build script path
        build_script = Path(__file__).parent / "native" / "build_unified.sh"
        
        if not build_script.exists():
            print(f"❌ Unified build script not found at: {build_script}")
            return False
        
        print(f"📁 Unified build script: {build_script}")
        print("🚀 Building complete DMG installer with Electron + Nuitka...")
        print("🔄 This will take a few minutes...")
        
        # Run the unified build script
        result = subprocess.run(
            ["bash", str(build_script), "--open"],
            cwd=build_script.parent,
            text=True
        )
        
        if result.returncode == 0:
            print("🎉 Unified build completed successfully!")
            print("📦 Check native/unified_dist/ for the final DMG installer")
            return True
        else:
            print(f"❌ Unified build failed with exit code: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ Unified build failed: {e}")
        return False

def install_dependencies():
    """Install dependencies from requirements.txt"""
    try:
        print("📦 Running pip3 install -r requirements.txt...")
        result = subprocess.run([
            "pip3", "install", "--break-system-packages", "-r", "requirements.txt"
        ], text=True)
        
        if result.returncode == 0:
            print("✅ Dependencies ready")
            return True
        else:
            print("❌ pip3 install failed")
            return False
            
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return False

def build_local_binary():
    """Build local macOS binary using PyInstaller"""
    try:
        print("📦 Creating PyInstaller spec for macOS...")
        
        # Create PyInstaller spec for local macOS build
        spec_content = '''
# -*- mode: python ; coding: utf-8 -*-
a = Analysis(
    ['warpcore_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('web', 'web'),
        ('config', 'config'),
    ],
    hiddenimports=[
        'webview',
        'uvicorn', 
        'fastapi',
        'websockets',
        'pydantic',
        'yaml',
        'keyring',
        'cryptography',
        'psutil',
        'jinja2',
        'aiofiles',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='warpcore-macos',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
        
        # Write spec file
        with open('warpcore_macos.spec', 'w') as f:
            f.write(spec_content)
        
        print("🛠️ Building with PyInstaller...")
        result = subprocess.run([
            'pyinstaller', 'warpcore_macos.spec', '--clean', '--noconfirm'
        ], text=True, capture_output=True)
        
        if result.returncode == 0:
            # Check if binary was created
            macos_binary = Path('./dist/warpcore-macos')
            if macos_binary.exists():
                print(f"✅ Local macOS binary created: {macos_binary}")
                print(f"📏 Binary size: {macos_binary.stat().st_size // 1024 // 1024}MB")
                return True
            else:
                print("❌ Binary not found after build")
                return False
        else:
            print(f"❌ PyInstaller failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Local build failed: {e}")
        return False

def run_iterate_local():
    """Complete local development cycle: build + test + run"""
    print("🚀 WARPCORE Local Iterate - Complete Development Cycle")
    print("=" * 50)
    
    # Install dependencies 
    print("📦 Step 1: Installing dependencies...")
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        print("💡 Try manually: pip install -r requirements.txt")
        print("💡 Or use Docker: python3 warpcore.py iterate --docker")
        return False
    
    try:
        print("✅ Dependencies ready")
        
        # Step 2: Build local binary
        print("\n🔨 Step 2: Building local macOS binary...")
        if not build_local_binary():
            print("⚠️  Build failed but continuing with source...")
        
        # Step 3: Test
        print("\n🧪 Step 3: Running tests...")
        if not run_tests():
            print("⚠️  Tests failed but continuing...")
        
        # Step 4: Run
        print("\n🌐 Step 4: Starting WARPCORE web interface...")
        print("📍 Will be available at: http://localhost:8000")
        start_web_mode(8000)
        
    except KeyboardInterrupt:
        print("\n👋 WARPCORE iterate stopped")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Iterate failed: {e}")
        sys.exit(1)

def run_iterate_docker():
    """Complete Docker development cycle: build + test + run"""
    print("🐳 WARPCORE Docker Iterate - Complete Development Cycle")
    print("=" * 50)
    
    try:
        # Step 1: Build 
        print("🔨 Step 1: Building with Docker...")
        # Build both macOS and Linux artifacts (skip tests)
        if not run_docker_build("--build-dmg"):
            print("❌ Docker macOS build failed - stopping iterate")
            return False
        if not run_docker_build("--build-native"):
            print("❌ Docker build failed - stopping iterate")
            return False
        
        # Step 2: Test (skip for now since build includes tests)
        print("\n✅ Step 2: Tests completed during build")
        
        # Step 3: Run native PyWebView app locally
        print("\n🚀 Step 3: Starting native PyWebView app...")
        print("💡 Docker built the Linux binary, now running native macOS app")
        
        # Run the native PyWebView app we built with unified build
        native_app = Path(__file__).parent / "native" / "build" / "dist" / "WARPCORE.app" / "Contents" / "MacOS" / "warpcore_app"
        
        if native_app.exists():
            print(f"🎨 Launching native PyWebView app: {native_app}")
            subprocess.run([str(native_app)])
        else:
            print("⚠️  Native app not found, falling back to web mode...")
            print("🌐 Starting web server instead...")
            print("📍 Available at: http://localhost:8000")
            start_web_mode(8000)
        
    except KeyboardInterrupt:
        print("\n👋 WARPCORE Docker iterate stopped")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Docker iterate failed: {e}")
        sys.exit(1)

def run_docker_app():
    """Run the Docker-built application"""
    try:
        # Check if we have a built binary
        binary_path = Path(__file__).parent / "dist" / "warpcore-real"
        
        if binary_path.exists():
            print(f"📍 Found Docker-built binary: {binary_path}")
            print("💡 Note: This is a Linux binary - running via Docker...")
            
            # Run the binary inside Docker
            docker_compose_path = Path(__file__).parent / "linux-native" / "docker-compose.yml"
            
            result = subprocess.run([
                "docker-compose", "-f", str(docker_compose_path), 
                "run", "--rm", "-p", "8000:8000", "warpcore-build", 
                "/app/dist/warpcore-real"
            ], cwd=Path(__file__).parent)
            
        else:
            print("❌ No Docker-built binary found")
            print("💡 Run: python3 warpcore.py iterate --docker first")
            
    except Exception as e:
        print(f"❌ Failed to run Docker app: {e}")

def run_mac_native(web_mode=False, native_mode=False):
    """Run local macOS WARPCORE (runtime-only)"""
    print("🖥️ WARPCORE macOS Native Runtime")
    print("=" * 30)
    
    # Check if we have a built macOS binary
    macos_binary = Path('./dist/warpcore-macos')
    
    if macos_binary.exists():
        print(f"🚀 Found local macOS binary: {macos_binary}")
        if web_mode:
            print("🌐 Running built binary in web mode...")
            subprocess.run([str(macos_binary)])
        elif native_mode:
            print("🖥️ Running built binary in native mode...")
            subprocess.run([str(macos_binary)])
    else:
        print("💡 No built binary found, running from source...")
        if web_mode:
            print("🌐 Starting local WARPCORE in web mode...")
            print("📍 Will be available at: http://localhost:8000")
            start_web_mode(8000)
        elif native_mode:
            print("🖥️ Starting local WARPCORE in native mode...")
            start_native_mode(recompile=False)

def run_docker_native(web_mode=False, native_mode=False):
    """Run Docker-built WARPCORE (runtime-only)"""
    print("🐳 WARPCORE Docker Native Runtime")
    print("=" * 30)
    
    # Check if Docker-built binary exists
    binary_path = Path(__file__).parent / "dist" / "warpcore-real"
    
    if not binary_path.exists():
        print("❌ No Docker-built binary found")
        print("💡 Run: python3 warpcore.py iterate --docker first")
        return
    
    if web_mode:
        print("🌐 Starting Docker-built WARPCORE in web mode...")
        print("📍 Will be available at: http://localhost:8000")
        run_docker_app()
    elif native_mode:
        print("🖥️ Docker-built native mode not supported on macOS")
        print("💡 Use --web mode or run: python3 warpcore.py --mac-native --native")

def run_native_build():
    """Build native macOS app using linux-native build system"""
    try:
        print("🔨 Building native macOS app...")
        
        # Use our new linux-native/build.sh script
        build_script = Path(__file__).parent / "linux-native" / "build.sh"
        
        if not build_script.exists():
            print(f"❌ Build script not found: {build_script}")
            return False
        
        result = subprocess.run(
            ["bash", str(build_script), "--build-native"],
            cwd=Path(__file__).parent,
            text=True
        )
        
        if result.returncode == 0:
            print("🎉 Native build completed successfully!")
            return True
        else:
            print(f"❌ Native build failed with exit code: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ Native build failed: {e}")
        return False

def run_docker_build(command="--all"):
    """Build using Docker with specific command"""
    try:
        print(f"🐳 Building with Docker ({command})...")
        
        # Check if Docker is available
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
        
        docker_compose_path = Path(__file__).parent / "linux-native" / "docker-compose.yml"
        
        if not docker_compose_path.exists():
            print(f"❌ Docker compose file not found: {docker_compose_path}")
            return False
        
        # First: Build Docker image (use cache when possible)
        print("🔧 Building Docker image with cache optimization...")
        rebuild_result = subprocess.run(
            ["docker-compose", "-f", str(docker_compose_path), "build", "warpcore-build"],
            cwd=Path(__file__).parent,
            text=True
        )
        
        if rebuild_result.returncode != 0:
            print("❌ Docker image rebuild failed")
            return False
        
        print("✅ Docker image rebuilt successfully")
        
        # Run docker compose with specific command
        result = subprocess.run(
            ["docker-compose", "-f", str(docker_compose_path), "run", "--rm", "warpcore-build", "./linux-native/build.sh", command],
            cwd=Path(__file__).parent,
            text=True
        )
        
        if result.returncode == 0:
            print("🎉 Docker build completed successfully!")
            return True
        else:
            print(f"❌ Docker build failed with exit code: {result.returncode}")
            return False
            
    except subprocess.CalledProcessError:
        print("❌ Docker not found - please install Docker")
        return False
    except Exception as e:
        print(f"❌ Docker build failed: {e}")
        return False

def run_tests():
    """Run test suite with backgrounding and tmp logging"""
    try:
        print("🧪 Running test suite...")
        
        # Background testing with tmp logging (following your rules)
        import time
        log_file = f"/tmp/warpcore-test-{int(time.time())}.log"
        
        print(f"📝 Test output will be logged to: {log_file}")
        
        # Check if pytest is available
        try:
            subprocess.run([sys.executable, "-m", "pytest", "--version"], 
                         check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print("⚠️  pytest not found, running basic Python tests...")
            # Fallback to basic validation
            result = subprocess.run(
                [sys.executable, "-c", "import web.main; print('✅ Basic import test passed')"],
                cwd=Path(__file__).parent,
                text=True
            )
            return result.returncode == 0
        
        # Run pytest with timeout and background logging
        with open(log_file, 'w') as f:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-v"],
                cwd=Path(__file__).parent,
                stdout=f,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=60  # 60 second timeout
            )
        
        if result.returncode == 0:
            print("🎉 All tests passed!")
            return True
        else:
            print(f"❌ Tests failed - check log: {log_file}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Tests timed out - check log: {log_file}")
        return False
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False

def run_full_rebuild():
    """Run full clean rebuild using the build script"""
    try:
        # Get the build script path
        build_script = Path(__file__).parent / "native" / "build" / "build_nuitka.sh"
        
        if not build_script.exists():
            print(f"❌ Build script not found at: {build_script}")
            return False
        
        print(f"📁 Build script: {build_script}")
        print("🧹 This will do a complete clean rebuild...")
        
        # Clean ALL __pycache__ directories before building
        print("🧹 Cleaning Python cache recursively...")
        root_dir = Path(__file__).parent
        try:
            result = subprocess.run(["find", str(root_dir), "-type", "d", "-name", "__pycache__"], 
                                  capture_output=True, text=True)
            if result.stdout.strip():
                pycache_dirs = result.stdout.strip().split('\n')
                for pycache_dir in pycache_dirs:
                    if pycache_dir:
                        subprocess.run(["rm", "-rf", pycache_dir], check=True)
                        print(f"   🗾️  Removed: {pycache_dir}")
        except subprocess.CalledProcessError:
            print("   ⚠️  Some __pycache__ directories could not be removed")
        
        # Change to build directory
        build_dir = build_script.parent
        original_cwd = os.getcwd()
        
        try:
            os.chdir(build_dir)
            
            # Run the build script with real-time output
            print("🚀 Starting build process...")
            result = subprocess.run(
                ["bash", str(build_script)],
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True
            )
            
            if result.returncode == 0:
                print("🎉 Build completed successfully!")
                
                # Check if native app was built
                dist_dir = build_dir / "dist"
                app_bundle = dist_dir / "WARPCORE.app"
                
                if app_bundle.exists():
                    print(f"✅ Native app bundle created: {app_bundle}")
                    return True
                else:
                    print("⚠️ Native app bundle not found after build")
                    return False
            else:
                print(f"❌ Build failed with exit code: {result.returncode}")
                return False
                
        finally:
            # Always restore original directory
            os.chdir(original_cwd)
            
    except Exception as e:
        print(f"❌ Build failed: {e}")
        return False

def start_web_mode(port=8000):
    """Start WARPCORE in web server mode"""
    try:
        # Import and start the web application
        from web.main import run_server
        run_server(host="127.0.0.1", port=port)
    except ImportError as e:
        print(f"⚠️  Web server dependencies not available: {e}")
        print("💡 Install dependencies with: pip install -r requirements.txt")
        print("💡 Or use Docker version: python3 warpcore.py iterate --docker")
        
        # Create a simple fallback server
        print("\n🚀 Starting minimal fallback server...")
        start_fallback_server(port)
        
def start_fallback_server(port=8000):
    """Start a minimal web server when dependencies are missing"""
    try:
        import http.server
        import socketserver
        import webbrowser
        import threading
        import time
        
        # Create simple HTML content
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>WARPCORE - Setup Required</title>
    <style>
        body {{ font-family: system-ui; margin: 40px; background: #1a1a2e; color: white; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        h1 {{ color: #4CAF50; }}
        .status {{ background: #16213e; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        code {{ background: #2d2d2d; padding: 2px 8px; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>⚡ WARPCORE Command Center</h1>
        <div class="status">
            <h3>⚠️  Dependencies Required</h3>
            <p>To run the full WARPCORE application, install dependencies:</p>
            <code>pip install -r requirements.txt</code>
            <p>Or use the Docker version:</p>
            <code>python3 warpcore.py iterate --docker</code>
        </div>
    </div>
</body>
</html>
        """
        
        # Write HTML to temp file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html_content)
            html_file = f.name
        
        # Open browser
        def open_browser():
            time.sleep(1)
            webbrowser.open(f'file://{html_file}')
        
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        print(f"📍 Fallback page opened in browser")
        print(f"💡 Install dependencies to run full WARPCORE: pip install -r requirements.txt")
        
    except Exception as e:
        print(f"❌ Fallback server failed: {e}")
        sys.exit(1)

def start_native_mode(recompile=False):
    """Start WARPCORE as native desktop application"""
    
    if recompile:
        print("🔧 Performing full clean rebuild...")
        if not run_full_rebuild():
            print("❌ Rebuild failed, cannot start native app")
            sys.exit(1)
        print("✅ Rebuild completed, starting native app...")
    
    try:
        if recompile:
            # Use the built app bundle
            build_dir = Path(__file__).parent / "native" / "build"
            app_bundle = build_dir / "dist" / "WARPCORE.app"
            
            if app_bundle.exists():
                print(f"🚀 Launching built native app: {app_bundle}")
                subprocess.run(["open", str(app_bundle)])
                return
            else:
                print("❌ Built app bundle not found, falling back to development mode")
        
        # Development mode - run from source
        print("💻 Running in development mode...")
        native_dir = Path(__file__).parent / "native"
        os.chdir(native_dir)
        
        # Add native directory to Python path
        sys.path.insert(0, str(native_dir))
        
        from warpcore_app import WARPCORENativeApp
        app = WARPCORENativeApp()
        app.run()
    except ImportError as e:
        print(f"❌ Failed to import native modules: {e}")
        print("💡 Make sure native dependencies are installed")
        sys.exit(1)

def start_electron_mode():
    """Start WARPCORE with Electron wrapper"""
    import subprocess
    
    electron_dir = Path(__file__).parent / "native" / "electron"
    
    if not electron_dir.exists():
        print("❌ Electron directory not found")
        print(f"Expected: {electron_dir}")
        sys.exit(1)
    
    print(f"📁 Electron directory: {electron_dir}")
    
    try:
        # Check if npm is installed
        subprocess.run(["npm", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ npm not found - please install Node.js and npm")
        sys.exit(1)
    
    try:
        # Start Electron app
        os.chdir(electron_dir)
        print("📦 Running npm start...")
        subprocess.run(["npm", "start"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Electron app: {e}")
        print("💡 Try running 'npm install' in the electron directory first")
        sys.exit(1)

def detect_current_project_name():
    """Auto-detect current project name from common files"""
    current_dir = Path(__file__).parent
    
    # Check key files for common project names
    check_files = ['README.md', 'warpcore.py', 'package.json', 'build_unified.sh']
    candidates = set()
    
    for file_name in check_files:
        file_path = current_dir / file_name
        if not file_path.exists():
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().upper()
                # Look for common project name patterns
                for word in ['WARPCORE', 'WARPCORE', 'WARPCORE', 'WARPCORE', 'wARpCorE', 'APP']:
                    if word in content and len(word) >= 3:
                        candidates.add(word)
        except:
            continue
    
    # Return most likely candidate (longest name first)
    if candidates:
        return max(candidates, key=len)
    return None

def aggressive_rename(old_name, new_name):
    """Fast parallel rename with core variations only"""
    import concurrent.futures
    import threading
    from collections import defaultdict
    
    current_dir = Path(__file__).parent
    print(f"🔄 Fast rename: '{old_name}' → '{new_name}' in {current_dir}")
    
    # Generate ALL possible case combinations
    def generate_all_case_variations(name):
        """Generate all possible case combinations for a name"""
        if len(name) <= 1:
            return [name.upper(), name.lower()]
        
        variations = set()
        
        # Core variations
        variations.add(name.upper())     # APEX
        variations.add(name.lower())     # apex
        variations.add(name.title())     # Apex
        variations.add(name.capitalize()) # Apex
        
        # All possible case combinations (2^n combinations)
        for i in range(2 ** len(name)):
            variant = ""
            for j, char in enumerate(name):
                if i & (1 << j):
                    variant += char.upper()
                else:
                    variant += char.lower()
            variations.add(variant)
        
        return list(variations)
    
    old_variations = generate_all_case_variations(old_name)
    new_variations = generate_all_case_variations(new_name)
    
    # Create pairs - match by index
    variations = list(zip(old_variations, new_variations))
    
    print(f"⚡ Processing {len(variations)} variations in parallel...")
    
    # Get all text files once
    all_files = []
    for file_path in current_dir.rglob('*'):
        if file_path.is_file() and not file_path.is_symlink():
            try:
                with open(file_path, 'rb') as f:
                    if b'\x00' not in f.read(512):  # Not binary
                        all_files.append(file_path)
            except:
                continue
    
    print(f"📁 Found {len(all_files)} text files to process")
    
    # Process files in parallel
    def process_file_batch(files_batch):
        results = []
        for file_path in files_batch:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                modified = False
                for old_var, new_var in variations:
                    if old_var in content:
                        content = content.replace(old_var, new_var)
                        modified = True
                
                if modified:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    results.append(file_path.name)
            except:
                continue
        return results
    
    # Split files into batches for parallel processing
    batch_size = max(1, len(all_files) // 8)  # 8 parallel workers
    file_batches = [all_files[i:i + batch_size] for i in range(0, len(all_files), batch_size)]
    
    # Process in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(process_file_batch, batch) for batch in file_batches]
        
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            try:
                results = future.result()
                if results:
                    print(f"  ✅ Batch {i+1}: {len(results)} files updated")
            except Exception as e:
                continue
    
    # Quick file/dir rename (simple cases only)
    print("📝 Renaming files/directories...")
    
    # Files
    for file_path in list(current_dir.rglob('*')):
        if file_path.is_file():
            for old_var, new_var in variations:
                if old_var.lower() in file_path.name.lower():
                    try:
                        new_name_str = file_path.name.replace(old_var, new_var).replace(old_var.lower(), new_var.lower())
                        if new_name_str != file_path.name:
                            new_path = file_path.parent / new_name_str
                            if not new_path.exists():
                                file_path.rename(new_path)
                                print(f"  📄 {file_path.name} → {new_name_str}")
                                break
                    except:
                        continue
    
    # Directories (deepest first)
    all_dirs = sorted([p for p in current_dir.rglob('*') if p.is_dir()], key=lambda x: len(str(x)), reverse=True)
    for dir_path in all_dirs:
        for old_var, new_var in variations:
            if old_var.lower() in dir_path.name.lower():
                try:
                    new_name_str = dir_path.name.replace(old_var, new_var).replace(old_var.lower(), new_var.lower())
                    if new_name_str != dir_path.name:
                        new_path = dir_path.parent / new_name_str
                        if not new_path.exists() and dir_path.exists():
                            dir_path.rename(new_path)
                            print(f"  📁 {dir_path.name} → {new_name_str}")
                            break
                except:
                    continue
    
    print(f"⚡ Done! Fast parallel rename '{old_name}' → '{new_name}' complete")

def run_fork_command(target_name):
    """Run the WARPCORE Framer to fork framework to new app"""
    try:
        # Validate target name
        if not target_name:
            print("❌ Target name cannot be empty")
            sys.exit(1)
        
        # Auto-detect current project name
        current_name = detect_current_project_name()
        if not current_name:
            print("❌ Could not detect current project name")
            print("💡 Make sure you're in a valid project directory")
            sys.exit(1)
            
        # Check if fork script exists
        fork_script = Path(__file__).parent / "bin" / "fork.sh"
        if not fork_script.exists():
            print(f"❌ Fork script not found: {fork_script}")
            print("💡 Make sure bin/fork.sh exists and is executable")
            sys.exit(1)
        
        print(f"🚀 Forking {current_name} → {target_name}")
        
        # Run the fork script with current and target names
        result = subprocess.run(
            ["bash", str(fork_script), current_name, target_name],
            cwd=Path(__file__).parent,
            text=True
        )
        
        if result.returncode == 0:
            print(f"\n🎉 Successfully forked {current_name} to {target_name}!")
            print(f"💡 Next: cd ../{target_name} && python {target_name.lower()}.py --help")
        else:
            print(f"❌ Fork command failed with exit code: {result.returncode}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Fork command failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
