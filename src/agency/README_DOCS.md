# WARPCORE Agency Documentation System

🚀 **WARP-DEMO** Auto-generating documentation system that creates beautiful HTML visualizations from real agent schemas.

## Overview

The WARPCORE Agency Documentation System automatically parses your agent JSON files and generates dynamic Mermaid flow diagrams and comprehensive HTML documentation. The system reads the actual agent file structure, extracts input/output relationships from filenames, and cross-references with JSON schema data to create accurate flow visualizations.

## Features

✅ **Real Schema Parsing**: Reads actual agent JSON files, not hardcoded data  
✅ **Dynamic Flow Generation**: Creates Mermaid diagrams from filename patterns  
✅ **Beautiful HTML Output**: Comprehensive documentation with tabs and styling  
✅ **CLI Integration**: Built into the agency.py command system  
✅ **Build Automation**: Scripts for automated documentation rebuilds  
✅ **WARP-DEMO Watermarks**: Following user rules for test/demo markers  

## Quick Start

### Generate Documentation

```bash
# Full HTML documentation
python agency.py docs build

# Flow diagram only
python agency.py docs flow

# HTML documentation (explicit)
python agency.py docs html
```

### Using Build Scripts

```bash
# Simple one-time build
python build_docs_simple.py

# List all agent files
python build_docs_simple.py --list-only

# Generate flow diagram only
python build_docs_simple.py --flow-only
```

## Generated Files

The documentation system creates:

- **Dynamic HTML**: `/docs/agency/warpcore_agent_flow_dynamic.html`
- **Mermaid Flow**: Generated and embedded in HTML
- **Agent Analysis**: Real-time parsing of JSON schemas

## File Structure Analysis

The system intelligently parses agent filenames using the pattern:
```
{position}_{agent}_from_{inputs}_to_{outputs}.json
```

Examples:
- `0a_origin_from_none_to_boss.json` → Origin outputs to Boss
- `4b_craftbuddy_from_craftsman_to_enforcer_gatekeeper.json` → CraftBuddy can loop back to Enforcer or promote to Gatekeeper

## Documentation Features

### Interactive HTML Dashboard
- **Flow Tab**: Dynamic Mermaid diagram with real agent relationships
- **Agents Tab**: Individual agent cards with details
- **Schema Tab**: JSON representation of the complete flow
- **Files Tab**: Current agent file structure

### Real-Time Statistics
- Total agent count
- Unique position mapping
- Loop pattern detection
- Parallel flow identification

### Styling & Theming
- Dark theme with WARPCORE colors
- Agent-specific color coding
- Responsive design for all screen sizes
- WARP-DEMO watermarks as per user rules

## Advanced Usage

### Custom Agents Directory
```bash
python agency.py --agents-dir /path/to/custom/agents docs build
```

### Integration with Web Dashboard

The generated documentation can be integrated into the main WARPCORE web dashboard by:

1. Adding the flow generator to the dashboard routes
2. Serving the generated HTML as an iframe or embedded content
3. Using the Mermaid data for real-time flow visualization

### API Integration Example

```python
from flow_generator import AgentFlowGenerator

generator = AgentFlowGenerator(agents_dir="./agents")
mermaid_flow = generator.generate_mermaid_flow()
html_docs = generator.generate_html_documentation()
```

## Build System Architecture

### Core Components

1. **flow_generator.py**: Main engine for parsing and generation
2. **agency.py**: CLI integration with docs commands
3. **build_docs_simple.py**: Standalone build automation

### Flow Generation Process

1. **Agent Discovery**: Scan agents directory for JSON files
2. **Schema Parsing**: Extract metadata from each agent file
3. **Relationship Mapping**: Parse input/output flow from filenames
4. **Mermaid Generation**: Create flowchart syntax with styling
5. **HTML Assembly**: Build complete documentation with tabs

### Styling System

- **Agent Colors**: Each agent type has a specific color scheme
- **Flow Arrows**: Different arrow styles for loops vs promotions
- **Responsive Layout**: Mobile-friendly grid systems
- **WARP-DEMO Branding**: Consistent watermarking per user rules

## Maintenance

### Adding New Agents

The system automatically discovers new agents following the naming pattern:
```
{position}_{name}_from_{inputs}_to_{outputs}.json
```

### Updating Documentation

Documentation updates automatically when:
- Agent files are modified
- New agents are added
- Agent relationships change

### Troubleshooting

**Common Issues:**
- Ensure agent files follow the naming pattern
- Check that JSON files are valid
- Verify flow_generator.py is in the agency directory

**Debugging:**
```bash
# Validate agent files
python build_docs_simple.py --list-only

# Test flow generation only
python agency.py docs flow
```

## Integration with WARPCORE Web

The documentation system is designed to integrate seamlessly with the existing WARPCORE web dashboard:

1. **Route Addition**: Add `/docs/flow` endpoint
2. **Real-time Updates**: Regenerate on agent file changes  
3. **API Endpoints**: Serve Mermaid data for dynamic visualization
4. **Dashboard Embedding**: Include flow visualization in main UI

## Future Enhancements

- [ ] Real-time file watching with automatic rebuilds
- [ ] Interactive flow diagram editing
- [ ] Agent performance metrics visualization
- [ ] Integration with workflow execution data
- [ ] Export to multiple formats (PDF, PNG, SVG)

---

**🚀 WARP-DEMO Documentation System** - Generating beautiful documentation from real agent schemas!