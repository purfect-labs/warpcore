# WARPCORE Franchise Integration Specification

## Executive Summary

The WARPCORE Agency system's franchise architecture enables seamless integration between different agent collections while maintaining clear separation of concerns. This specification defines how Staff (software development) and Framer (intelligence & content creation) franchises integrate, share resources, and maintain compatibility within a unified system architecture.

## Integration Architecture Overview

### Core Integration Principles
- **Unified CLI Interface**: Single command structure works across all franchises
- **Shared Infrastructure**: Common caching, logging, and execution systems
- **Franchise Isolation**: Clear boundaries prevent cross-contamination
- **Resource Sharing**: Common utilities and configurations
- **Seamless Switching**: Users can switch franchises without learning new interfaces

### System Architecture Layers
```
┌─────────────────────────────────────────────────────────────┐
│                    CLI Interface Layer                      │
│  python agency.py [--franchise staff|framer] [agent] [args]│
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                 Franchise Router Layer                     │
│  - Franchise Discovery & Validation                        │
│  - Agent Path Resolution                                    │
│  - Context Header Selection                                 │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                Agent Discovery Layer                        │
│  Staff: agents/franchise/staff/                             │
│  Framer: agents/franchise/framer/agents/                    │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│               Context Injection Layer                       │
│  Staff: Software Development Context                        │
│  Framer: Intelligence Collection Context                    │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                Agent Execution Layer                        │
│  - Prompt Enhancement                                       │
│  - User Input Integration                                   │
│  - Asset Directive Injection                               │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│               Franchise Cache Layer                         │
│  Primary: .data/franchise/[staff|framer]/                   │
│  Secondary: src/agency/.data/franchise/[staff|framer]/      │
└─────────────────────────────────────────────────────────────┘
```

## Franchise Router Implementation

### 1. Franchise Discovery and Validation
```python
class FranchiseRouter:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.franchise_base = base_path / "agents" / "franchise"
        self.available_franchises = self._discover_franchises()
        
    def _discover_franchises(self) -> Dict[str, FranchiseInfo]:
        franchises = {}
        
        if not self.franchise_base.exists():
            raise FranchiseSystemError("Franchise directory not found")
            
        for franchise_dir in self.franchise_base.iterdir():
            if not franchise_dir.is_dir() or franchise_dir.name.startswith('.'):
                continue
                
            franchise_name = franchise_dir.name
            franchise_info = self._analyze_franchise(franchise_dir)
            franchises[franchise_name] = franchise_info
            
        return franchises
    
    def _analyze_franchise(self, franchise_dir: Path) -> FranchiseInfo:
        info = FranchiseInfo(
            name=franchise_dir.name,
            path=franchise_dir,
            agents_path=self._resolve_agents_path(franchise_dir),
            docs_path=self._resolve_docs_path(franchise_dir),
            schema_path=self._resolve_schema_path(franchise_dir),
            context_type=self._determine_context_type(franchise_dir.name)
        )
        
        # Validate franchise structure
        info.agent_count = len(list(info.agents_path.glob("*.json"))) if info.agents_path.exists() else 0
        info.has_schema = info.schema_path.exists() if info.schema_path else False
        info.valid = info.agent_count > 0
        
        return info
    
    def _resolve_agents_path(self, franchise_dir: Path) -> Path:
        # Staff franchise: agents directly in franchise directory
        if franchise_dir.name == "staff":
            return franchise_dir
        # Other franchises: agents in subdirectory
        else:
            return franchise_dir / "agents"
    
    def _resolve_docs_path(self, franchise_dir: Path) -> Optional[Path]:
        if (franchise_dir / "docs").exists():
            return franchise_dir / "docs"
        return None
    
    def _resolve_schema_path(self, franchise_dir: Path) -> Optional[Path]:
        schema_paths = [
            franchise_dir / "docs" / "warpcore_agent_flow_schema.json",
            self.franchise_base / "docs" / "warpcore_agent_flow_schema.json"
        ]
        
        for path in schema_paths:
            if path.exists():
                return path
        return None
    
    def _determine_context_type(self, franchise_name: str) -> str:
        context_mapping = {
            "staff": "software_development",
            "framer": "intelligence_collection",
            "marketing": "marketing_campaigns",
            "sales": "sales_processes"
        }
        return context_mapping.get(franchise_name, "general_purpose")
```

### 2. Agent Resolution System
```python
class AgentResolver:
    def __init__(self, franchise_router: FranchiseRouter):
        self.router = franchise_router
        
    def resolve_agent(self, franchise: str, agent_alias: str) -> ResolvedAgent:
        # Validate franchise exists
        if franchise not in self.router.available_franchises:
            available = list(self.router.available_franchises.keys())
            raise FranchiseNotFoundError(
                f"Franchise '{franchise}' not found. Available: {available}"
            )
        
        franchise_info = self.router.available_franchises[franchise]
        
        # Search for agent in franchise
        agent_files = list(franchise_info.agents_path.glob(f"*{agent_alias}*.json"))
        
        if not agent_files:
            available_agents = self._get_available_agents(franchise)
            raise AgentNotFoundError(
                f"Agent '{agent_alias}' not found in '{franchise}' franchise.\n"
                f"Available agents: {', '.join(available_agents)}"
            )
        
        # Load agent specification
        agent_file = agent_files[0]
        try:
            with open(agent_file, 'r') as f:
                agent_spec = json.load(f)
        except Exception as e:
            raise AgentLoadError(f"Failed to load agent {agent_file}: {e}")
        
        return ResolvedAgent(
            franchise=franchise,
            alias=agent_alias,
            file_path=agent_file,
            spec=agent_spec,
            franchise_info=franchise_info
        )
    
    def _get_available_agents(self, franchise: str) -> List[str]:
        franchise_info = self.router.available_franchises[franchise]
        agent_files = list(franchise_info.agents_path.glob("*.json"))
        
        agents = []
        for agent_file in agent_files:
            if agent_file.name.startswith('__'):
                continue
            
            # Extract agent alias from filename
            try:
                with open(agent_file, 'r') as f:
                    spec = json.load(f)
                agent_id = spec.get('agent_id', agent_file.stem)
                agents.append(agent_id)
            except:
                # Fallback to filename parsing
                agents.append(self._extract_alias_from_filename(agent_file.stem))
        
        return sorted(agents)
    
    def _extract_alias_from_filename(self, filename: str) -> str:
        # Extract from patterns like "1b_oracle_from_user_to_architect"
        parts = filename.split('_')
        if len(parts) >= 2:
            return parts[1]  # Return "oracle" from "1b_oracle_..."
        return filename
```

## Context Integration System

### 1. Franchise-Specific Context Headers
```python
class ContextIntegrator:
    def __init__(self):
        self.context_generators = {
            "software_development": self._generate_staff_context,
            "intelligence_collection": self._generate_framer_context,
            "marketing_campaigns": self._generate_marketing_context,
            "sales_processes": self._generate_sales_context
        }
    
    def generate_context_header(self, franchise_info: FranchiseInfo, 
                               client_dir: Path, agent_spec: Dict[str, Any]) -> str:
        context_type = franchise_info.context_type
        generator = self.context_generators.get(context_type, self._generate_default_context)
        
        return generator(franchise_info, client_dir, agent_spec)
    
    def _generate_staff_context(self, franchise_info: FranchiseInfo, 
                               client_dir: Path, agent_spec: Dict[str, Any]) -> str:
        return f'''
## STAFF FRANCHISE CONTEXT (SOFTWARE DEVELOPMENT)

**Current Working Directory**: {client_dir}
**Platform**: Cross-platform compatible
**Shell**: System default shell
**Python**: Available system Python
**Franchise**: Staff (Software Development Focus)
**Agent**: {agent_spec.get('agent_id', 'unknown')}

### PROJECT STRUCTURE
```
{client_dir}/
├── .data/franchise/staff/     # Staff workflow cache and results
├── .config/                   # Configuration files
├── src/agency/                # Agency system
│   └── agents/franchise/staff/# Staff agent specifications
├── src/api/                   # PAP architecture implementation
│   ├── controllers/          # Business logic controllers
│   ├── providers/            # Data/service providers
│   └── orchestrators/        # Workflow orchestrators
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
    
    def _generate_framer_context(self, franchise_info: FranchiseInfo,
                                client_dir: Path, agent_spec: Dict[str, Any]) -> str:
        return f'''
## FRAMER FRANCHISE CONTEXT (INTELLIGENCE & CONTENT CREATION)

**Current Working Directory**: {client_dir}
**Platform**: Cross-platform compatible
**Shell**: System default shell
**Python**: Available system Python
**Franchise**: Framer (Intelligence Collection & Content Creation Focus)
**Agent**: {agent_spec.get('agent_id', 'unknown')}

### PROJECT STRUCTURE
```
{client_dir}/
├── .data/franchise/framer/    # Framer workflow cache and results
├── intelligence/              # Intelligence collection workspace
│   ├── sources/              # Data source configurations
│   ├── raw/                  # Raw collected data
│   ├── processed/            # Processed intelligence
│   └── reports/              # Intelligence reports
├── content/                   # Content creation workspace
│   ├── drafts/               # Content drafts
│   ├── assets/               # Media assets
│   └── published/            # Published content
└── src/agency/                # Agency system
    └── agents/franchise/framer/# Framer agent specifications
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

### 2. Universal Asset Directive Integration
```python
class AssetDirectiveIntegrator:
    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
    
    def inject_franchise_asset_directive(self, agent_spec: Dict[str, Any], 
                                       franchise: str) -> Dict[str, Any]:
        base_directive = self.cache_manager.get_shared_asset_directive()
        franchise_directive = self._get_franchise_specific_directive(franchise)
        
        enhanced_spec = agent_spec.copy()
        original_prompt = enhanced_spec.get('prompt', '')
        
        combined_directive = f"{base_directive}\n\n{franchise_directive}"
        enhanced_spec['prompt'] = f"{combined_directive}\n\n{original_prompt}"
        
        return enhanced_spec
    
    def _get_franchise_specific_directive(self, franchise: str) -> str:
        if franchise == "staff":
            return '''
### STAFF FRANCHISE ASSET MANAGEMENT
Store development-related assets in franchise-specific directories:
- Code samples and patches: `assets/code/`
- Test results and reports: `assets/testing/`
- Documentation artifacts: `assets/docs/`
- Configuration files: `assets/config/`
'''
        elif franchise == "framer":
            return '''
### FRAMER FRANCHISE ASSET MANAGEMENT
Store intelligence and content assets in franchise-specific directories:
- Collected data and intelligence: `assets/intelligence/`
- Generated content and drafts: `assets/content/`
- Media files and visualizations: `assets/media/`
- Research reports and analysis: `assets/reports/`
'''
        else:
            return "### FRANCHISE ASSET MANAGEMENT\nStore franchise-specific assets appropriately."
```

## Cross-Franchise Compatibility

### 1. Shared Resource Management
```python
class SharedResourceManager:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.shared_configs = base_path / ".config"
        self.shared_cache = base_path / ".data" / "shared"
        
    def get_shared_configuration(self, config_name: str) -> Optional[Dict[str, Any]]:
        config_file = self.shared_configs / f"{config_name}.json"
        if config_file.exists():
            with open(config_file, 'r') as f:
                return json.load(f)
        return None
    
    def get_cross_franchise_insights(self) -> Dict[str, Any]:
        """Get insights that might be useful across franchises"""
        insights = {
            "workflow_patterns": self._analyze_workflow_patterns(),
            "common_user_intents": self._identify_common_user_intents(),
            "shared_data_sources": self._discover_shared_data_sources(),
            "cross_pollination_opportunities": self._find_cross_pollination_opportunities()
        }
        return insights
    
    def _analyze_workflow_patterns(self) -> Dict[str, Any]:
        """Analyze common patterns across franchise workflows"""
        return {
            "successful_workflows": "workflows that consistently produce good results",
            "common_failure_points": "where workflows tend to fail across franchises",
            "optimization_opportunities": "areas for improvement in workflow design"
        }
    
    def _identify_common_user_intents(self) -> List[str]:
        """Identify user intents that span multiple franchises"""
        return [
            "research_and_analysis",
            "content_creation",
            "problem_solving",
            "optimization_and_improvement"
        ]
```

### 2. Franchise Communication Protocols
```python
class FranchiseCommunication:
    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
        
    def enable_cross_franchise_workflow(self, source_franchise: str, 
                                      target_franchise: str, 
                                      workflow_id: str) -> bool:
        """Enable workflow to pass data from one franchise to another"""
        try:
            # Create cross-franchise communication record
            communication_record = {
                "source_franchise": source_franchise,
                "target_franchise": target_franchise,
                "workflow_id": workflow_id,
                "timestamp": datetime.now().isoformat(),
                "status": "initiated"
            }
            
            # Store in shared cache area
            comm_file = f"cross_franchise_{workflow_id}.json"
            self.cache_manager.write_shared_cache(comm_file, communication_record)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to enable cross-franchise communication: {e}")
            return False
    
    def transfer_workflow_data(self, workflow_id: str, 
                             data: Dict[str, Any],
                             from_franchise: str,
                             to_franchise: str) -> bool:
        """Transfer data from one franchise workflow to another"""
        try:
            transfer_record = {
                "workflow_id": workflow_id,
                "data": data,
                "from_franchise": from_franchise,
                "to_franchise": to_franchise,
                "timestamp": datetime.now().isoformat()
            }
            
            transfer_file = f"transfer_{workflow_id}_{from_franchise}_to_{to_franchise}.json"
            self.cache_manager.write_shared_cache(transfer_file, transfer_record)
            
            # Notify target franchise
            self._notify_target_franchise(to_franchise, transfer_record)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to transfer workflow data: {e}")
            return False
```

## Cache Integration Architecture

### 1. Franchise-Isolated Cache System
```python
class FranchiseCacheIntegration:
    def __init__(self, primary_cache: Path, secondary_cache: Path):
        self.primary_cache = primary_cache
        self.secondary_cache = secondary_cache
        
    def get_franchise_cache_structure(self) -> Dict[str, Path]:
        return {
            "staff_primary": self.primary_cache / "franchise" / "staff",
            "staff_secondary": self.secondary_cache / "franchise" / "staff",
            "framer_primary": self.primary_cache / "franchise" / "framer",
            "framer_secondary": self.secondary_cache / "franchise" / "framer",
            "shared_primary": self.primary_cache / "shared",
            "shared_secondary": self.secondary_cache / "shared"
        }
    
    def ensure_franchise_cache_structure(self):
        """Ensure all franchise cache directories exist"""
        cache_structure = self.get_franchise_cache_structure()
        
        for cache_type, cache_path in cache_structure.items():
            cache_path.mkdir(parents=True, exist_ok=True)
            
            # Create franchise-specific subdirectories
            if "staff" in cache_type or "framer" in cache_type:
                (cache_path / "workflows").mkdir(exist_ok=True)
                (cache_path / "assets").mkdir(exist_ok=True)
                (cache_path / "traces").mkdir(exist_ok=True)
    
    def write_franchise_cache(self, franchise: str, workflow_id: str, 
                            trace_id: str, agent_name: str, 
                            data: Dict[str, Any]) -> bool:
        """Write to franchise-specific cache"""
        cache_structure = self.get_franchise_cache_structure()
        
        primary_path = cache_structure[f"{franchise}_primary"]
        secondary_path = cache_structure[f"{franchise}_secondary"]
        
        filename = f"{workflow_id}_{trace_id}_{agent_name}.json"
        
        try:
            # Write to both primary and secondary caches
            with open(primary_path / filename, 'w') as f:
                json.dump(data, f, indent=2)
                
            with open(secondary_path / filename, 'w') as f:
                json.dump(data, f, indent=2)
                
            print(f"✅ FRANCHISE CACHE ({franchise}): {filename}")
            return True
            
        except Exception as e:
            print(f"❌ FRANCHISE CACHE WRITE FAILED: {e}")
            return False
```

### 2. Cross-Franchise Cache Analytics
```python
class FranchiseCacheAnalytics:
    def __init__(self, cache_integration: FranchiseCacheIntegration):
        self.cache = cache_integration
        
    def analyze_franchise_usage(self) -> Dict[str, Any]:
        """Analyze usage patterns across franchises"""
        cache_structure = self.cache.get_franchise_cache_structure()
        
        analysis = {}
        
        for franchise in ["staff", "framer"]:
            primary_path = cache_structure[f"{franchise}_primary"]
            
            if not primary_path.exists():
                continue
                
            cache_files = list(primary_path.glob("*.json"))
            
            analysis[franchise] = {
                "total_workflows": len(cache_files),
                "most_active_agents": self._get_most_active_agents(cache_files),
                "workflow_success_rate": self._calculate_success_rate(cache_files),
                "average_workflow_duration": self._calculate_avg_duration(cache_files),
                "storage_usage_mb": self._calculate_storage_usage(primary_path)
            }
        
        return analysis
    
    def _get_most_active_agents(self, cache_files: List[Path]) -> List[str]:
        agent_counts = {}
        
        for file in cache_files:
            # Extract agent name from filename
            parts = file.stem.split('_')
            if len(parts) >= 3:
                agent_name = parts[2]  # workflow_trace_agent pattern
                agent_counts[agent_name] = agent_counts.get(agent_name, 0) + 1
        
        return sorted(agent_counts.keys(), key=agent_counts.get, reverse=True)[:5]
    
    def generate_cross_franchise_insights(self) -> Dict[str, Any]:
        """Generate insights comparing franchise performance"""
        usage_analysis = self.analyze_franchise_usage()
        
        insights = {
            "performance_comparison": self._compare_franchise_performance(usage_analysis),
            "workflow_efficiency": self._analyze_workflow_efficiency(usage_analysis),
            "resource_utilization": self._analyze_resource_utilization(usage_analysis),
            "optimization_recommendations": self._generate_optimization_recommendations(usage_analysis)
        }
        
        return insights
```

## Integration Testing Framework

### 1. Cross-Franchise Test Suite
```python
class FranchiseIntegrationTests:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.router = FranchiseRouter(base_path)
        self.resolver = AgentResolver(self.router)
        
    def test_franchise_discovery(self) -> bool:
        """Test that all franchises are properly discovered"""
        try:
            franchises = self.router.available_franchises
            
            # Test staff franchise exists
            assert "staff" in franchises, "Staff franchise not found"
            assert franchises["staff"].valid, "Staff franchise not valid"
            
            # Test framer franchise exists  
            assert "framer" in franchises, "Framer franchise not found"
            assert franchises["framer"].valid, "Framer franchise not valid"
            
            print("✅ Franchise discovery test passed")
            return True
            
        except Exception as e:
            print(f"❌ Franchise discovery test failed: {e}")
            return False
    
    def test_agent_resolution(self) -> bool:
        """Test agent resolution across franchises"""
        test_cases = [
            ("staff", "oracle"),
            ("framer", "oracle"),
            ("framer", "ghostwriter"),
            ("framer", "alice")
        ]
        
        for franchise, agent in test_cases:
            try:
                resolved = self.resolver.resolve_agent(franchise, agent)
                assert resolved.franchise == franchise
                assert resolved.alias == agent
                assert resolved.spec is not None
                print(f"✅ Resolved {franchise}/{agent}")
                
            except Exception as e:
                print(f"❌ Failed to resolve {franchise}/{agent}: {e}")
                return False
        
        print("✅ Agent resolution test passed")
        return True
    
    def test_context_injection(self) -> bool:
        """Test franchise-specific context injection"""
        integrator = ContextIntegrator()
        
        # Test staff context
        staff_info = self.router.available_franchises["staff"]
        staff_context = integrator.generate_context_header(
            staff_info, Path("/test"), {"agent_id": "test"}
        )
        assert "SOFTWARE DEVELOPMENT" in staff_context
        assert "PAP architecture" in staff_context
        
        # Test framer context
        framer_info = self.router.available_franchises["framer"]
        framer_context = integrator.generate_context_header(
            framer_info, Path("/test"), {"agent_id": "test"}
        )
        assert "INTELLIGENCE & CONTENT CREATION" in framer_context
        assert "intelligence/" in framer_context
        
        print("✅ Context injection test passed")
        return True
    
    def run_integration_test_suite(self) -> bool:
        """Run complete integration test suite"""
        tests = [
            self.test_franchise_discovery,
            self.test_agent_resolution,
            self.test_context_injection
        ]
        
        results = []
        for test in tests:
            results.append(test())
        
        success_rate = sum(results) / len(results) * 100
        print(f"\n🧪 Integration Test Results: {success_rate:.1f}% passed")
        
        return all(results)
```

## Performance Optimization

### 1. Franchise Performance Monitoring
```python
class FranchisePerformanceMonitor:
    def __init__(self):
        self.metrics = {
            "franchise_switch_time": [],
            "agent_resolution_time": [], 
            "context_injection_time": [],
            "cache_write_time": []
        }
    
    def measure_franchise_switch(self, from_franchise: str, to_franchise: str):
        """Measure time to switch between franchises"""
        start_time = time.time()
        
        # Simulate franchise switch operations
        self._load_franchise_context(to_franchise)
        self._initialize_franchise_cache(to_franchise)
        
        switch_time = time.time() - start_time
        self.metrics["franchise_switch_time"].append(switch_time)
        
        print(f"⏱️  Franchise switch ({from_franchise} → {to_franchise}): {switch_time:.3f}s")
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate performance analysis report"""
        report = {}
        
        for metric_name, values in self.metrics.items():
            if values:
                report[metric_name] = {
                    "average": statistics.mean(values),
                    "median": statistics.median(values),
                    "max": max(values),
                    "min": min(values),
                    "count": len(values)
                }
        
        return report
```

This comprehensive integration specification ensures that the WARPCORE franchise system maintains perfect compatibility while enabling powerful domain-specific agent architectures. The system provides seamless switching between franchises while maintaining clear isolation and optimal performance.