# WARPCORE Agency System

🚀 **Intelligent workflow selector and agent orchestrator**

## Quick Start

```bash
# Interactive mode
python src/agency/agency.py

# Command line mode  
python src/agency/agency.py <workflow_id> [input.json]

# Make executable
chmod +x src/agency/agency.py
./src/agency/agency.py
```

## Available Workflows

| ID | Workflow | Description |
|----|----------|-------------|
| 1 | **Gap Analysis** | Analyze codebase gaps and generate fixes |
| 2 | **Security Licensing** | Implement license management system |
| 3 | **Manual Requirements** | Convert user specs to structured requirements |
| 4 | **User Input Translator** | Convert raw specs to validated requirements |
| 5 | **Custom Agent Chain** | Build custom workflow from available agents |
| 6 | **System Management** | Manage agents, schemas, and compression |

## Agent Chain Execution

### Gap Analysis Workflow (ID: 1)
```
bootstrap → orchestrator → schema_reconciler → requirements_generator → requirements_validator → implementor → gate_promote
```

**Example:**
```bash
python src/agency/agency.py 1
```

### User Input Translator (ID: 4)
**Example:**
```bash
python src/agency/agency.py 4
```

## System Management (ID: 6)

Available operations:
1. **Update agent schemas** - Apply polymorphic system to all agents
2. **Compress old workflow data** - Archive and optimize storage
3. **Validate agent specifications** - Check all agent JSON files
4. **Create new agent from template** - Generate new agent spec

**Example:**
```bash
echo "1" | python src/agency/agency.py 6  # Update schemas
```

## Directory Structure

```
src/agency/
├── agency.py           # Main entry point
├── agents/            # Agent JSON specifications
├── workflows/         # Workflow definitions
├── systems/           # System management scripts
├── web/              # Web dashboard
└── utils/            # Utility modules
```

## Available Agents

- `bootstrap` - Initialize workflow and environment
- `orchestrator` - Coordinate agent execution
- `schema_reconciler` - Handle schema validation and reconciliation
- `requirements_generator` - Generate structured requirements
- `requirements_validator` - Validate and enhance requirements
- `implementor` - Generate code implementations
- `gate_promote` - Final validation and promotion
- `user_input_translator` - Convert raw user input to structured format

## JSON Input Format

For command-line execution with JSON input:

```json
{
  "workflow_id": "wf_20241007_123456_abc12345",
  "user_specifications": {
    "title": "WARP DEMO Test Requirements",
    "description": "WARP FAKE test scenario",
    "requirements_text": "Build a simple API endpoint",
    "timeline": "1 week",
    "priorities": ["high", "security"]
  },
  "context": {
    "codebase_path": "/path/to/codebase",
    "target_language": "python"
  }
}
```

## Features

✅ **Interactive & Command-Line Modes**
- Menu-driven workflow selection
- Direct CLI execution with parameters
- JSON input file support

✅ **Agent Orchestration**
- Dynamic agent loading from JSON specs
- Workflow ID generation and tracking
- Agent availability validation

✅ **System Integration**
- Polymorphic schema system integration
- Data compression capabilities
- Error handling and logging

✅ **User Experience** 
- Clear visual indicators with emojis
- Step-by-step execution logging
- Graceful error handling and shutdown

## Error Handling

The system provides comprehensive error handling:

- **Unknown workflows** - Returns exit code 1
- **Missing agents** - Stops execution with clear error message
- **File not found** - Handles missing JSON input gracefully
- **Keyboard interrupt** - Clean shutdown with goodbye message

## Development

### Adding New Workflows

1. Add workflow to `list_available_workflows()`
2. Implement workflow method following pattern
3. Add to `execute_workflow()` mapping
4. Update this documentation

### Adding New Agents

1. Create agent JSON spec in `agents/` directory
2. Agent will be automatically discovered
3. Can be used in custom workflows immediately

## Integration

The agency system integrates with:
- **Agent Schema System** - Polymorphic schema management
- **Data Compression** - Workflow data archival
- **Web Dashboard** - Visual workflow monitoring (coming soon)

---

🚀 **WARPCORE Agency** - Built for intelligent workflow orchestration with WARP DEMO watermarking in all test outputs.