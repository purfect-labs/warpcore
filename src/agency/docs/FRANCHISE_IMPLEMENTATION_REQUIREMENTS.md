# WARPCORE Staff Franchise Implementation Requirements

## Executive Summary

Based on analysis of the 3 franchise specification documents and current WARPCORE architecture, this document provides comprehensive implementation requirements for making the Staff franchise fully functional within the new franchise-aware system. **All existing staff agents remain untouched** - this implementation focuses solely on CLI, discovery, cache isolation, and context injection systems.

## Current Analysis Summary

### ✅ What's Already Perfect (NO CHANGES NEEDED)
- **Staff Agent Files**: `/src/agency/agents/franchise/staff/agents/*.json` - All 11 agents are correctly structured
- **Agent Content**: All prompts, schemas, and workflows are production-ready
- **Directory Structure**: Franchise directory layout matches specification exactly
- **Agent Flow**: Staff agents follow correct PAP workflow patterns

### 🔧 What Needs Implementation (FOCUS AREAS)
1. **CLI Franchise Selection**: `--franchise` option and routing
2. **Agent Discovery**: Franchise-aware agent resolution
3. **Cache Isolation**: Franchise-specific cache directories
4. **Context Injection**: Staff-specific context headers
5. **Integration Testing**: Multi-layer validation patterns

---

## 1. CLI Interface Implementation

### File: `src/agency/agency.py`
**Requirements**: Add franchise-aware argument parsing and routing

**Current Issues**: 
- Hardcoded agent aliases pointing to old flat structure
- No `--franchise` option support
- Agent discovery not franchise-aware

**Implementation Requirements**:

```python
# UPDATE: Add franchise argument parsing
parser.add_argument('--franchise', '-f', 
                   choices=['staff', 'framer'], 
                   default='staff',
                   help='Select agent franchise (default: staff)')

parser.add_argument('--list-franchises', 
                   action='store_true',
                   help='List available franchises')

# UPDATE: Remove hardcoded agent_aliases - delegate to discovery
# DELETE: self.agent_aliases = { ... }  # Remove entirely
# REPLACE WITH: Dynamic discovery via AgentDiscovery class
```

**Key Changes**:
1. **Remove hardcoded aliases** - use franchise-aware discovery
2. **Add franchise parameter** to all agent execution methods
3. **Update help system** to show franchise-specific agents
4. **Maintain backward compatibility** - default to staff franchise

---

## 2. Agent Discovery System Updates

### File: `src/agency/utils/agent_discovery.py`
**Requirements**: Make discovery system franchise-aware

**Current Issues**:
- Discovery looks in `/agents/*.json` (old flat structure)
- No franchise parameter support
- Path resolution not franchise-aware

**Implementation Requirements**:

```python
class AgentDiscovery:
    def __init__(self, base_path: Path, franchise: str = "staff"):
        self.base_path = base_path
        self.franchise = franchise
        self.agents_path = self._resolve_franchise_path()
        self.schema_path = self._resolve_schema_path()
        
    def _resolve_franchise_path(self) -> Path:
        """Resolve franchise-specific agent path"""
        franchise_base = self.base_path / "agents" / "franchise" / self.franchise
        
        # Staff: agents in franchise/staff/agents/
        # Framer: agents in franchise/framer/agents/
        return franchise_base / "agents"
    
    def _resolve_schema_path(self) -> Path:
        """Resolve franchise-specific schema file"""
        franchise_base = self.base_path / "agents" / "franchise" / self.franchise
        
        # Look for franchise-specific schema first
        if (franchise_base / "docs" / "warpcore_agent_flow_schema.json").exists():
            return franchise_base / "docs" / "warpcore_agent_flow_schema.json"
        
        # Fallback to shared docs
        return self.base_path / "agents" / "franchise" / "docs" / "warpcore_agent_flow_schema.json"
```

**Key Changes**:
1. **Add franchise parameter** to constructor
2. **Update path resolution** to use franchise structure  
3. **Maintain existing methods** - same interface, different paths
4. **Add franchise validation** - error handling for missing franchises

---

## 3. Agency Composition Updates

### File: `src/agency/utils/agency_composition.py`
**Requirements**: Pass franchise parameter through composition layer

**Current Issues**:
- No franchise parameter in constructor
- AgentDiscovery instantiated without franchise
- Methods don't pass franchise context

**Implementation Requirements**:

```python
class WARPCOREAgencyComposition:
    def __init__(self, client_dir_absolute: Optional[str] = None, franchise: str = "staff"):
        # Store franchise
        self.franchise = franchise
        
        # Update agent discovery to use franchise
        self.agent_discovery = AgentDiscovery(self.base_path, franchise)
        
        # Update other components to be franchise-aware
        self.workflow_manager = WorkflowManager(self.base_path, self.client_dir_absolute, franchise)
        self.agent_executor = AgentExecutor(self.base_path, self.client_dir_absolute, self.agent_discovery, franchise)
        
        # Update cache manager for franchise isolation
        self.cache_manager = CacheManager(self.primary_cache, self.secondary_cache, franchise)
```

**Key Changes**:
1. **Add franchise parameter** to constructor with default "staff"
2. **Pass franchise** to all utility classes
3. **Update configuration display** to show active franchise
4. **Maintain backward compatibility** - default behavior unchanged

---

## 4. Cache Isolation Implementation

### File: `src/agency/utils/cache_manager.py`
**Requirements**: Implement franchise-specific cache directories

**Current Issues**:
- Cache paths not franchise-aware
- Potential cross-contamination between franchises

**Implementation Requirements**:

```python
class CacheManager:
    def __init__(self, primary_cache: Path, secondary_cache: Path, franchise: str = "staff"):
        self.franchise = franchise
        
        # Create franchise-specific cache paths
        self.primary_cache = primary_cache / "franchise" / franchise
        self.secondary_cache = secondary_cache / "franchise" / franchise
        
        # Ensure directories exist
        self.primary_cache.mkdir(parents=True, exist_ok=True)
        self.secondary_cache.mkdir(parents=True, exist_ok=True)
    
    def get_cache_path(self, workflow_id: str, trace_id: str, agent_name: str, cache_type: str = "output") -> str:
        """Generate franchise-aware cache file path"""
        cache_filename = f"{workflow_id}_{trace_id}_{agent_name}_{cache_type}.json"
        return str(self.primary_cache / cache_filename)
```

**Key Changes**:
1. **Add franchise subdirectories** to cache paths
2. **Isolate franchise caches** - no cross-contamination  
3. **Update asset directive** to include franchise in paths
4. **Maintain dual-cache pattern** - both primary and secondary

---

## 5. Context Injection System

### File: `src/agency/utils/context_injector.py` (NEW FILE)
**Requirements**: Create franchise-specific context header injection

**Implementation Requirements**:

```python
class FranchiseContextInjector:
    def __init__(self, franchise: str):
        self.franchise = franchise
        self.context_templates = {
            "staff": self._get_staff_context_template(),
            "framer": self._get_framer_context_template()
        }
    
    def _get_staff_context_template(self) -> str:
        return '''
## STAFF FRANCHISE CONTEXT (SOFTWARE DEVELOPMENT FOCUS)

**Current Working Directory**: CLIENT_DIR_ABSOLUTE
**Platform**: Cross-platform compatible  
**Shell**: System default shell
**Python**: Available system Python
**Home**: USER_HOME
**Trace ID**: TRACE_ID (for step ordering)
**Franchise**: Staff (Software Development Focus)
**Agent**: {agent_id} - {agent_role}
**Workflow Position**: {workflow_position}

### STAFF PROJECT STRUCTURE
```
CLIENT_DIR_ABSOLUTE/
├── .data/franchise/staff/       # Staff workflow cache and results
├── src/agency/                  # Agency system (staff franchise default)
├── src/api/                     # PAP architecture implementation
├── src/testing/                 # Multi-layer testing framework
├── docs/                        # Documentation
└── src/agency/agents/franchise/staff/ # Staff agent specifications
```

### AVAILABLE STAFF TOOLS
**Development**: code analysis, PAP architecture validation, schema reconciliation
**Testing**: multi-layer validation, background testing, fail-fast patterns
**Implementation**: file operations, git operations, database operations
**Quality**: code coherence, architectural compliance, security validation
**Documentation**: technical writing, API documentation, architecture diagrams

### STAFF WORKFLOW SEQUENCE
**Phase 1**: Bootstrap (Origin → Boss)
**Phase 2**: Analysis (Boss → Pathfinder) + User Input (User → Oracle)  
**Phase 3**: Architecture (Pathfinder + Oracle → Architect → Enforcer)
**Phase 4**: Implementation (Enforcer → Craftsman ↔ Craftbuddy → Gatekeeper)

### STAFF MISSION STATEMENT
Transform user requirements into high-quality, architecturally compliant code implementations.
Focus: Requirements → Analysis → Architecture → Implementation → Validation
Architecture: PAP-compliant software development with comprehensive testing
```
'''
    
    def inject_context(self, agent_spec: Dict[str, Any], **context_vars) -> Dict[str, Any]:
        """Inject franchise-specific context into agent prompt"""
        context_template = self.context_templates[self.franchise]
        enhanced_spec = agent_spec.copy()
        
        # Format context with provided variables
        context_header = context_template.format(**context_vars)
        
        # Inject at start of prompt (after existing environment context)
        original_prompt = enhanced_spec.get('prompt', '')
        enhanced_spec['prompt'] = context_header + '\n\n' + original_prompt
        
        return enhanced_spec
```

**Key Features**:
1. **Franchise-specific templates** - different contexts per franchise
2. **Variable substitution** - dynamic context injection
3. **Prompt enhancement** - preserve original prompt, add context
4. **Extensible design** - easy to add new franchises

---

## 6. Agent Executor Updates

### File: `src/agency/utils/agent_executor.py`
**Requirements**: Integrate franchise-aware discovery and context injection

**Implementation Requirements**:

```python
class AgentExecutor:
    def __init__(self, base_path: Path, client_dir_absolute: Path, 
                 agent_discovery: AgentDiscovery, franchise: str = "staff"):
        self.franchise = franchise
        self.context_injector = FranchiseContextInjector(franchise)
        # ... rest of initialization
    
    def execute_individual_agent(self, agent_alias: str, workflow_id: Optional[str] = None, 
                                user_input_or_spec: Optional[str] = None, 
                                user_input: Optional[Dict] = None) -> bool:
        # Use franchise-aware discovery to resolve agent
        agent_info = self.agent_discovery.get_agent_info(agent_alias)
        if not agent_info:
            print(f"❌ Agent '{agent_alias}' not found in '{self.franchise}' franchise")
            available = self.agent_discovery.list_all_agents()
            print(f"Available agents: {', '.join(available)}")
            return False
        
        # Inject franchise-specific context
        enhanced_spec = self.context_injector.inject_context(
            agent_info['agent_data'],
            agent_id=agent_alias,
            agent_role=agent_info.get('role', 'Unknown'),
            workflow_position=agent_info.get('position', 'Unknown')
        )
        
        # Continue with execution using enhanced spec...
```

---

## File Modification Summary

### Files to Modify:
1. **`src/agency/agency.py`** - Add franchise CLI support, remove hardcoded aliases
2. **`src/agency/utils/agent_discovery.py`** - Add franchise awareness 
3. **`src/agency/utils/agency_composition.py`** - Pass franchise through layers
4. **`src/agency/utils/cache_manager.py`** - Add franchise cache isolation
5. **`src/agency/utils/agent_executor.py`** - Integrate context injection

### Files to Create:
1. **`src/agency/utils/context_injector.py`** - Franchise context injection system
2. **`src/agency/tests/test_franchise_integration.py`** - Comprehensive testing

### Files to NOT Touch:
- **ALL staff agent files** - `/src/agency/agents/franchise/staff/agents/*.json`
- **Staff directory structure** - Perfect as is
- **Agent schemas and prompts** - No modifications needed

---

## Success Criteria

### ✅ Implementation Success Indicators:
1. **Backward Compatibility**: All existing `python agency.py` commands work identically
2. **Franchise Selection**: `python agency.py --franchise staff oracle` works correctly  
3. **Agent Discovery**: Staff agents discovered from franchise directory structure
4. **Cache Isolation**: Staff workflows cache to `.data/franchise/staff/`
5. **Context Injection**: Staff agents receive appropriate context headers
6. **Error Handling**: Clear messages for franchise and agent resolution issues
7. **Testing**: All franchise integration tests pass

### 🧪 Validation Commands:
```bash
# Test backward compatibility (should work unchanged)
python agency.py pathfinder
python agency.py gap_analysis

# Test explicit franchise selection (new functionality)  
python agency.py --franchise staff pathfinder
python agency.py --list-franchises

# Test agent discovery (should find staff agents in new location)
python agency.py agents

# Test cache isolation (should create franchise-specific directories)
ls -la .data/franchise/staff/
```

---

This implementation preserves all existing staff functionality while adding the franchise architecture foundation needed to support the framer franchise and future expansions.

<citations>
<document>
<document_type>RULE</document_type>
<document_id>NoSE2KykRQ88LJcPkrCOBC</document_id>
</document>
<document>
<document_type>RULE</document_type>
<document_id>ZdkT2akGMr8kwyxWhsPYkw</document_id>
</document>
<document>
<document_type>RULE</document_type>
<document_id>asIO3B744xXFjLwhR7suHb</document_id>
</document>
</citations>