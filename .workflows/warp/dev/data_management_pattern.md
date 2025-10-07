# WARPCORE Data Management Pattern

## 📦 **Compression & Git Strategy**

### **Directory Structure**
```
.data/
├── compressed/           # Committed to git - shared workflow summaries
├── full/                # Gitignored - complete local workflow data  
├── archive/             # Gitignored - old workflows
└── current/             # Gitignored - active workflow working files
```

### **File Naming Conventions**
```bash
# Compressed (Committed)
.data/compressed/wf_summary_{workflow_id}.json.gz
.data/compressed/agent_metrics_{date}.json.gz

# Full Local (Gitignored) 
.data/full/wf_{workflow_id}_{agent_name}_complete.json
.data/full/wf_{workflow_id}_full_results.json

# Current Working (Gitignored)
.data/current/active_workflow_state.json
.data/current/agent_handoff_cache.json

# Archive (Gitignored)
.data/archive/wf_{workflow_id}_{date}.json.gz
```

## 🔄 **Compression Workflow Pattern**

### **Agent Execution Pattern**
```python
def agent_data_management(workflow_id, agent_name, results):
    # 1. Save full results locally (gitignored)
    full_path = f".data/full/wf_{workflow_id}_{agent_name}_complete.json"
    save_json(full_path, results)
    
    # 2. Create compressed summary (for git commit)
    summary = extract_summary(results)
    compressed_path = f".data/compressed/wf_summary_{workflow_id}_{agent_name}.json.gz"
    save_compressed(compressed_path, summary)
    
    # 3. Update current state (gitignored)
    current_state = {
        "workflow_id": workflow_id,
        "last_agent": agent_name,
        "completion_time": datetime.utcnow().isoformat(),
        "full_data_path": full_path,
        "compressed_path": compressed_path
    }
    save_json(".data/current/workflow_state.json", current_state)
    
    # 4. Archive old workflows (gitignored)
    archive_old_workflows()
```

### **Summary Extraction Logic**
```python
def extract_summary(full_results):
    """Extract key metrics for compressed version"""
    return {
        "workflow_id": full_results.get("workflow_id"),
        "agent_name": full_results.get("agent_name"), 
        "timestamp": full_results.get("timestamp"),
        "execution_metrics": full_results.get("execution_metrics"),
        "performance_metrics": full_results.get("performance_metrics"),
        "data_compression": full_results.get("data_compression"),
        "bonus_contributions": full_results.get("bonus_contributions"),
        "key_outcomes": extract_key_outcomes(full_results),
        "next_agent": full_results.get("next_agent")
    }
```

## 🔒 **GitIgnore Configuration**

### **Add to .gitignore**
```gitignore
# Full workflow data (local only)
.data/full/
.data/archive/ 
.data/current/

# Keep compressed summaries (committed)
!.data/compressed/

# Temporary agent files
.data/tmp_*
.data/agent_*.tmp
```

## 🎯 **Operational Pattern**

### **Agents Always Use Full Data**
```python
# Agents read from full data
input_file = f".data/full/wf_{workflow_id}_previous_agent_complete.json"

# Agents write both versions
write_full_results(f".data/full/wf_{workflow_id}_{current_agent}_complete.json", results)
write_compressed_summary(f".data/compressed/wf_summary_{workflow_id}_{current_agent}.json.gz", results)
```

### **Git Commits Include**
- Compressed workflow summaries 
- Agent specifications
- Configuration files
- Documentation

### **Local Environment Has**
- Full detailed workflow data
- Complete agent outputs
- Debugging information
- Development cache files

## 📊 **Benefits**

- **Repository Size**: Minimal - only compressed summaries committed
- **Local Performance**: Full data available for agents and debugging
- **Sharing**: Key metrics and outcomes shared via compressed files
- **Privacy**: Detailed data stays local, summaries can be sanitized
- **Scalability**: Archive pattern prevents data accumulation

## 🔧 **Implementation Status**

- ✅ **Compression Logic**: Added to all 7 agent specifications
- ✅ **Bonus Contributions**: Consistent tracking across all agents  
- 🔄 **Directory Structure**: Ready to implement
- 🔄 **GitIgnore Rules**: Ready to add
- 🔄 **Agent Updates**: Ready to modify for full/compressed pattern

**This pattern provides efficient data management with full local capability and minimal repository overhead.**