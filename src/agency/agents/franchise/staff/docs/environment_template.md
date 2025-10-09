# POLYMORPHIC ENVIRONMENT TEMPLATE
# Use this template in all agent prompts - placeholders get populated dynamically

```
## ENVIRONMENT CONTEXT (DO NOT DISCOVER - USE THIS INFO)

**Current Working Directory**: {{WORKING_DIR}}
**Platform**: {{PLATFORM}} ({{ARCHITECTURE}})
**Shell**: {{SHELL}} {{SHELL_VERSION}}
**Python**: {{PYTHON_VERSION}}
**Home**: {{HOME_DIR}}
**Timestamp**: {{CURRENT_TIMESTAMP}}

### AGENT SYSTEM ARCHITECTURE (KNOWN - DO NOT SCAN)
```
{{WORKING_DIR}}/src/agency/
├── agents/                    # Agent JSON specifications ({{TOTAL_AGENTS}} active agents)
│   ├── docs/                 # Documentation generation system
│   │   ├── flow_generator.py        # Mermaid/HTML generator
│   │   ├── mermaid_flow_config.json # Styling configuration
│   │   ├── warpcore_agent_flow_schema.json # Master schema
│   │   └── warpcore_agent_flow.mermaid     # Generated diagram
{{AGENT_FILE_LIST}}
├── agency.py                  # Main orchestrator
└── warpcore_agent_flow_schema.json # Root schema file
```

**IMPORTANT**: Use this context - do NOT waste time discovering what you already know!
```

# PLACEHOLDER DEFINITIONS
- {{WORKING_DIR}}: Current working directory path
- {{PLATFORM}}: Operating system name  
- {{ARCHITECTURE}}: System architecture
- {{SHELL}}: Current shell executable
- {{SHELL_VERSION}}: Shell version string
- {{PYTHON_VERSION}}: Python version
- {{HOME_DIR}}: User home directory
- {{CURRENT_TIMESTAMP}}: ISO format timestamp
- {{TOTAL_AGENTS}}: Current count of active agents
- {{AGENT_FILE_LIST}}: Dynamic list of agent files with descriptions