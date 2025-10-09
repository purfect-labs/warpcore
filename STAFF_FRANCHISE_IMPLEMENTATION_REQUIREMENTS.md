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
        
        # Staff: agents directly in franchise/staff/agents/
        # Framer: agents in franchise/framer/agents/
        if self.franchise == "staff":
            return franchise_base / "agents"
        else:
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

**Current Issues**:
- Not franchise-aware
- No context injection
- Hardcoded agent resolution

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

**Key Changes**:
1. **Add franchise parameter** and context injector
2. **Use franchise-aware discovery** instead of hardcoded paths
3. **Inject context** before agent execution
4. **Improve error handling** with franchise-specific messages

---

## 6. Multi-Franchise Documentation Builder

### File: `src/agency/agents/franchise/docs/flow_generator.py` (ENHANCEMENT)
**Requirements**: Extend documentation builder for multi-franchise support with Purfect Labs branding

**Current State**: 
- Single-franchise documentation generation
- Basic HTML template without branding
- No franchise discovery or selection UI

**Implementation Requirements**:

```python
class FranchiseDocBuilder:
    def __init__(self, franchise_base_path: Path):
        self.franchise_base = franchise_base_path
        self.discovered_franchises = self._discover_all_franchises()
        self.purfect_labs_branding = self._load_branding_config()
        
    def _discover_all_franchises(self) -> Dict[str, Dict]:
        """Auto-discover all franchise directories and their documentation"""
        franchises = {}
        
        for franchise_dir in self.franchise_base.glob("*/"):
            if franchise_dir.name in ['docs', '__pycache__']:
                continue
                
            agents_dir = franchise_dir / "agents"
            docs_dir = franchise_dir / "docs"
            
            if agents_dir.exists():
                agent_files = list(agents_dir.glob("*.json"))
                
                franchises[franchise_dir.name] = {
                    'name': franchise_dir.name,
                    'display_name': franchise_dir.name.title(),
                    'path': franchise_dir,
                    'agents_dir': agents_dir,
                    'docs_dir': docs_dir,
                    'agent_count': len(agent_files),
                    'has_schema': (docs_dir / "warpcore_agent_flow_schema.json").exists(),
                    'has_mermaid': (docs_dir / "warpcore_agent_flow.mermaid").exists(),
                    'schema_path': docs_dir / "warpcore_agent_flow_schema.json",
                    'mermaid_path': docs_dir / "warpcore_agent_flow.mermaid"
                }
        
        return franchises
    
    def generate_multi_franchise_documentation(self) -> str:
        """Generate unified HTML with franchise tabs and Purfect Labs branding"""
        franchise_tabs = self._generate_franchise_tabs()
        franchise_content = self._generate_franchise_content()
        
        return self._build_purfect_labs_template(
            franchise_tabs=franchise_tabs,
            franchise_content=franchise_content
        )
```

**UI Requirements**:

1. **Purfect Labs Branded Header**:
   ```html
   <div class="purfect-header">
       <div class="purfect-logo">Purfect Labs</div>
       <div class="purfect-tagline">UR DevOps. Purfectly Simplified.</div>
       <div class="purfect-subtitle">WARPCORE Agent System Documentation</div>
   </div>
   ```

2. **Franchise Selector Interface**:
   ```html
   <div class="franchise-selector">
       <div class="franchise-tabs">
           <button class="franchise-tab active" data-franchise="staff">
               🏢 Staff Franchise
               <span class="agent-count">11 agents</span>
           </button>
           <button class="franchise-tab" data-franchise="framer">
               🎨 Framer Franchise
               <span class="agent-count">11 agents</span>
           </button>
       </div>
   </div>
   ```

3. **Per-Franchise Mermaid Rendering**:
   ```html
   <div id="staff-franchise" class="franchise-content active">
       <div class="franchise-header">
           <h2>🏢 Staff Franchise - DevOps Automation</h2>
           <p>Intelligent workflow automation for development operations</p>
       </div>
       <div class="mermaid-container">
           <div class="mermaid">
               <!-- Staff franchise mermaid content -->
           </div>
       </div>
   </div>
   
   <div id="framer-franchise" class="franchise-content">
       <div class="franchise-header">
           <h2>🎨 Framer Franchise - Content Intelligence</h2>
           <p>AI-powered content creation and data analysis</p>
       </div>
       <div class="mermaid-container">
           <div class="mermaid">
               <!-- Framer franchise mermaid content -->
           </div>
       </div>
   </div>
   ```

**Color Scheme & Branding** (matching purfectlabs.com):

```css
:root {
    /* Purfect Labs Purple/Blue Theme */
    --purfect-primary: #8b5cf6;    /* Purple */
    --purfect-secondary: #3b82f6;  /* Blue */
    --purfect-accent: #06b6d4;     /* Cyan */
    --purfect-dark: #0f172a;       /* Dark navy */
    --purfect-gradient: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 50%, #06b6d4 100%);
}

.purfect-header {
    background: var(--purfect-gradient);
    padding: 40px;
    text-align: center;
    border-radius: 16px;
    margin-bottom: 30px;
}

.purfect-logo {
    font-size: 2.5rem;
    font-weight: 800;
    color: white;
    text-shadow: 0 0 30px rgba(255, 255, 255, 0.3);
}

.purfect-tagline {
    font-size: 1.2rem;
    color: rgba(255, 255, 255, 0.9);
    margin: 10px 0;
    font-weight: 600;
}

.franchise-tab {
    background: var(--purfect-gradient);
    border: none;
    color: white;
    padding: 16px 24px;
    border-radius: 12px;
    margin: 0 8px;
    cursor: pointer;
    transition: all 0.3s ease;
}

.franchise-tab:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(139, 92, 246, 0.3);
}
```

**CLI Enhancement**:

```python
# Update agency.py to support multi-franchise docs
parser.add_argument('--all-franchises', 
                   action='store_true',
                   help='Generate documentation for all franchises')

def handle_docs_command(args):
    if args.all_franchises:
        builder = FranchiseDocBuilder(self.base_path / "agents" / "franchise")
        output_file = builder.generate_multi_franchise_documentation()
        print(f"🌐 Multi-franchise documentation: file://{output_file}")
    else:
        # Single franchise mode (existing behavior)
        generator = AgentFlowGenerator(agents_dir=args.agents_dir)
        output_file = generator.build_documentation(args.output)
```

**Key Features**:
1. **Auto-Discovery**: Scans `/franchise/` directory for all franchises
2. **Unified UI**: Single HTML with tabbed interface for each franchise
3. **Purfect Labs Branding**: Professional branding matching website
4. **Mermaid Integration**: Per-franchise diagram rendering
5. **Responsive Design**: Mobile-friendly interface
6. **Extensible**: Easy to add new franchises as they're created

**Output Structure**:
```
src/agency/agents/franchise/docs/
├── multi_franchise_docs.html      # Combined documentation
├── flow_generator.py              # Enhanced with FranchiseDocBuilder
└── purfect_labs_branding.css      # Branding styles
```

---

## 7. Integration Testing Requirements

### File: `src/agency/tests/test_franchise_integration.py` (NEW FILE)
**Requirements**: Comprehensive franchise integration testing

**Implementation Requirements**:

```python
class TestFranchiseIntegration:
    def test_staff_franchise_agent_discovery(self):
        """Test that staff franchise agents are discovered correctly"""
        discovery = AgentDiscovery(base_path, "staff")
        agents = discovery.list_all_agents()
        
        expected_agents = [
            'origin', 'boss', 'pathfinder', 'oracle', 'architect', 
            'enforcer', 'craftsman', 'craftbuddy', 'gatekeeper', 
            'mama_bear', 'harmony'
        ]
        
        for agent in expected_agents:
            assert agent in agents, f"Staff agent {agent} not found"
    
    def test_staff_franchise_cache_isolation(self):
        """Test that staff franchise cache is properly isolated"""
        cache_manager = CacheManager(primary_cache, secondary_cache, "staff")
        
        # Test cache path generation
        cache_path = cache_manager.get_cache_path("wf_test", "tr_test", "pathfinder")
        assert "/franchise/staff/" in cache_path
        
        # Test cache write isolation
        test_data = {"test": "data"}
        success = cache_manager.enforce_dual_cache_write("wf_test", "tr_test", "pathfinder", test_data)
        assert success
        
        # Verify files exist in franchise-specific directories
        assert (primary_cache / "franchise" / "staff").exists()
        assert (secondary_cache / "franchise" / "staff").exists()
    
    def test_staff_franchise_context_injection(self):
        """Test that staff context is properly injected"""
        injector = FranchiseContextInjector("staff")
        
        test_spec = {"prompt": "Original prompt content"}
        enhanced = injector.inject_context(test_spec, agent_id="pathfinder", agent_role="Schema Reconciler")
        
        assert "STAFF FRANCHISE CONTEXT" in enhanced["prompt"]
        assert "Software Development Focus" in enhanced["prompt"]
        assert "Original prompt content" in enhanced["prompt"]
    
    def test_cli_franchise_integration(self):
        """Test CLI franchise parameter integration"""
        # Test default behavior (backward compatibility)
        agency = WARPCOREAgency()
        assert agency.franchise == "staff"
        
        # Test explicit franchise selection  
        agency_staff = WARPCOREAgency(franchise="staff")
        assert agency_staff.franchise == "staff"
        
        # Test agent discovery integration
        agents = agency_staff.list_available_agents()
        assert len(agents) > 0
```

**Testing Strategy**:
1. **Unit Tests**: Each component tested individually
2. **Integration Tests**: Full franchise workflow testing
3. **Backward Compatibility**: Ensure existing functionality preserved
4. **Cache Isolation**: Verify no cross-contamination
5. **Context Injection**: Validate franchise-specific contexts
6. **CLI Integration**: Test command-line franchise selection

---

## 8. Migration and Backward Compatibility

### Requirements Summary:
1. **Zero Breaking Changes**: All existing commands work identically
2. **Default Behavior**: Staff franchise is default, no behavior change
3. **Gradual Migration**: New franchise features are opt-in
4. **Error Handling**: Clear messages for franchise-related issues

### Migration Steps:
1. **Phase 1**: Update utils classes with franchise parameters (default="staff")
2. **Phase 2**: Update CLI with optional --franchise parameter
3. **Phase 3**: Add context injection system
4. **Phase 4**: Implement cache isolation
5. **Phase 5**: Add comprehensive testing

---

## 9. File Modification Summary

### Files to Modify:
1. **`src/agency/agency.py`** - Add franchise CLI support, remove hardcoded aliases
2. **`src/agency/utils/agent_discovery.py`** - Add franchise awareness 
3. **`src/agency/utils/agency_composition.py`** - Pass franchise through layers
4. **`src/agency/utils/cache_manager.py`** - Add franchise cache isolation
5. **`src/agency/utils/agent_executor.py`** - Integrate context injection

### Files to Create:
1. **`src/agency/utils/context_injector.py`** - Franchise context injection system
2. **`src/agency/tests/test_franchise_integration.py`** - Comprehensive testing
3. **`src/agency/agents/franchise/docs/purfect_labs_branding.css`** - Purfect Labs branding styles

### Files to Enhance:
1. **`src/agency/agents/franchise/docs/flow_generator.py`** - Add FranchiseDocBuilder class for multi-franchise support

### Files to NOT Touch:
- **ALL staff agent files** - `/src/agency/agents/franchise/staff/agents/*.json`
- **Staff directory structure** - Perfect as is
- **Agent schemas and prompts** - No modifications needed

---

## 10. Success Criteria

### ✅ Implementation Success Indicators:
1. **Backward Compatibility**: All existing `python agency.py` commands work identically
2. **Franchise Selection**: `python agency.py --franchise staff oracle` works correctly  
3. **Agent Discovery**: Staff agents discovered from franchise directory structure
4. **Cache Isolation**: Staff workflows cache to `.data/franchise/staff/`
5. **Context Injection**: Staff agents receive appropriate context headers
6. **Error Handling**: Clear messages for franchise and agent resolution issues
7. **Testing**: All franchise integration tests pass
8. **Documentation**: Implementation matches all 3 franchise specifications
9. **Multi-Franchise Docs**: `python agency.py docs --all-franchises` generates Purfect Labs branded documentation with Staff and Framer franchise tabs

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

# Test multi-franchise documentation with Purfect Labs branding
python agency.py docs --all-franchises
open src/agency/agents/franchise/docs/multi_franchise_docs.html
```

---

## Implementation Priority

### 🚀 Phase 1 (Core Infrastructure)
1. Update AgentDiscovery with franchise awareness
2. Update agency_composition to pass franchise parameter
3. Modify agency.py CLI to accept --franchise parameter

### 🔧 Phase 2 (Enhancement Features)  
1. Implement CacheManager franchise isolation
2. Create FranchiseContextInjector system
3. Update AgentExecutor with context injection

### 🧪 Phase 3 (Testing & Validation)
1. Create comprehensive test suite
2. Validate backward compatibility
3. Test franchise integration end-to-end

### 📋 Phase 4 (Documentation & Polish)
1. Update CLI help system
2. Add error handling improvements  
3. Final testing and validation

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