# 🚀 WARPCORE Agent Dashboard

A comprehensive web-based dashboard for viewing and analyzing all WARPCORE franchise agents, their JSON schemas, polymorphic mappings, and build information.

## 🔧 Features

- **Multi-Franchise Support**: View agents from all franchises (APEX, FRAMER, STAFF, PATROL)
- **JSON Schema Viewer**: Complete JSON representation of each agent with syntax highlighting
- **Polymorphic Schema Information**: Shows polymorphic mappings and schema-specific features
- **Build Information**: Displays static build info, caching strategies, and metadata
- **Search & Filter**: Real-time search across agents, schemas, and properties
- **Statistics Dashboard**: Overview of total agents, franchises, and polymorphic mappings
- **Interactive UI**: Expandable agent cards with tabbed content views

## 📁 Files

- `comprehensive_dashboard.html` - Main dashboard web interface
- `dashboard_data_loader.py` - Python script to load agent data from files
- `serve_dashboard.py` - HTTP server to serve the dashboard locally
- `dashboard_data.json` - Generated JSON data file with all agent information
- `README.md` - This documentation

## 🚀 Quick Start

### 1. Generate Dashboard Data

```bash
python dashboard_data_loader.py
```

This scans your franchise directories and generates `dashboard_data.json` with all agent information.

### 2. Start the Dashboard Server

```bash
python serve_dashboard.py
```

This will:
- Start a local HTTP server (typically on port 8080)
- Automatically open the dashboard in your browser
- Display the dashboard URL for manual access

### 3. Alternative Server Options

```bash
# Use specific port
python serve_dashboard.py --port 9000

# Don't auto-open browser
python serve_dashboard.py --no-browser

# Regenerate data before starting
python serve_dashboard.py --regenerate-data
```

## 📊 Dashboard Structure

### Franchise Tabs
- **APEX**: 4 agents (Commander, Tactician, Operator, Intel)
- **FRAMER**: 14 agents (Origin, Boss, Pathfinder, Oracle, etc.)
- **STAFF**: 11 agents (Legacy structure)
- **PATROL**: 15 agents (Including Deep, Cipher, Glitch, Zero)

### Agent Cards
Each agent card displays:

1. **JSON Schema Tab**
   - Complete agent JSON with syntax highlighting
   - All properties, schemas, and configurations

2. **Polymorphic Tab**
   - Schema class mapping (e.g., `BootstrapAgentSchema`)
   - Base features shared across schema types
   - Schema-specific features unique to that type

3. **Build Info Tab**
   - Static build information and timestamps
   - Caching strategy details
   - Polymorphic enhancement status

## 🔍 Search Functionality

The search box in the top-right allows filtering by:
- Agent names
- Schema properties
- Polymorphic classes
- Any text content within agent definitions

## 📈 Statistics

The dashboard displays real-time statistics:
- **Total Agents**: All agents across all franchises
- **Franchises**: Number of active franchises
- **Polymorphic Mappings**: Total schema mappings available

## 🏗️ Technical Details

### Data Loading
- Scans `franchise/` and `build_output/` directories
- Loads JSON files and extracts agent metadata
- Maps agents to polymorphic schemas
- Generates comprehensive data structure

### Polymorphic Schema Types
- `BootstrapAgentSchema` - System initialization
- `OrchestratorAgentSchema` - Workflow coordination
- `SchemaReconcilerAgentSchema` - File analysis and coherence
- `RequirementsGeneratorAgentSchema` - Requirements enumeration
- `RequirementsValidatorAgentSchema` - Validation and PAP compliance
- `ImplementationAgentSchema` - Code implementation and testing
- `GatePromoteAgentSchema` - Cross-validation and promotion
- `UserInputTranslatorAgentSchema` - Input processing

### Caching Strategy Visualization
Shows the three-tier caching system:
- **Workflow Cache**: Standard JSON for next agent
- **Asset Cache**: ALL generated work products
- **Artifacts Cache**: ONLY truly remarkable discoveries

## 🔄 Updating Data

The dashboard automatically loads real agent data if available. To refresh:

1. **Manual Regeneration**:
   ```bash
   python dashboard_data_loader.py
   ```

2. **Auto-regeneration with Server**:
   ```bash
   python serve_dashboard.py --regenerate-data
   ```

3. **Browser Refresh**: After regenerating data, refresh your browser

## 🎨 Visual Design

- **Cyberpunk Theme**: Dark background with neon accents
- **Color Coding**: Green (#00ff88) for primary, Blue (#00ccff) for secondary
- **Responsive Design**: Works on desktop and tablet devices
- **Smooth Animations**: Expandable cards and hover effects
- **Syntax Highlighting**: JSON properties color-coded by type

## 🚨 Troubleshooting

### Port Already in Use
The server automatically finds free ports. If you get port errors:
```bash
python serve_dashboard.py --port 9001
```

### Missing Agent Data
If no data loads:
```bash
python dashboard_data_loader.py
python serve_dashboard.py --regenerate-data
```

### Browser Cache Issues
Force refresh with Ctrl+F5 or Cmd+Shift+R

## 🔮 Future Enhancements

- Real-time agent status monitoring
- Agent execution history tracking
- Interactive flow diagrams
- Export functionality for agent data
- Comparison views between franchise agents
- Integration with agency.py workflow system

---

**Built for WARPCORE Agent System**  
*Comprehensive schema visualization and polymorphic analysis*