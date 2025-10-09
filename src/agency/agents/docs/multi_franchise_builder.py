#!/usr/bin/env python3
"""
Multi-Franchise Documentation Builder
Combines individual franchise documentation into a unified tabbed interface
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import subprocess
import sys

# Add the flow generator to path for imports
sys.path.append(str(Path(__file__).parent.parent / "franchise" / "docs"))
try:
    from flow_generator import AgentFlowGenerator
except ImportError:
    print("⚠️ Could not import flow_generator, using basic functionality")
    AgentFlowGenerator = None

class MultiFranchiseDocBuilder:
    """Builds unified documentation from multiple franchise docs"""
    
    def __init__(self, franchise_base_path: Optional[Path] = None):
        self.base_path = Path(__file__).parent.parent
        self.franchise_base = franchise_base_path or (self.base_path / "franchise")
        self.output_dir = Path(__file__).parent
        
        self.discovered_franchises = self._discover_franchises()
        
    def _discover_franchises(self) -> Dict[str, Dict[str, Any]]:
        """Auto-discover franchise directories and their documentation"""
        franchises = {}
        
        if not self.franchise_base.exists():
            print(f"❌ Franchise base not found: {self.franchise_base}")
            return franchises
        
        for franchise_dir in self.franchise_base.glob("*/"):
            if franchise_dir.name in ['docs', '__pycache__', '.git']:
                continue
            
            franchise_name = franchise_dir.name
            agents_dir = franchise_dir / "agents"
            docs_dir = franchise_dir / "docs"
            
            if agents_dir.exists():
                # Count agents
                agent_files = list(agents_dir.glob("*.json"))
                
                # Check for existing documentation
                flow_generator = docs_dir / "flow_generator.py"
                existing_html = docs_dir / "warpcore_agent_flow_dynamic.html"
                mermaid_file = docs_dir / "agent_flow.mermaid"
                
                franchises[franchise_name] = {
                    'name': franchise_name,
                    'display_name': franchise_name.title(),
                    'path': franchise_dir,
                    'agents_dir': agents_dir,
                    'docs_dir': docs_dir,
                    'agent_count': len(agent_files),
                    'has_generator': flow_generator.exists(),
                    'has_existing_html': existing_html.exists(),
                    'has_mermaid': mermaid_file.exists(),
                    'generator_path': flow_generator,
                    'html_path': existing_html,
                    'mermaid_path': mermaid_file,
                    'focus': self._get_franchise_focus(franchise_name)
                }
                
                print(f"📁 Discovered {franchise_name}: {len(agent_files)} agents")
        
        return franchises
    
    def _get_franchise_focus(self, franchise_name: str) -> str:
        """Get franchise focus description"""
        focus_map = {
            'staff': 'Software Development',
            'framer': 'Content Intelligence'
        }
        return focus_map.get(franchise_name.lower(), 'General Purpose')
    
    def build_franchise_docs(self, franchise_name: str) -> bool:
        """Build documentation for a specific franchise"""
        if franchise_name not in self.discovered_franchises:
            print(f"❌ Franchise '{franchise_name}' not found")
            return False
        
        franchise_info = self.discovered_franchises[franchise_name]
        
        print(f"🔨 Building docs for {franchise_info['display_name']} franchise...")
        
        # Use the franchise's own flow generator if it exists
        generator_path = franchise_info['generator_path']
        agents_dir = franchise_info['agents_dir']
        docs_dir = franchise_info['docs_dir']
        
        if generator_path.exists():
            try:
                # Run the franchise's flow generator
                cmd = [
                    'python3', str(generator_path),
                    '--agents-dir', str(agents_dir),
                    '--output', str(docs_dir / 'warpcore_agent_flow_dynamic.html'),
                    '--mode', 'both'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(docs_dir))
                
                if result.returncode == 0:
                    print(f"✅ Built {franchise_name} franchise documentation")
                    return True
                else:
                    print(f"⚠️ Error building {franchise_name} docs: {result.stderr}")
                    
            except Exception as e:
                print(f"❌ Failed to build {franchise_name} docs: {e}")
        
        # Fallback: Use imported flow generator if available
        if AgentFlowGenerator:
            try:
                generator = AgentFlowGenerator(str(agents_dir))
                output_file = generator.build_documentation(str(docs_dir / 'warpcore_agent_flow_dynamic.html'))
                print(f"✅ Built {franchise_name} docs using fallback generator")
                return True
            except Exception as e:
                print(f"❌ Fallback generator failed for {franchise_name}: {e}")
        
        return False
    
    def build_all_franchise_docs(self) -> Dict[str, bool]:
        """Build documentation for all discovered franchises"""
        results = {}
        
        print(f"🏗️ Building documentation for {len(self.discovered_franchises)} franchises...")
        
        for franchise_name in self.discovered_franchises:
            results[franchise_name] = self.build_franchise_docs(franchise_name)
        
        return results
    
    def extract_mermaid_from_franchise(self, franchise_name: str) -> Optional[str]:
        """Extract mermaid diagram from franchise documentation"""
        if franchise_name not in self.discovered_franchises:
            return None
        
        franchise_info = self.discovered_franchises[franchise_name]
        mermaid_file = franchise_info['mermaid_path']
        
        if mermaid_file.exists():
            try:
                with open(mermaid_file, 'r') as f:
                    return f.read().strip()
            except Exception as e:
                print(f"⚠️ Could not read mermaid for {franchise_name}: {e}")
        
        return None
    
    def generate_unified_html(self) -> str:
        """Generate unified multi-franchise HTML documentation"""
        timestamp = datetime.now().isoformat()
        
        # Generate franchise tabs
        franchise_tabs = self._generate_franchise_tabs()
        franchise_content = self._generate_franchise_content()
        
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WARPCORE Multi-Franchise Agent Documentation</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
    <style>
        {self._get_unified_css_styles()}
    </style>
</head>
<body>
    <div class="container">
        <!-- Purfect Labs Header -->
        <div class="purfect-header">
            <div class="purfect-logo">Purfect Labs</div>
            <div class="purfect-tagline">UR DevOps. Purfectly Simplified.</div>
            <div class="purfect-subtitle">WARPCORE Multi-Franchise Agent Documentation</div>
            <div class="watermark">Generated: {timestamp}</div>
        </div>

        <!-- Franchise Selector -->
        <div class="franchise-selector">
            <div class="franchise-tabs">
                {franchise_tabs}
            </div>
        </div>

        <!-- Franchise Content -->
        <div class="franchise-content-container">
            {franchise_content}
        </div>
        
        <!-- Multi-Franchise Summary -->
        <div class="multi-franchise-summary">
            <h2>🌐 Multi-Franchise Overview</h2>
            <div class="summary-stats">
                {self._generate_summary_stats()}
            </div>
        </div>
    </div>

    <script>
        {self._get_unified_javascript()}
    </script>
</body>
</html>"""
        
        return html_template
    
    def _generate_franchise_tabs(self) -> str:
        """Generate franchise tab buttons"""
        tabs_html = ""
        
        for i, (franchise_name, franchise_info) in enumerate(self.discovered_franchises.items()):
            active_class = "active" if i == 0 else ""
            emoji = "🏢" if franchise_name == "staff" else "🎨"
            
            tabs_html += f"""
                <button class="franchise-tab {active_class}" data-franchise="{franchise_name}">
                    {emoji} {franchise_info['display_name']} Franchise
                    <span class="agent-count">{franchise_info['agent_count']} agents</span>
                </button>
            """
        
        return tabs_html
    
    def _generate_franchise_content(self) -> str:
        """Generate content sections for each franchise"""
        content_html = ""
        
        for i, (franchise_name, franchise_info) in enumerate(self.discovered_franchises.items()):
            active_class = "active" if i == 0 else ""
            
            # Extract mermaid diagram
            mermaid_content = self.extract_mermaid_from_franchise(franchise_name)
            mermaid_html = ""
            
            if mermaid_content:
                mermaid_html = f"""
                    <div class="mermaid-container">
                        <div class="mermaid">
{mermaid_content}
                        </div>
                    </div>
                """
            else:
                mermaid_html = f"""
                    <div class="mermaid-placeholder">
                        <p>📊 Mermaid diagram not available for {franchise_info['display_name']} franchise</p>
                        <p>Run the franchise documentation builder to generate diagrams</p>
                    </div>
                """
            
            content_html += f"""
            <div id="{franchise_name}-franchise" class="franchise-content {active_class}">
                <div class="franchise-header">
                    <h2>{'🏢' if franchise_name == 'staff' else '🎨'} {franchise_info['display_name']} Franchise - {franchise_info['focus']}</h2>
                    <p>{self._get_franchise_description(franchise_name)}</p>
                    <div class="franchise-stats">
                        <span class="stat">Agents: {franchise_info['agent_count']}</span>
                        <span class="stat">Focus: {franchise_info['focus']}</span>
                        <span class="stat">Path: {franchise_info['path'].name}/</span>
                    </div>
                </div>
                {mermaid_html}
            </div>
            """
        
        return content_html
    
    def _get_franchise_description(self, franchise_name: str) -> str:
        """Get franchise description"""
        descriptions = {
            'staff': 'Intelligent workflow automation for development operations and software implementation',
            'framer': 'AI-powered content creation, data analysis, and content intelligence systems'
        }
        return descriptions.get(franchise_name, 'Multi-purpose agent workflow system')
    
    def _generate_summary_stats(self) -> str:
        """Generate summary statistics across all franchises"""
        total_agents = sum(info['agent_count'] for info in self.discovered_franchises.values())
        total_franchises = len(self.discovered_franchises)
        
        stats_html = f"""
            <div class="summary-stat">
                <div class="stat-value">{total_franchises}</div>
                <div class="stat-label">Total Franchises</div>
            </div>
            <div class="summary-stat">
                <div class="stat-value">{total_agents}</div>
                <div class="stat-label">Total Agents</div>
            </div>
        """
        
        for franchise_name, franchise_info in self.discovered_franchises.items():
            emoji = "🏢" if franchise_name == "staff" else "🎨"
            stats_html += f"""
                <div class="summary-stat">
                    <div class="stat-value">{franchise_info['agent_count']}</div>
                    <div class="stat-label">{emoji} {franchise_info['display_name']}</div>
                </div>
            """
        
        return stats_html
    
    def _get_unified_css_styles(self) -> str:
        """Get CSS styles for unified documentation"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
            color: #f8fafc;
            line-height: 1.6;
            min-height: 100vh;
        }

        .container {
            padding: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }

        /* Purfect Labs Branding */
        .purfect-header {
            background: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 50%, #06b6d4 100%);
            padding: 40px;
            text-align: center;
            border-radius: 16px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(139, 92, 246, 0.2);
        }

        .purfect-logo {
            font-size: 2.5rem;
            font-weight: 800;
            color: white;
            text-shadow: 0 0 30px rgba(255, 255, 255, 0.3);
            margin-bottom: 8px;
        }

        .purfect-tagline {
            font-size: 1.2rem;
            color: rgba(255, 255, 255, 0.9);
            margin: 10px 0;
            font-weight: 600;
        }

        .purfect-subtitle {
            font-size: 1rem;
            color: rgba(255, 255, 255, 0.8);
            margin-bottom: 15px;
        }

        .watermark {
            background: rgba(255, 255, 255, 0.1);
            color: rgba(255, 255, 255, 0.8);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.85rem;
            display: inline-block;
            font-weight: 500;
        }

        /* Franchise Selector */
        .franchise-selector {
            margin-bottom: 30px;
        }

        .franchise-tabs {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            justify-content: center;
        }

        .franchise-tab {
            background: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 50%, #06b6d4 100%);
            border: none;
            color: white;
            padding: 16px 24px;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 1rem;
            font-weight: 600;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
            min-width: 200px;
        }

        .franchise-tab:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(139, 92, 246, 0.3);
        }

        .franchise-tab.active {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(139, 92, 246, 0.4);
            background: linear-gradient(135deg, #7c3aed 0%, #2563eb 50%, #0891b2 100%);
        }

        .agent-count {
            font-size: 0.8rem;
            font-weight: 400;
            opacity: 0.9;
        }

        /* Franchise Content */
        .franchise-content-container {
            position: relative;
        }

        .franchise-content {
            display: none;
            animation: fadeIn 0.3s ease-in-out;
        }

        .franchise-content.active {
            display: block;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .franchise-header {
            text-align: center;
            margin-bottom: 30px;
            padding: 30px;
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(59, 130, 246, 0.05) 100%);
            border-radius: 16px;
            border: 1px solid rgba(139, 92, 246, 0.2);
        }

        .franchise-header h2 {
            font-size: 2rem;
            margin-bottom: 10px;
            color: #8b5cf6;
            background: linear-gradient(135deg, #8b5cf6, #3b82f6);
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .franchise-header p {
            font-size: 1.1rem;
            color: #cbd5e1;
            margin-bottom: 15px;
        }

        .franchise-stats {
            display: flex;
            gap: 20px;
            justify-content: center;
            flex-wrap: wrap;
        }

        .franchise-stats .stat {
            background: rgba(139, 92, 246, 0.1);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 500;
            color: #a78bfa;
            border: 1px solid rgba(139, 92, 246, 0.2);
        }

        /* Mermaid Container */
        .mermaid-container {
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(30, 41, 59, 0.6) 100%);
            border-radius: 16px;
            padding: 30px;
            text-align: center;
            margin: 30px 0;
            border: 1px solid rgba(139, 92, 246, 0.1);
            backdrop-filter: blur(20px);
            box-shadow: 0 8px 32px rgba(139, 92, 246, 0.1);
        }

        .mermaid-placeholder {
            text-align: center;
            padding: 60px 20px;
            color: #6b7280;
            font-size: 1.1rem;
            background: rgba(139, 92, 246, 0.05);
            border-radius: 16px;
            border: 2px dashed rgba(139, 92, 246, 0.2);
            margin: 30px 0;
        }

        /* Multi-Franchise Summary */
        .multi-franchise-summary {
            margin-top: 40px;
            padding: 30px;
            background: linear-gradient(135deg, rgba(6, 182, 212, 0.1) 0%, rgba(139, 92, 246, 0.05) 100%);
            border-radius: 16px;
            border: 1px solid rgba(6, 182, 212, 0.2);
        }

        .multi-franchise-summary h2 {
            text-align: center;
            margin-bottom: 20px;
            color: #06b6d4;
            background: linear-gradient(135deg, #06b6d4, #8b5cf6);
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .summary-stats {
            display: flex;
            gap: 20px;
            justify-content: center;
            flex-wrap: wrap;
        }

        .summary-stat {
            background: linear-gradient(135deg, rgba(6, 182, 212, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            border: 1px solid rgba(6, 182, 212, 0.2);
            min-width: 120px;
        }

        .summary-stat .stat-value {
            font-size: 2rem;
            font-weight: 700;
            color: #06b6d4;
            display: block;
            margin-bottom: 8px;
        }

        .summary-stat .stat-label {
            color: #cbd5e1;
            font-size: 0.85rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        @media (max-width: 768px) {
            .container {
                padding: 15px;
            }
            
            .purfect-header {
                padding: 30px 20px;
            }
            
            .purfect-logo {
                font-size: 2rem;
            }
            
            .franchise-tabs {
                flex-direction: column;
                align-items: center;
            }
            
            .franchise-tab {
                min-width: 250px;
            }
            
            .franchise-stats {
                flex-direction: column;
                align-items: center;
            }
            
            .summary-stats {
                flex-direction: column;
                align-items: center;
            }
        }
        """
    
    def _get_unified_javascript(self) -> str:
        """Get JavaScript for unified documentation"""
        return """
        // Initialize Mermaid
        mermaid.initialize({
            startOnLoad: true,
            theme: 'dark',
            flowchart: {
                useMaxWidth: true,
                htmlLabels: true
            }
        });

        // Franchise tab switching
        document.querySelectorAll('.franchise-tab').forEach(tab => {
            tab.addEventListener('click', function() {
                const franchiseName = this.getAttribute('data-franchise');
                
                // Remove active from all tabs and content
                document.querySelectorAll('.franchise-tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.franchise-content').forEach(c => c.classList.remove('active'));
                
                // Activate clicked tab and corresponding content
                this.classList.add('active');
                document.getElementById(franchiseName + '-franchise').classList.add('active');
                
                // Reinitialize mermaid for the newly visible content
                setTimeout(() => {
                    mermaid.init(undefined, document.querySelector(`#${franchiseName}-franchise .mermaid`));
                }, 100);
            });
        });

        // Initialize first franchise content
        document.addEventListener('DOMContentLoaded', function() {
            const firstTab = document.querySelector('.franchise-tab.active');
            if (firstTab) {
                const franchiseName = firstTab.getAttribute('data-franchise');
                setTimeout(() => {
                    mermaid.init(undefined, document.querySelector(`#${franchiseName}-franchise .mermaid`));
                }, 100);
            }
        });
        """
    
    def build_unified_documentation(self, output_file: Optional[str] = None) -> str:
        """Build complete unified multi-franchise documentation"""
        if not output_file:
            output_file = str(self.output_dir / "multi_franchise_docs.html")
        
        print("🏗️ Building unified multi-franchise documentation...")
        
        # Build individual franchise docs first
        build_results = self.build_all_franchise_docs()
        
        # Generate unified HTML
        unified_html = self.generate_unified_html()
        
        # Save unified documentation
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(unified_html)
        
        print(f"✅ Multi-franchise documentation built: {output_file}")
        
        # Show results
        print(f"\n📊 Build Results:")
        for franchise, success in build_results.items():
            status = "✅" if success else "❌"
            print(f"   {status} {franchise.title()} franchise")
        
        return output_file

def main():
    """Command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-Franchise Documentation Builder")
    parser.add_argument('--franchise-dir', '-f', help='Path to franchise base directory')
    parser.add_argument('--output', '-o', help='Output HTML file path')
    parser.add_argument('--build-individual', '-i', action='store_true', help='Build individual franchise docs first')
    
    args = parser.parse_args()
    
    franchise_path = Path(args.franchise_dir) if args.franchise_dir else None
    builder = MultiFranchiseDocBuilder(franchise_path)
    
    if args.build_individual:
        print("🔨 Building individual franchise documentation...")
        results = builder.build_all_franchise_docs()
        for franchise, success in results.items():
            status = "✅" if success else "❌"
            print(f"   {status} {franchise}")
    
    # Build unified documentation
    output_file = builder.build_unified_documentation(args.output)
    
    print(f"\n🌐 Multi-franchise documentation: file://{os.path.abspath(output_file)}")

if __name__ == "__main__":
    main()