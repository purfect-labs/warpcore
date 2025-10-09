#!/usr/bin/env python3
"""
Universal Mermaid ASCII Parser - Completely franchise-agnostic
Takes ANY Mermaid flowchart syntax and converts it to beautiful ASCII art for terminal display.
Works with any Mermaid content, not tied to any specific system or schema.
"""
import re
from typing import Dict, List, Tuple, Any, Optional

class MermaidASCIIParser:
    def __init__(self):
        # Color codes for beautiful terminal output
        self.colors = {
            'red': '\033[91m', 'green': '\033[92m', 'yellow': '\033[93m',
            'blue': '\033[94m', 'magenta': '\033[95m', 'cyan': '\033[96m',
            'white': '\033[97m', 'bold': '\033[1m', 'reset': '\033[0m'
        }
        
    def parse_mermaid_content(self, mermaid_content: str) -> Dict[str, Any]:
        """Parse raw Mermaid content into structured data"""
        # Handle literal \n sequences in the content
        if '\\n' in mermaid_content:
            mermaid_content = mermaid_content.replace('\\n', '\n')
        
        lines = mermaid_content.split('\n')
        
        # Extract diagram type
        diagram_type = self._extract_diagram_type(lines)
        
        # Parse nodes and connections
        nodes = self._parse_nodes(lines)
        connections = self._parse_connections(lines)
        
        # Extract any styling information
        styles = self._parse_styles(lines)
        
        return {
            'type': diagram_type,
            'nodes': nodes,
            'connections': connections,
            'styles': styles,
            'raw_content': mermaid_content
        }
    
    def _extract_diagram_type(self, lines: List[str]) -> str:
        """Extract the diagram type from Mermaid syntax"""
        for line in lines:
            line = line.strip()
            if line.startswith('flowchart') or line.startswith('graph'):
                return 'flowchart'
            elif line.startswith('sequenceDiagram'):
                return 'sequence'
            elif line.startswith('gantt'):
                return 'gantt'
            elif line.startswith('gitgraph'):
                return 'gitgraph'
            elif line.startswith('erDiagram'):
                return 'entity_relationship'
            elif line.startswith('classDiagram'):
                return 'class'
        return 'unknown'
    
    def _parse_nodes(self, lines: List[str]) -> Dict[str, Dict[str, str]]:
        """Parse node definitions from Mermaid syntax"""
        nodes = {}
        
        for line in lines:
            line = line.strip()
            
            # Skip comments and empty lines
            if line.startswith('%%') or not line or '-->' in line:
                continue
                
            # Parse various node definition patterns
            node_patterns = [
                # Standard rectangular: A[Label] or A["Label"]
                r'^\s*([A-Za-z0-9_]+)\[([^\]]+)\]',
                # Rounded: A(Label) or A("Label")  
                r'^\s*([A-Za-z0-9_]+)\(([^)]+)\)',
                # Circle: A((Label))
                r'^\s*([A-Za-z0-9_]+)\(\(([^)]+)\)\)',
                # Asymmetric: A>Label]
                r'^\s*([A-Za-z0-9_]+)>([^\]]+)\]',
                # Rhombus: A{Label}
                r'^\s*([A-Za-z0-9_]+)\{([^}]+)\}',
                # Hexagon: A{{Label}}
                r'^\s*([A-Za-z0-9_]+)\{\{([^}]+)\}\}',
                # Stadium: A([Label])
                r'^\s*([A-Za-z0-9_]+)\(\[([^\]]+)\]\)',
                # Subroutine: A[[Label]]
                r'^\s*([A-Za-z0-9_]+)\[\[([^\]]+)\]\]'
            ]
            
            for pattern in node_patterns:
                match = re.match(pattern, line)
                if match:
                    node_id = match.group(1)
                    node_label = match.group(2).replace('"', '').replace('<br/>', ' ').replace('<br>', ' ')
                    
                    # Determine node shape
                    if '((' in line and '))' in line:
                        shape = 'circle'
                    elif '(' in line and ')' in line:
                        shape = 'rounded'
                    elif '{' in line and '}' in line:
                        shape = 'diamond'
                    elif '{{' in line and '}}' in line:
                        shape = 'hexagon'
                    elif '[[' in line and ']]' in line:
                        shape = 'subroutine'
                    elif '([' in line and '])' in line:
                        shape = 'stadium'
                    elif '>' in line:
                        shape = 'asymmetric'
                    else:
                        shape = 'rectangle'
                    
                    nodes[node_id] = {
                        'label': node_label.strip(),
                        'shape': shape,
                        'id': node_id
                    }
                    break
        
        return nodes
    
    def _parse_connections(self, lines: List[str]) -> List[Tuple[str, str, str, str]]:
        """Parse connections/edges from Mermaid syntax"""
        connections = []
        
        for line in lines:
            line = line.strip()
            
            # Skip comments and node definitions
            if line.startswith('%%') or not line or not '--' in line:
                continue
            
            # Parse different arrow types and connections
            connection_patterns = [
                # With label: A -->|"label"| B
                r'^\s*([A-Za-z0-9_]+)\s*(-->|---|\.-\.>|\.-\.|\-\.\-|\=\=\=\>|\=\=\=)\s*\|\s*"?([^"|]+)"?\s*\|\s*([A-Za-z0-9_]+)',
                # Simple: A --> B
                r'^\s*([A-Za-z0-9_]+)\s*(-->|---|\.-\.>|\.-\.|\-\.\-|\=\=\=\>|\=\=\=)\s*([A-Za-z0-9_]+)',
                # Multi-node: A --> B & C
                r'^\s*([A-Za-z0-9_]+)\s*(-->|---|\.-\.>|\.-\.|\-\.\-|\=\=\=\>|\=\=\=)\s*([A-Za-z0-9_&\s]+)'
            ]
            
            for pattern in connection_patterns:
                match = re.match(pattern, line)
                if match:
                    from_node = match.group(1)
                    arrow_type = match.group(2)
                    
                    if len(match.groups()) == 4:
                        # Has label
                        label = match.group(3)
                        to_node = match.group(4)
                        connections.append((from_node, to_node, label, arrow_type))
                    else:
                        # No label - check for multi-node
                        to_nodes = match.group(3)
                        if '&' in to_nodes:
                            # Multiple target nodes
                            targets = [n.strip() for n in to_nodes.split('&')]
                            for target in targets:
                                connections.append((from_node, target, '', arrow_type))
                        else:
                            connections.append((from_node, to_nodes, '', arrow_type))
                    break
        
        return connections
    
    def _parse_styles(self, lines: List[str]) -> Dict[str, Dict[str, str]]:
        """Parse styling information from Mermaid syntax"""
        styles = {}
        
        for line in lines:
            line = line.strip()
            
            # Parse classDef: classDef className fill:#f9f,stroke:#333,stroke-width:4px
            if line.startswith('classDef'):
                parts = line.split(' ', 2)
                if len(parts) >= 3:
                    class_name = parts[1]
                    style_def = parts[2]
                    styles[class_name] = self._parse_style_definition(style_def)
        
        return styles
    
    def _parse_style_definition(self, style_def: str) -> Dict[str, str]:
        """Parse individual style definition"""
        style = {}
        # Simple parsing of style properties
        properties = style_def.split(',')
        for prop in properties:
            if ':' in prop:
                key, value = prop.split(':', 1)
                style[key.strip()] = value.strip()
        return style
    
    def generate_ascii_art(self, parsed_data: Dict[str, Any], title: str = "MERMAID FLOW") -> str:
        """Generate beautiful ASCII art from parsed Mermaid data"""
        nodes = parsed_data['nodes']
        connections = parsed_data['connections']
        diagram_type = parsed_data['type']
        
        ascii_lines = []
        
        # Header
        ascii_lines.append(f"{self.colors['bold']}{self.colors['cyan']}")
        ascii_lines.append("╔════════════════════════════════════════════════════════════════════════════════╗")
        ascii_lines.append(f"║                    🎯 {title.upper()} DIAGRAM 🎯                    ║")
        ascii_lines.append("╚════════════════════════════════════════════════════════════════════════════════╝")
        ascii_lines.append(f"{self.colors['reset']}")
        ascii_lines.append("")
        
        # Diagram type info
        ascii_lines.append(f"{self.colors['yellow']}📋 Diagram Type: {self.colors['bold']}{diagram_type.upper()}{self.colors['reset']}")
        ascii_lines.append("")
        
        # Nodes section
        if nodes:
            ascii_lines.append(f"{self.colors['bold']}{self.colors['green']}🔵 NODES ({len(nodes)}):{self.colors['reset']}")
            
            # Group nodes by shape for better visualization
            shape_groups = {}
            for node_id, node_data in nodes.items():
                shape = node_data['shape']
                if shape not in shape_groups:
                    shape_groups[shape] = []
                shape_groups[shape].append((node_id, node_data['label']))
            
            for shape, node_list in shape_groups.items():
                shape_emoji = self._get_shape_emoji(shape)
                ascii_lines.append(f"  {shape_emoji} {shape.title()}:")
                for node_id, label in node_list:
                    clean_label = label.replace(' ', '_').upper()
                    ascii_lines.append(f"     {self.colors['white']}{node_id}{self.colors['reset']} → {self.colors['cyan']}{clean_label}{self.colors['reset']}")
            ascii_lines.append("")
        
        # Connections section
        if connections:
            ascii_lines.append(f"{self.colors['bold']}{self.colors['blue']}🔗 CONNECTIONS ({len(connections)}):{self.colors['reset']}")
            
            # Group connections by arrow type
            arrow_groups = {}
            for from_node, to_node, label, arrow_type in connections:
                if arrow_type not in arrow_groups:
                    arrow_groups[arrow_type] = []
                arrow_groups[arrow_type].append((from_node, to_node, label))
            
            for arrow_type, conn_list in arrow_groups.items():
                arrow_emoji = self._get_arrow_emoji(arrow_type)
                arrow_symbol = self._get_arrow_symbol(arrow_type)
                ascii_lines.append(f"  {arrow_emoji} {arrow_type}:")
                
                for from_node, to_node, label in conn_list:
                    from_label = nodes.get(from_node, {}).get('label', from_node)
                    to_label = nodes.get(to_node, {}).get('label', to_node)
                    
                    if label:
                        conn_str = f"{self.colors['magenta']}{from_label}{self.colors['reset']} {arrow_symbol} {self.colors['cyan']}{to_label}{self.colors['reset']} {self.colors['yellow']}[{label}]{self.colors['reset']}"
                    else:
                        conn_str = f"{self.colors['magenta']}{from_label}{self.colors['reset']} {arrow_symbol} {self.colors['cyan']}{to_label}{self.colors['reset']}"
                    
                    ascii_lines.append(f"     {conn_str}")
            ascii_lines.append("")
        
        # Summary footer
        ascii_lines.append(f"{self.colors['bold']}{self.colors['cyan']}╔════════════════════════════════════════════════════════════════════════════════╗")
        ascii_lines.append(f"║  📊 {len(nodes)} Nodes  •  {len(connections)} Connections  •  {diagram_type.title()} Diagram  ║")
        ascii_lines.append(f"╚════════════════════════════════════════════════════════════════════════════════╝{self.colors['reset']}")
        
        return "\n".join(ascii_lines)
    
    def _get_shape_emoji(self, shape: str) -> str:
        """Get emoji for node shape"""
        shape_emojis = {
            'rectangle': '⬜',
            'rounded': '⭕',
            'circle': '⚫',
            'diamond': '🔶',
            'hexagon': '⬡',
            'stadium': '🏟️',
            'subroutine': '📦',
            'asymmetric': '📐'
        }
        return shape_emojis.get(shape, '🔸')
    
    def _get_arrow_emoji(self, arrow_type: str) -> str:
        """Get emoji for arrow type"""
        arrow_emojis = {
            '-->': '➡️',
            '---': '➖',
            '.--.>': '🔀',
            '.-.': '⚪',
            '-.-': '⚬',
            '===>': '⚡',
            '===': '🔗'
        }
        return arrow_emojis.get(arrow_type, '🔗')
    
    def _get_arrow_symbol(self, arrow_type: str) -> str:
        """Get Unicode symbol for arrow type"""
        arrow_symbols = {
            '-->': '→',
            '---': '—',
            '.--.>': '⇢',
            '.-.': '⋯',
            '-.-': '⋅⋅⋅',
            '===>': '⟹',
            '===': '≡'
        }
        return arrow_symbols.get(arrow_type, '→')

def parse_mermaid_to_ascii(mermaid_content: str, title: str = "MERMAID FLOW") -> str:
    """Standalone function to convert any Mermaid content to ASCII art"""
    parser = MermaidASCIIParser()
    parsed_data = parser.parse_mermaid_content(mermaid_content)
    return parser.generate_ascii_art(parsed_data, title)

# CLI interface for standalone usage
if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert Mermaid flowchart to ASCII art")
    parser.add_argument("input_file", help="Mermaid file to convert")
    parser.add_argument("--title", default="MERMAID FLOW", help="Title for the ASCII diagram")
    
    args = parser.parse_args()
    
    try:
        with open(args.input_file, 'r') as f:
            mermaid_content = f.read()
        
        ascii_art = parse_mermaid_to_ascii(mermaid_content, args.title)
        print(ascii_art)
        
    except FileNotFoundError:
        print(f"❌ File not found: {args.input_file}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)