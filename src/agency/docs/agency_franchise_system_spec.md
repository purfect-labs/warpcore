# WARPCORE Agency Franchise System Specification

## Executive Summary

The WARPCORE Agency system now supports **franchise-based agent architectures** where different agent collections (franchises) can operate using the same workflow patterns but with different domain expertise. The `--franchise` CLI option allows users to switch between agent sets while maintaining identical command interfaces.

## Franchise Architecture Overview

### Core Concept
- **Staff Franchise**: Software development agents (default)
- **Framer Franchise**: Intelligence collection & content creation agents
- **Future Franchises**: Marketing, Sales, DevOps, etc.

### Directory Structure
```
src/agency/agents/
├── franchise/
│   ├── staff/                    # Default franchise (software development)
│   │   ├── 0a_origin_from_none_to_boss.json
│   │   ├── 0b_boss_from_origin_to_pathfinder.json
│   │   ├── 1a_pathfinder_from_boss_to_architect.json
│   │   ├── 1b_oracle_from_user_to_architect.json
│   │   ├── 2_architect_from_pathfinder_oracle_to_enforcer.json
│   │   ├── 3_enforcer_from_architect_craftbuddy_to_craftsman.json
│   │   ├── 4a_craftsman_from_enforcer_gatekeeper_to_craftbuddy.json
│   │   ├── 4b_craftbuddy_from_craftsman_to_enforcer_gatekeeper.json
│   │   ├── 5_gatekeeper_from_craftbuddy_to_craftsman_pathfinder.json
│   │   ├── harmony_meta_coherence_agent.json
│   │   └── mama_bear.json
│   ├── framer/                   # Intelligence & content creation franchise
│   │   ├── agents/
│   │   │   ├── 0a_origin_from_none_to_boss.json
│   │   │   ├── 0b_boss_from_origin_to_pathfinder.json
│   │   │   ├── 1a_pathfinder_from_boss_to_architect.json
│   │   │   ├── 1b_oracle_from_user_to_architect.json
│   │   │   ├── 2_architect_from_pathfinder_oracle_to_enforcer.json
│   │   │   ├── 3_enforcer_from_architect_craftbuddy_to_craftsman.json
│   │   │   ├── 4a_craftsman_from_enforcer_gatekeeper_to_craftbuddy.json
│   │   │   ├── 4b_craftbuddy_from_craftsman_to_enforcer_gatekeeper.json
│   │   │   ├── 5_gatekeeper_from_craftbuddy_to_craftsman_pathfinder.json
│   │   │   ├── 6_ghostwriter_from_gatekeeper_to_alice.json
│   │   │   ├── 7_alice_from_ghostwriter_to_flux.json
│   │   │   ├── 8_flux_from_alice_to_complete.json
│   │   │   ├── harmony_meta_coherence_agent.json
│   │   │   └── mama_bear.json
│   │   └── docs/
│   │       ├── mermaid_flow_config.json
│   │       ├── warpcore_agent_flow_schema.json
│   │       └── framer_flow_preview.html
│   └── docs/                     # Shared franchise documentation
└── __legacy__/                   # Old flat agent structure (deprecated)
```

## CLI Interface Specification

### Backward Compatibility
Current staff commands work identically:
```bash
# These work exactly as before (default to staff franchise)
python agency.py oracle "Build user auth system"
python agency.py pathfinder
python agency.py gap_analysis
```

### Franchise Selection
New `--franchise` option:
```bash
# Explicit staff franchise (identical behavior to default)
python agency.py --franchise staff oracle "Build user auth system"

# Framer franchise (intelligence collection)
python agency.py --franchise framer oracle "Research crypto Twitter sentiment"

# Framer-specific agents
python agency.py --franchise framer ghostwriter "workflow_id_123"
python agency.py --franchise framer alice "workflow_id_123"
python agency.py --franchise framer flux "workflow_id_123"
```

### Franchise Discovery
```bash
# List available franchises
python agency.py --list-franchises

# List agents in specific franchise
python agency.py --franchise staff --list-agents
python agency.py --franchise framer --list-agents
```

## Agency.py CLI Architecture

### Updated Command Structure
```python
parser.add_argument('--franchise', '-f', 
                   choices=['staff', 'framer'], 
                   default='staff',
                   help='Select agent franchise (default: staff)')
parser.add_argument('--list-franchises', 
                   action='store_true',
                   help='List available franchises')
parser.add_argument('workflow_or_agent', nargs='?', 
                   help='Agent alias (origin, boss, pathfinder, etc.) or workflow command')
```

### Franchise Resolution Logic
1. **Default Resolution**: If no `--franchise` specified, use `staff`
2. **Franchise Validation**: Ensure specified franchise exists
3. **Agent Resolution**: Find agent in franchise-specific directory
4. **Context Injection**: Apply franchise-specific headers and context

### Error Handling
```python
def resolve_franchise_agent(franchise: str, agent_alias: str) -> Optional[Path]:
    franchise_path = agents_base / "franchise" / franchise
    
    if franchise == "staff":
        agent_search_path = franchise_path
    else:
        agent_search_path = franchise_path / "agents"
    
    if not agent_search_path.exists():
        raise FranchiseNotFoundError(f"Franchise '{franchise}' not found")
    
    agent_files = list(agent_search_path.glob(f"*{agent_alias}*.json"))
    if not agent_files:
        available_agents = discover_franchise_agents(franchise)
        raise AgentNotFoundError(
            f"Agent '{agent_alias}' not found in franchise '{franchise}'\n"
            f"Available agents: {', '.join(available_agents)}"
        )
    
    return agent_files[0]
```

## AgentDiscovery Class Updates

### Franchise-Aware Discovery
```python
class AgentDiscovery:
    def __init__(self, base_path: Path, franchise: str = "staff"):
        self.base_path = base_path
        self.franchise = franchise
        self.agents_path = self._resolve_franchise_path()
        self.schema_path = self._resolve_schema_path()
        
    def _resolve_franchise_path(self) -> Path:
        franchise_base = self.base_path / "agents" / "franchise" / self.franchise
        
        if self.franchise == "staff":
            return franchise_base
        else:
            return franchise_base / "agents"
    
    def _resolve_schema_path(self) -> Path:
        franchise_base = self.base_path / "agents" / "franchise" / self.franchise
        
        if (franchise_base / "docs" / "warpcore_agent_flow_schema.json").exists():
            return franchise_base / "docs" / "warpcore_agent_flow_schema.json"
        
        # Fallback to shared docs
        return self.base_path / "agents" / "franchise" / "docs" / "warpcore_agent_flow_schema.json"
```

### Multi-Franchise Discovery
```python
def discover_all_franchises(base_path: Path) -> Dict[str, Dict[str, Any]]:
    franchise_base = base_path / "agents" / "franchise"
    franchises = {}
    
    for franchise_dir in franchise_base.iterdir():
        if not franchise_dir.is_dir() or franchise_dir.name.startswith('.'):
            continue
            
        franchise_name = franchise_dir.name
        franchise_info = {
            'name': franchise_name,
            'path': franchise_dir,
            'agents_path': None,
            'docs_path': None,
            'agent_count': 0,
            'available_agents': []
        }
        
        # Determine agent path structure
        if franchise_name == "staff":
            franchise_info['agents_path'] = franchise_dir
        else:
            franchise_info['agents_path'] = franchise_dir / "agents"
        
        # Find docs path
        if (franchise_dir / "docs").exists():
            franchise_info['docs_path'] = franchise_dir / "docs"
        
        # Count agents
        if franchise_info['agents_path'] and franchise_info['agents_path'].exists():
            agent_files = list(franchise_info['agents_path'].glob("*.json"))
            franchise_info['agent_count'] = len(agent_files)
            franchise_info['available_agents'] = [
                f.stem for f in agent_files if not f.name.startswith('__')
            ]
        
        franchises[franchise_name] = franchise_info
    
    return franchises
```

## Caching Architecture

### Franchise-Layer Cache Namespacing
```python
class FranchiseCacheManager:
    def __init__(self, primary_cache: Path, secondary_cache: Path, franchise: str):
        self.primary_cache = primary_cache
        self.secondary_cache = secondary_cache
        self.franchise = franchise
        
    def get_franchise_cache_path(self, cache_base: Path, workflow_id: str) -> Path:
        return cache_base / "franchise" / self.franchise / workflow_id
    
    def enforce_dual_cache_write(self, workflow_id: str, trace_id: str, 
                                agent_name: str, output_data: Dict[str, Any]) -> bool:
        cache_filename = f"{workflow_id}_{trace_id}_{agent_name}_output.json"
        
        # Franchise-specific cache paths
        primary_franchise_path = self.get_franchise_cache_path(self.primary_cache, workflow_id)
        secondary_franchise_path = self.get_franchise_cache_path(self.secondary_cache, workflow_id)
        
        primary_file = primary_franchise_path / cache_filename
        secondary_file = secondary_franchise_path / cache_filename
        
        success = True
        
        try:
            # Ensure franchise directories exist
            primary_franchise_path.mkdir(parents=True, exist_ok=True)
            secondary_franchise_path.mkdir(parents=True, exist_ok=True)
            
            # Write to both caches with franchise isolation
            with open(primary_file, 'w') as f:
                json.dump(output_data, f, indent=2)
            
            with open(secondary_file, 'w') as f:
                json.dump(output_data, f, indent=2)
            
            print(f"✅ FRANCHISE CACHE: {self.franchise} / {cache_filename}")
            
        except Exception as e:
            print(f"❌ FRANCHISE CACHE WRITE FAILED: {e}")
            success = False
        
        return success
```

### Cache Isolation Benefits
- **No Cross-Contamination**: Staff and Framer workflows isolated
- **Parallel Execution**: Different franchises can run simultaneously
- **Audit Trail**: Clear franchise attribution in cache
- **Cleanup**: Franchise-specific cache cleanup

## Context Header Injection

### Franchise-Specific Headers
```python
class FranchiseContextManager:
    def __init__(self, franchise: str):
        self.franchise = franchise
        
    def get_franchise_context_header(self) -> str:
        if self.franchise == "staff":
            return self._get_staff_context_header()
        elif self.franchise == "framer":
            return self._get_framer_context_header()
        else:
            return self._get_default_context_header()
    
    def _get_staff_context_header(self) -> str:
        return '''
## STAFF FRANCHISE CONTEXT (SOFTWARE DEVELOPMENT)

**Current Working Directory**: CLIENT_DIR_ABSOLUTE
**Platform**: Cross-platform compatible
**Shell**: System default shell
**Python**: Available system Python
**Home**: USER_HOME
**Trace ID**: TRACE_ID (for step ordering)
**Franchise**: Staff (Software Development Focus)

### PROJECT STRUCTURE (DYNAMIC - DO NOT SCAN)
```
CLIENT_DIR_ABSOLUTE/
├── .data/                     # Workflow cache and results
├── .config/                   # Configuration files
├── src/agency/                # Main agency system
│   ├── agents/franchise/staff/# Staff agent specifications
│   ├── systems/              # Schema and system management
│   ├── workflows/            # Workflow specifications
│   └── agency.py             # Main orchestrator
├── src/api/                   # PAP architecture implementation
│   ├── controllers/          # Business logic controllers
│   ├── providers/            # Data/service providers
│   ├── orchestrators/        # Workflow orchestrators
│   └── middleware/           # Cross-cutting concerns
└── docs/                     # Documentation
```

### AVAILABLE TOOLS AND PRIMITIVES
**File Operations**: read_files, write_files, file_glob, find_files
**Execution**: run_command, subprocess, shell scripting
**Git**: Full git repository with version control
**Database**: SQLite available, existing licensing database
**Config**: Hierarchical config system (.config/warpcore.config)
**Web**: Flask/FastAPI servers, web dashboard
**Testing**: Playwright, pytest, multi-layer validation

### STAFF FRANCHISE MISSION
Transform user requirements into PAP-compliant software implementations
Focus: Codebase analysis, requirements generation, implementation, testing
Architecture: Route → Controller → Orchestrator → Provider → Middleware → Executor
'''
    
    def _get_framer_context_header(self) -> str:
        return '''
## FRAMER FRANCHISE CONTEXT (INTELLIGENCE & CONTENT CREATION)

**Current Working Directory**: CLIENT_DIR_ABSOLUTE
**Platform**: Cross-platform compatible
**Shell**: System default shell
**Python**: Available system Python
**Home**: USER_HOME
**Trace ID**: TRACE_ID (for step ordering)
**Franchise**: Framer (Intelligence Collection & Content Creation Focus)

### PROJECT STRUCTURE (DYNAMIC - DO NOT SCAN)
```
CLIENT_DIR_ABSOLUTE/
├── .data/franchise/framer/    # Framer workflow cache and results
├── .config/                   # Configuration files
├── src/agency/                # Main agency system
│   └── agents/franchise/framer/# Framer agent specifications
├── intelligence/              # Intelligence collection results
│   ├── sources/              # Data source configurations
│   ├── raw/                  # Raw collected data
│   ├── processed/            # Processed intelligence
│   └── reports/              # Intelligence reports
└── content/                   # Content creation outputs
    ├── drafts/               # Content drafts
    ├── assets/               # Media assets
    └── published/            # Published content
```

### AVAILABLE TOOLS AND PRIMITIVES
**Data Collection**: web scraping, API calls, social media monitoring
**Content Processing**: text analysis, sentiment analysis, pattern recognition
**Content Creation**: text generation, formatting, style adaptation
**Publishing**: multi-platform content distribution
**Intelligence**: research synthesis, trend analysis, insight generation

### FRAMER FRANCHISE MISSION
Transform user research intents into intelligence collection and content creation
Focus: Data gathering, analysis, insight generation, content creation, publishing
Flow: Intelligence → Analysis → Content → Enhancement → Publishing
'''
```

## Agent Execution Flow

### Franchise-Aware Execution
```python
class FranchiseAgentExecutor:
    def __init__(self, franchise: str, base_path: Path, client_dir: Path):
        self.franchise = franchise
        self.discovery = AgentDiscovery(base_path, franchise)
        self.cache_manager = FranchiseCacheManager(
            client_dir.parent / ".data", 
            base_path / ".data", 
            franchise
        )
        self.context_manager = FranchiseContextManager(franchise)
        
    def execute_agent(self, agent_alias: str, workflow_id: str, 
                     user_input: Optional[str] = None) -> bool:
        # Resolve franchise-specific agent
        agent_info = self.discovery.get_agent_info(agent_alias)
        if not agent_info:
            print(f"❌ Agent '{agent_alias}' not found in {self.franchise} franchise")
            return False
        
        # Load agent specification
        agent_spec = agent_info['agent_data']
        
        # Inject franchise-specific context
        enhanced_spec = self._inject_franchise_context(agent_spec)
        
        # Add user input if provided
        if user_input:
            enhanced_spec = self._inject_user_input(enhanced_spec, user_input, agent_alias)
        
        # Execute with franchise context
        return self._execute_with_franchise_context(enhanced_spec, agent_alias, workflow_id)
    
    def _inject_franchise_context(self, agent_spec: Dict[str, Any]) -> Dict[str, Any]:
        context_header = self.context_manager.get_franchise_context_header()
        original_prompt = agent_spec.get('prompt', '')
        
        enhanced_spec = agent_spec.copy()
        enhanced_spec['prompt'] = context_header + "\n\n" + original_prompt
        
        return enhanced_spec
```

## Migration Strategy

### Phase 1: Backward Compatibility (Immediate)
- All existing staff commands work identically
- `--franchise staff` is optional (defaults to staff)
- No changes required for current workflows

### Phase 2: Framer Franchise Introduction
- `--franchise framer` enables framer agents
- Framer agents accessible with same command patterns
- Franchise-specific caching implemented

### Phase 3: Advanced Features
- Cross-franchise workflows
- Franchise composition patterns
- Advanced caching strategies

## Testing Strategy

### Unit Tests
```python
def test_franchise_discovery():
    base_path = Path("/test/agency")
    discovery = AgentDiscovery(base_path, "staff")
    agents = discovery.list_all_agents()
    assert "oracle" in agents
    
def test_franchise_caching():
    cache_manager = FranchiseCacheManager(Path("/cache1"), Path("/cache2"), "framer")
    success = cache_manager.enforce_dual_cache_write("wf_123", "tr_456", "oracle", {"test": "data"})
    assert success
    
def test_cli_franchise_selection():
    # Test that --franchise framer uses framer agents
    # Test that default uses staff agents
    # Test franchise validation
    pass
```

### Integration Tests
```python
def test_staff_franchise_identical_behavior():
    # Ensure staff franchise behaves identically to pre-franchise system
    pass
    
def test_framer_franchise_execution():
    # Test framer agents execute with proper context
    pass
    
def test_franchise_cache_isolation():
    # Ensure staff and framer caches don't interfere
    pass
```

## Error Handling

### Franchise-Specific Errors
```python
class FranchiseError(Exception):
    """Base exception for franchise-related errors"""
    pass

class FranchiseNotFoundError(FranchiseError):
    """Raised when specified franchise doesn't exist"""
    pass

class AgentNotFoundInFranchiseError(FranchiseError):
    """Raised when agent not found in specified franchise"""
    pass

class FranchiseCacheError(FranchiseError):
    """Raised when franchise cache operations fail"""
    pass
```

### User-Friendly Error Messages
```
❌ Franchise 'marketing' not found
   Available franchises: staff, framer
   
❌ Agent 'ghostwriter' not found in staff franchise  
   Available agents: origin, boss, pathfinder, oracle, architect, enforcer, craftsman, craftbuddy, gatekeeper
   💡 Try: python agency.py --franchise framer ghostwriter

❌ Framer franchise cache write failed
   Check permissions on .data/franchise/framer/ directory
```

## Documentation Updates

### CLI Help Updates
```bash
python agency.py --help
# Shows franchise options prominently

python agency.py --franchise framer --help  
# Shows framer-specific help and agents

python agency.py oracle --help
# Shows oracle help with franchise context
```

### Franchise-Specific Documentation
- Staff franchise: Focus on software development workflows
- Framer franchise: Focus on intelligence and content creation
- Migration guides for each franchise type

## Security Considerations

### Franchise Isolation
- Cache isolation prevents data leakage between franchises
- Different context headers prevent prompt injection
- Separate execution environments for different domain focuses

### Access Control
- Franchise selection is explicit and validated
- No automatic cross-franchise access
- Clear audit trails for franchise usage

This specification ensures the WARPCORE Agency system maintains perfect backward compatibility while enabling powerful franchise-based agent architectures for different domain focuses.