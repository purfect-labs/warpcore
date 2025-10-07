#!/usr/bin/env python3
"""
WARPCORE Workflow Logger
Centralized logging system for all agent interactions, decisions, and outputs
"""

import json
import time
import os
from datetime import datetime
from pathlib import Path

class WARPCOREWorkflowLogger:
    def __init__(self, data_dir=".data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.log_file = self.data_dir / "workflow_execution.jsonl"
        
    def log_agent_action(self, workflow_id, sequence_id, agent_name, action_type, content, motive, metadata=None):
        """
        Log any agent action, decision, or output
        
        Args:
            workflow_id: Unique workflow identifier (wf_xxxxx)
            sequence_id: Agent sequence (seq_001, seq_002, etc.)
            agent_name: Name of the agent performing action
            action_type: Type of action (PLANNING, EXECUTING, OUTPUT, HANDOFF, DECISION)
            content: The actual content/data being logged
            motive: Why this action is being taken
            metadata: Additional context data
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "workflow_id": workflow_id,
            "sequence_id": sequence_id,
            "agent_name": agent_name,
            "action_type": action_type,
            "content": content,
            "motive": motive,
            "metadata": metadata or {},
            "log_level": "INFO"
        }
        
        # Append to JSONL file (one JSON object per line)
        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def log_planning(self, workflow_id, sequence_id, agent_name, plan_content, reasoning):
        """Log agent planning phase"""
        self.log_agent_action(
            workflow_id=workflow_id,
            sequence_id=sequence_id,
            agent_name=agent_name,
            action_type="PLANNING",
            content=plan_content,
            motive=f"Agent planning phase: {reasoning}",
            metadata={"phase": "planning", "step_type": "preparation"}
        )
    
    def log_execution(self, workflow_id, sequence_id, agent_name, execution_content, purpose):
        """Log agent execution phase"""
        self.log_agent_action(
            workflow_id=workflow_id,
            sequence_id=sequence_id,
            agent_name=agent_name,
            action_type="EXECUTING",
            content=execution_content,
            motive=f"Executing agent task: {purpose}",
            metadata={"phase": "execution", "step_type": "implementation"}
        )
    
    def log_output(self, workflow_id, sequence_id, agent_name, output_data, purpose):
        """Log agent output generation"""
        self.log_agent_action(
            workflow_id=workflow_id,
            sequence_id=sequence_id,
            agent_name=agent_name,
            action_type="OUTPUT",
            content=output_data,
            motive=f"Generating output for: {purpose}",
            metadata={"phase": "output", "step_type": "result_generation"}
        )
    
    def log_handoff(self, workflow_id, sequence_id, from_agent, to_agent, handoff_data, reason):
        """Log agent-to-agent handoff"""
        self.log_agent_action(
            workflow_id=workflow_id,
            sequence_id=sequence_id,
            agent_name=f"{from_agent}_to_{to_agent}",
            action_type="HANDOFF",
            content=handoff_data,
            motive=f"Handoff from {from_agent} to {to_agent}: {reason}",
            metadata={
                "phase": "handoff",
                "from_agent": from_agent,
                "to_agent": to_agent,
                "step_type": "agent_transition"
            }
        )
    
    def log_decision(self, workflow_id, sequence_id, agent_name, decision_content, rationale, alternatives=None):
        """Log agent decision making"""
        self.log_agent_action(
            workflow_id=workflow_id,
            sequence_id=sequence_id,
            agent_name=agent_name,
            action_type="DECISION",
            content=decision_content,
            motive=f"Agent decision: {rationale}",
            metadata={
                "phase": "decision",
                "alternatives_considered": alternatives or [],
                "step_type": "decision_making"
            }
        )
    
    def log_error(self, workflow_id, sequence_id, agent_name, error_content, context):
        """Log agent errors or issues"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "workflow_id": workflow_id,
            "sequence_id": sequence_id,
            "agent_name": agent_name,
            "action_type": "ERROR",
            "content": error_content,
            "motive": f"Error encountered: {context}",
            "metadata": {"phase": "error", "step_type": "error_handling"},
            "log_level": "ERROR"
        }
        
        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def get_workflow_logs(self, workflow_id):
        """Retrieve all logs for a specific workflow"""
        logs = []
        if self.log_file.exists():
            with open(self.log_file, "r") as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        if log_entry.get("workflow_id") == workflow_id:
                            logs.append(log_entry)
                    except json.JSONDecodeError:
                        continue
        return logs
    
    def get_agent_logs(self, agent_name, limit=100):
        """Retrieve recent logs for a specific agent"""
        logs = []
        if self.log_file.exists():
            with open(self.log_file, "r") as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        if log_entry.get("agent_name") == agent_name:
                            logs.append(log_entry)
                            if len(logs) >= limit:
                                break
                    except json.JSONDecodeError:
                        continue
        return logs[-limit:] if logs else []
    
    def export_workflow_summary(self, workflow_id, output_file=None):
        """Export a complete workflow execution summary"""
        logs = self.get_workflow_logs(workflow_id)
        
        summary = {
            "workflow_id": workflow_id,
            "export_timestamp": datetime.utcnow().isoformat() + "Z",
            "total_log_entries": len(logs),
            "agents_involved": list(set(log.get("agent_name", "") for log in logs)),
            "execution_timeline": logs,
            "action_types_summary": {}
        }
        
        # Count action types
        for log in logs:
            action_type = log.get("action_type", "UNKNOWN")
            summary["action_types_summary"][action_type] = summary["action_types_summary"].get(action_type, 0) + 1
        
        # Save summary
        if not output_file:
            output_file = self.data_dir / f"{workflow_id}_execution_summary.json"
        
        with open(output_file, "w") as f:
            json.dump(summary, f, indent=2)
        
        return summary


# Usage functions for agents to call directly
def init_logger():
    """Initialize logger instance"""
    return WARPCOREWorkflowLogger()

def log_agent_planning(workflow_id, sequence_id, agent_name, plan, reasoning):
    """Helper function for agents to log planning"""
    logger = init_logger()
    logger.log_planning(workflow_id, sequence_id, agent_name, plan, reasoning)

def log_agent_execution(workflow_id, sequence_id, agent_name, execution, purpose):
    """Helper function for agents to log execution"""
    logger = init_logger()
    logger.log_execution(workflow_id, sequence_id, agent_name, execution, purpose)

def log_agent_output(workflow_id, sequence_id, agent_name, output, purpose):
    """Helper function for agents to log output"""
    logger = init_logger()
    logger.log_output(workflow_id, sequence_id, agent_name, output, purpose)

def log_agent_handoff(workflow_id, sequence_id, from_agent, to_agent, data, reason):
    """Helper function for agents to log handoffs"""
    logger = init_logger()
    logger.log_handoff(workflow_id, sequence_id, from_agent, to_agent, data, reason)

def log_agent_decision(workflow_id, sequence_id, agent_name, decision, rationale, alternatives=None):
    """Helper function for agents to log decisions"""
    logger = init_logger()
    logger.log_decision(workflow_id, sequence_id, agent_name, decision, rationale, alternatives)

def log_agent_error(workflow_id, sequence_id, agent_name, error, context):
    """Helper function for agents to log errors"""
    logger = init_logger()
    logger.log_error(workflow_id, sequence_id, agent_name, error, context)


if __name__ == "__main__":
    # Test the logger
    logger = WARPCOREWorkflowLogger()
    
    # Example usage
    test_workflow = "wf_test123"
    test_sequence = "seq_001"
    
    logger.log_planning(test_workflow, test_sequence, "test_agent", 
                       {"plan": "analyze schemas"}, 
                       "Starting gap analysis workflow")
    
    logger.log_execution(test_workflow, test_sequence, "test_agent",
                        {"files_analyzed": 5},
                        "Performing schema analysis")
    
    logger.log_output(test_workflow, test_sequence, "test_agent",
                     {"issues_found": 3},
                     "Generating analysis results")
    
    print("Logger test completed. Check .data/workflow_execution.jsonl")