#!/usr/bin/env python3
"""
WARPCORE Mock Data Generator
Creates comprehensive realistic data for dashboard testing with 10+ workflow runs
"""

import json
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import os

class WARPCOREMockDataGenerator:
    def __init__(self, data_dir="../.data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Create realistic progression over time
        self.base_timestamp = datetime.now() - timedelta(days=30)
        self.workflow_runs = []
        
        # Mock realistic project data
        self.project_files = ["src/api/auth.py", "src/web/templates.py", "src/data/config.py", 
                             "tests/test_auth.py", "docs/api.md", "requirements.txt"]
        self.issues_pool = [
            "AWS S3 provider needs GCP conversion",
            "Template manager has DEMO watermarks", 
            "Security middleware incomplete",
            "PAP interface inconsistency",
            "Fake license keys in config",
            "Demo project names hardcoded",
            "AWS auth references remaining",
            "Mock data in admin interface",
            "Incomplete validation rules",
            "Missing error handlers"
        ]
        
    def generate_workflow_id(self, run_number):
        """Generate realistic workflow ID"""
        timestamp = int((self.base_timestamp + timedelta(days=run_number)).timestamp())
        hash_input = f"warpcore_gap_analysis_{timestamp}_{run_number}"
        workflow_hash = hashlib.md5(hash_input.encode()).hexdigest()[:12]
        return f"wf_{workflow_hash}"
    
    def generate_realistic_metrics(self, run_number, agent_position):
        """Generate realistic performance metrics that show improvement over time"""
        # Base metrics that improve over time
        base_quality = 65 + (run_number * 2.5) + random.uniform(-5, 5)
        base_efficiency = 70 + (run_number * 2) + random.uniform(-4, 4)
        
        # Clamp values
        quality_score = max(60, min(98, base_quality))
        efficiency_rating = max(65, min(95, base_efficiency))
        
        # Convert to rating
        if efficiency_rating >= 90:
            rating = "EXCELLENT"
        elif efficiency_rating >= 80:
            rating = "GOOD"
        elif efficiency_rating >= 70:
            rating = "FAIR"
        else:
            rating = "POOR"
        
        return {
            "output_quality_score": round(quality_score),
            "efficiency_rating": rating,
            "efficiency_numeric": round(efficiency_rating)
        }
    
    def generate_agent_1_data(self, workflow_id, run_number):
        """Generate Agent 1 (Schema Reconciler) data"""
        timestamp = (self.base_timestamp + timedelta(days=run_number, hours=1)).isoformat() + "Z"
        metrics = self.generate_realistic_metrics(run_number, 1)
        
        # Issues decrease over time as system improves
        base_issues = max(3, 47 - (run_number * 2))
        issues_found = base_issues + random.randint(-2, 3)
        
        return {
            "workflow_id": workflow_id,
            "agent_name": "schema_coherence_reconciler_agent",
            "timestamp": timestamp,
            "execution_metrics": {
                "start_time": timestamp,
                "end_time": (datetime.fromisoformat(timestamp[:-1]) + timedelta(minutes=random.randint(8, 15))).isoformat() + "Z",
                "duration_seconds": random.randint(480, 900),
                "memory_usage_mb": random.randint(35, 65),
                "cpu_usage_percent": random.randint(15, 35)
            },
            "performance_metrics": {
                **metrics,
                "issues_identified": issues_found,
                "files_analyzed": random.randint(150, 185),
                "compliance_score": random.randint(85, 95)
            },
            "analysis_summary": {
                "total_files_analyzed": random.randint(175, 185),
                "total_lines": random.randint(44000, 48000),
                "pap_compliance_score": f"{random.randint(88, 95)}%",
                "coherence_issues_found": issues_found,
                "fake_demo_markers_total": max(50, 892 - (run_number * 35)),
                "architectural_violations_total": max(2, 23 - run_number)
            },
            "next_agent": "requirements_generator_agent",
            "next_agent_input": {
                "workflow_id": workflow_id,
                "total_issues_found": issues_found,
                "critical_issues_count": max(1, issues_found // 3),
                "cache_file": f".data/{workflow_id}_schema_coherence_analysis.json"
            }
        }
    
    def generate_agent_2_data(self, workflow_id, run_number, agent_1_data):
        """Generate Agent 2 (Requirements Generator) data"""
        timestamp = (self.base_timestamp + timedelta(days=run_number, hours=2)).isoformat() + "Z"
        metrics = self.generate_realistic_metrics(run_number, 2)
        
        issues_from_agent_1 = agent_1_data["analysis_summary"]["coherence_issues_found"]
        requirements_generated = min(30, max(5, issues_from_agent_1 + random.randint(-2, 5)))
        
        return {
            "workflow_id": workflow_id,
            "agent_name": "requirements_generator_agent", 
            "timestamp": timestamp,
            "execution_metrics": {
                "start_time": timestamp,
                "end_time": (datetime.fromisoformat(timestamp[:-1]) + timedelta(minutes=random.randint(12, 22))).isoformat() + "Z",
                "duration_seconds": random.randint(720, 1320),
                "memory_usage_mb": random.randint(45, 75),
                "cpu_usage_percent": random.randint(20, 40)
            },
            "performance_metrics": {
                **metrics,
                "requirements_generated": requirements_generated,
                "complexity_score": random.randint(70, 90),
                "dependency_accuracy": random.randint(85, 98)
            },
            "requirements_summary": {
                "total_requirements": requirements_generated,
                "total_subtasks": requirements_generated * random.randint(2, 4),
                "critical_count": max(1, requirements_generated // 4),
                "high_count": requirements_generated // 3,
                "medium_count": requirements_generated // 3,
                "low_count": requirements_generated // 6,
                "estimated_total_effort": f"{random.randint(6, 10)} weeks",
                "total_effort_hours": random.randint(240, 400)
            },
            "next_agent": "requirements_validator_agent",
            "next_agent_input": {
                "workflow_id": workflow_id,
                "total_requirements": requirements_generated,
                "cache_file": f".data/{workflow_id}_requirements_analysis.json"
            }
        }
    
    def generate_agent_3_data(self, workflow_id, run_number, agent_2_data):
        """Generate Agent 3 (Requirements Validator) data"""
        timestamp = (self.base_timestamp + timedelta(days=run_number, hours=3)).isoformat() + "Z"
        metrics = self.generate_realistic_metrics(run_number, 3)
        
        total_reqs = agent_2_data["requirements_summary"]["total_requirements"]
        approved = int(total_reqs * random.uniform(0.75, 0.95))
        revision_needed = total_reqs - approved - random.randint(0, 2)
        rejected = total_reqs - approved - revision_needed
        
        return {
            "workflow_id": workflow_id,
            "agent_name": "requirements_validator_agent",
            "timestamp": timestamp,
            "execution_metrics": {
                "start_time": timestamp,
                "end_time": (datetime.fromisoformat(timestamp[:-1]) + timedelta(minutes=random.randint(6, 12))).isoformat() + "Z",
                "duration_seconds": random.randint(360, 720),
                "memory_usage_mb": random.randint(30, 50),
                "cpu_usage_percent": random.randint(12, 25)
            },
            "performance_metrics": {
                **metrics,
                "requirements_validated": total_reqs,
                "approval_rate": round((approved / total_reqs) * 100),
                "validation_accuracy": random.randint(90, 98)
            },
            "validation_summary": {
                "requirements_validated": total_reqs,
                "pap_compliant": approved + revision_needed,
                "feasible": approved,
                "implementation_ready": approved,
                "validation_issues": revision_needed + rejected,
                "overall_status": "PASS" if approved >= (total_reqs * 0.7) else "NEEDS_REVISION"
            },
            "final_recommendations": {
                "proceed_with_implementation": approved >= (total_reqs * 0.7),
                "approved_requirements_count": approved,
                "revision_required_count": revision_needed,
                "rejected_count": rejected
            },
            "next_agent": "implementation_agent",
            "next_agent_input": {
                "workflow_id": workflow_id,
                "approved_requirements_count": approved,
                "revision_required_count": revision_needed,
                "rejected_count": rejected,
                "cache_file": f".data/{workflow_id}_requirements_validation.json",
                "implementation_focus": random.sample(self.issues_pool, min(3, len(self.issues_pool))),
                "priority_requirements": [f"REQ-{i:03d}" for i in range(1, approved + 1)]
            }
        }
    
    def generate_agent_4_data(self, workflow_id, run_number, agent_3_data):
        """Generate Agent 4 (Implementation) data with comprehensive dashboard analytics"""
        timestamp = (self.base_timestamp + timedelta(days=run_number, hours=4)).isoformat() + "Z"
        metrics = self.generate_realistic_metrics(run_number, 4)
        
        approved_reqs = agent_3_data["final_recommendations"]["approved_requirements_count"]
        implemented = int(approved_reqs * random.uniform(0.85, 1.0))
        
        # Generate comprehensive dashboard data
        completion_pct = round((run_number / 12) * 100) + random.randint(-5, 5)
        completion_pct = max(15, min(100, completion_pct))
        
        return {
            "workflow_id": workflow_id,
            "agent_name": "implementation_agent",
            "timestamp": timestamp,
            "execution_metrics": {
                "start_time": timestamp,
                "end_time": (datetime.fromisoformat(timestamp[:-1]) + timedelta(minutes=random.randint(25, 45))).isoformat() + "Z",
                "duration_seconds": random.randint(1500, 2700),
                "memory_usage_mb": random.randint(55, 95),
                "cpu_usage_percent": random.randint(30, 60)
            },
            "performance_metrics": {
                **metrics,
                "requirements_implemented": implemented,
                "implementation_success_rate": round((implemented / approved_reqs) * 100),
                "code_quality_score": random.randint(82, 96)
            },
            "implementation_summary": {
                "requirements_implemented": implemented,
                "requirements_failed": approved_reqs - implemented,
                "files_modified": random.randint(12, 25),
                "lines_changed": random.randint(450, 850),
                "tests_executed": random.randint(25, 45),
                "tests_passed": random.randint(22, 45),
                "tests_failed": random.randint(0, 3)
            },
            # COMPREHENSIVE DASHBOARD DATA
            "workflow_analytics": {
                "workflow_status": "IN_PROGRESS" if completion_pct < 100 else "COMPLETED",
                "completion_percentage": completion_pct,
                "sequences_completed": 4,
                "total_estimated_sequences": 5,
                "current_phase": "HIGH" if completion_pct < 50 else "MEDIUM",
                "agent_performance": {
                    f"seq_001_schema_reconciler": {
                        "execution_time_minutes": random.uniform(8, 15),
                        "output_quality_score": random.randint(75, 92),
                        "performance_rating": "GOOD",
                        "issues_identified": random.randint(15, 35)
                    },
                    f"seq_002_requirements_generator": {
                        "execution_time_minutes": random.uniform(12, 22),
                        "output_quality_score": random.randint(78, 94),
                        "performance_rating": "EXCELLENT",
                        "requirements_generated": approved_reqs
                    },
                    f"seq_003_requirements_validator": {
                        "execution_time_minutes": random.uniform(6, 12),
                        "output_quality_score": random.randint(85, 96),
                        "performance_rating": "EXCELLENT",
                        "enhancements_added": random.randint(5, 12)
                    },
                    f"seq_004_implementation": {
                        "execution_time_minutes": random.uniform(25, 45),
                        "output_quality_score": metrics["output_quality_score"],
                        "performance_rating": metrics["efficiency_rating"],
                        "requirements_implemented": implemented
                    }
                }
            },
            "progress_metrics": {
                "pap_compliance_score": random.randint(89, 97),
                "coherence_issues_identified": max(5, 47 - (run_number * 2)),
                "total_effort_hours_estimated": f"{random.randint(240, 400)}",
                "requirements_generated": approved_reqs,
                "requirements_validated": approved_reqs
            },
            "visualization_dashboard_data": {
                "workflow_progress_chart": {
                    "labels": ["Schema Analysis", "Requirements Gen", "Validation", "Implementation", "Gate Promote"],
                    "completion_data": [100, 100, 100, 100, 20 if completion_pct < 100 else 100],
                    "time_data": [12.5, 18.2, 8.7, 32.4, 0 if completion_pct < 100 else 15.6]
                },
                "agent_performance_radar": {
                    "agents": ["Agent 1", "Agent 2", "Agent 3", "Agent 4", "Agent 5"],
                    "metrics": [85, 92, 89, metrics["output_quality_score"], 88]
                },
                "issue_resolution_funnel": {
                    "identified": max(5, 47 - (run_number * 2)),
                    "analyzed": max(4, 35 - (run_number * 2)),
                    "resolved": max(3, 28 - (run_number * 2))
                },
                "workflow_health_metrics": {
                    "overall_health": random.randint(82, 96),
                    "velocity_trend": random.choice(["INCREASING", "STABLE", "INCREASING"]),
                    "quality_trend": random.choice(["IMPROVING", "STABLE", "IMPROVING"])
                }
            },
            "predictive_analytics": {
                "estimated_completion": {
                    "projected_completion": (datetime.fromisoformat(timestamp[:-1]) + timedelta(hours=random.randint(2, 8))).isoformat() + "Z",
                    "confidence_level": random.randint(75, 95)
                },
                "risk_indicators": [
                    {
                        "risk": "Integration complexity",
                        "probability": random.uniform(0.1, 0.4),
                        "impact": "MEDIUM",
                        "mitigation": "Incremental testing approach"
                    },
                    {
                        "risk": "Performance degradation", 
                        "probability": random.uniform(0.05, 0.2),
                        "impact": "LOW",
                        "mitigation": "Continuous monitoring"
                    }
                ]
            },
            "trending_metadata": {
                "run_sequence": run_number,
                "previous_run_comparison": {
                    "performance_change": random.uniform(-0.05, 0.15),
                    "efficiency_change": random.uniform(-0.03, 0.12),
                    "quality_improvement": random.uniform(0, 0.08)
                },
                "velocity_indicator": "FASTER" if run_number > 3 else random.choice(["FASTER", "SAME", "SLOWER"]),
                "success_rate": min(1.0, 0.6 + (run_number * 0.03))
            },
            "next_agent": "gate_promote_agent",
            "next_agent_input": {
                "workflow_id": workflow_id,
                "implementation_complete": implemented == approved_reqs,
                "requirements_implemented": implemented,
                "files_modified": random.randint(12, 25),
                "cache_file": f".data/{workflow_id}_implementation_results.json",
                "git_changes_ready": True
            }
        }
    
    def generate_agent_5_data(self, workflow_id, run_number, agent_4_data):
        """Generate Agent 5 (Gate Promote) data with cycle analytics"""
        timestamp = (self.base_timestamp + timedelta(days=run_number, hours=5)).isoformat() + "Z"
        metrics = self.generate_realistic_metrics(run_number, 5)
        
        # Gate decision based on overall quality
        overall_score = random.randint(85, 100) if run_number > 2 else random.randint(70, 95)
        gate_passes = overall_score >= 90
        
        return {
            "workflow_id": workflow_id,
            "agent_name": "gate_promote_agent",
            "timestamp": timestamp,
            "execution_metrics": {
                "start_time": timestamp,
                "end_time": (datetime.fromisoformat(timestamp[:-1]) + timedelta(minutes=random.randint(10, 18))).isoformat() + "Z",
                "duration_seconds": random.randint(600, 1080),
                "memory_usage_mb": random.randint(40, 65),
                "cpu_usage_percent": random.randint(18, 35)
            },
            "performance_metrics": {
                **metrics,
                "validation_success_rate": random.randint(88, 98),
                "gate_decision_accuracy": random.randint(92, 99),
                "cycle_improvement_score": min(100, 60 + (run_number * 3))
            },
            "gate_promotion_decision": {
                "overall_validation_score": f"{overall_score}%",
                "validation_threshold_met": gate_passes,
                "gate_decision": "PASS" if gate_passes else "FAIL",
                "gate_decision_reasoning": "All validation criteria met successfully" if gate_passes else "Minor improvements needed",
                "workflow_completion_status": "COMPLETE" if gate_passes else "REPEAT_CYCLE"
            },
            "cycle_analytics": {
                "cycle_number": run_number,
                "previous_cycle_results": {
                    "improvement_from_last": random.uniform(0.02, 0.15) if run_number > 1 else 0,
                    "quality_trend": "IMPROVING" if run_number > 2 else "STABLE"
                },
                "improvement_metrics": {
                    "pap_compliance_improvement": random.uniform(0.5, 3.2),
                    "issue_resolution_improvement": random.uniform(1.2, 4.8),
                    "velocity_improvement": random.uniform(0.1, 2.1)
                },
                "cross_cycle_trends": {
                    "performance_trend": "IMPROVING" if run_number >= 3 else "STABLE",
                    "efficiency_trend": "FASTER" if run_number >= 4 else "SAME",
                    "quality_trend": "HIGHER" if run_number >= 2 else "SAME"
                }
            },
            "trending_metadata": {
                "run_sequence": run_number,
                "historical_performance": [
                    {"run": i, "score": min(100, 65 + (i * 2.5))} for i in range(1, run_number + 1)
                ],
                "velocity_indicator": "FASTER" if run_number > 3 else "SAME",
                "success_rate_trend": min(1.0, 0.7 + (run_number * 0.025)),
                "completion_time_trend": "DECREASING" if run_number > 4 else "STABLE"
            }
        }
    
    def generate_execution_logs(self, workflow_id, run_number, agent_data_list):
        """Generate realistic execution logs for all agents"""
        logs = []
        
        for i, agent_data in enumerate(agent_data_list):
            agent_name = agent_data["agent_name"]
            sequence = f"seq_{i+1:03d}"
            base_time = datetime.fromisoformat(agent_data["timestamp"][:-1])
            
            # Planning log
            logs.append({
                "timestamp": (base_time - timedelta(minutes=2)).isoformat() + "Z",
                "workflow_id": workflow_id,
                "sequence_id": sequence,
                "agent_name": agent_name,
                "action_type": "PLANNING",
                "content": {
                    "analysis_plan": f"Execute {agent_name} analysis phase",
                    "execution_steps": [
                        "Load input data and validate",
                        "Perform core analysis",
                        "Generate structured output",
                        "Prepare handoff data"
                    ],
                    "expected_outcomes": f"Complete {agent_name} deliverables"
                },
                "motive": f"Agent planning phase: Starting {sequence} workflow execution",
                "metadata": {"phase": "planning", "step_type": "preparation"},
                "log_level": "INFO"
            })
            
            # Execution log
            logs.append({
                "timestamp": (base_time - timedelta(minutes=1)).isoformat() + "Z",
                "workflow_id": workflow_id,
                "sequence_id": sequence,
                "agent_name": agent_name,
                "action_type": "EXECUTING",
                "content": {
                    "current_step": f"Processing {agent_name} core logic",
                    "progress": f"{random.randint(45, 85)}%",
                    "intermediate_results": f"Generated {random.randint(5, 25)} analysis points"
                },
                "motive": f"Executing agent task: Core {agent_name} processing",
                "metadata": {"phase": "execution", "step_type": "implementation"},
                "log_level": "INFO"
            })
            
            # Output log
            logs.append({
                "timestamp": base_time.isoformat() + "Z",
                "workflow_id": workflow_id,
                "sequence_id": sequence,
                "agent_name": agent_name,
                "action_type": "OUTPUT",
                "content": {
                    "results_summary": f"{agent_name} completed successfully",
                    "key_findings": [
                        f"Processed {random.randint(10, 50)} items",
                        f"Quality score: {random.randint(80, 95)}%",
                        "All validation checks passed"
                    ],
                    "next_steps": f"Hand off to next agent in sequence"
                },
                "motive": f"Generating output for: {agent_name} completion",
                "metadata": {"phase": "output", "step_type": "result_generation"},
                "log_level": "INFO"
            })
            
            # Handoff log (except for last agent)
            if i < len(agent_data_list) - 1:
                next_agent = agent_data_list[i + 1]["agent_name"]
                logs.append({
                    "timestamp": (base_time + timedelta(minutes=1)).isoformat() + "Z",
                    "workflow_id": workflow_id,
                    "sequence_id": sequence,
                    "agent_name": f"{agent_name}_to_{next_agent}",
                    "action_type": "HANDOFF",
                    "content": {
                        "handoff_data": f"Complete {agent_name} results",
                        "context": f"Workflow progressing from {sequence} to seq_{i+2:03d}",
                        "expectations": f"{next_agent} should process handoff data"
                    },
                    "motive": f"Handoff from {agent_name} to {next_agent}: Workflow progression",
                    "metadata": {
                        "phase": "handoff",
                        "from_agent": agent_name,
                        "to_agent": next_agent,
                        "step_type": "agent_transition"
                    },
                    "log_level": "INFO"
                })
        
        return logs
    
    def generate_complete_workflow(self, run_number):
        """Generate complete workflow with all agents and realistic progression"""
        workflow_id = self.generate_workflow_id(run_number)
        print(f"  Generating workflow {run_number}: {workflow_id}")
        
        # Generate all agent data with realistic dependencies
        agent_1 = self.generate_agent_1_data(workflow_id, run_number)
        agent_2 = self.generate_agent_2_data(workflow_id, run_number, agent_1)
        agent_3 = self.generate_agent_3_data(workflow_id, run_number, agent_2)
        agent_4 = self.generate_agent_4_data(workflow_id, run_number, agent_3)
        agent_5 = self.generate_agent_5_data(workflow_id, run_number, agent_4)
        
        # Save individual agent files
        agents = [
            (agent_1, "schema_coherence_analysis"),
            (agent_2, "requirements_analysis"),
            (agent_3, "requirements_validation"),
            (agent_4, "implementation_results"),
            (agent_5, "gate_promotion_results")
        ]
        
        for agent_data, suffix in agents:
            filename = f"{workflow_id}_{suffix}.json"
            filepath = self.data_dir / filename
            with open(filepath, 'w') as f:
                json.dump(agent_data, f, indent=2)
        
        # Generate execution logs
        all_agents = [agent_1, agent_2, agent_3, agent_4, agent_5]
        execution_logs = self.generate_execution_logs(workflow_id, run_number, all_agents)
        
        return {
            "workflow_id": workflow_id,
            "agents": all_agents,
            "execution_logs": execution_logs,
            "files_created": [f"{workflow_id}_{suffix}.json" for _, suffix in agents]
        }
    
    def generate_mock_dataset(self, num_workflows=12):
        """Generate complete mock dataset with multiple workflows"""
        print(f"🚀 Generating {num_workflows} comprehensive workflow runs...")
        print(f"📁 Data directory: {self.data_dir}")
        
        all_execution_logs = []
        workflow_summaries = []
        
        for run in range(1, num_workflows + 1):
            workflow = self.generate_complete_workflow(run)
            all_execution_logs.extend(workflow["execution_logs"])
            
            # Create workflow summary
            workflow_summaries.append({
                "workflow_id": workflow["workflow_id"],
                "run_number": run,
                "files_created": workflow["files_created"],
                "agents_completed": len(workflow["agents"]),
                "execution_log_entries": len(workflow["execution_logs"])
            })
        
        # Write consolidated execution logs
        log_file = self.data_dir / "workflow_execution.jsonl"
        with open(log_file, 'w') as f:
            for log_entry in sorted(all_execution_logs, key=lambda x: x["timestamp"]):
                f.write(json.dumps(log_entry) + '\n')
        
        # Create analytics summary
        analytics_summary = {
            "generation_timestamp": datetime.now().isoformat() + "Z",
            "total_workflows": num_workflows,
            "total_agent_executions": num_workflows * 5,
            "total_execution_logs": len(all_execution_logs),
            "total_cache_files": num_workflows * 5,
            "data_directory": str(self.data_dir),
            "workflows": workflow_summaries,
            "performance_trends": {
                "avg_quality_improvement": 2.5,
                "avg_velocity_improvement": 1.8,
                "success_rate_progression": [0.7 + (i * 0.025) for i in range(num_workflows)]
            }
        }
        
        analytics_file = self.data_dir / "mock_data_summary.json"
        with open(analytics_file, 'w') as f:
            json.dump(analytics_summary, f, indent=2)
        
        print(f"\n✅ Mock data generation complete!")
        print(f"📊 Generated {num_workflows} workflow runs")
        print(f"🗃️  Created {num_workflows * 5} agent cache files")
        print(f"📝 Generated {len(all_execution_logs)} execution log entries")
        print(f"💾 Execution logs: {log_file}")
        print(f"📈 Analytics summary: {analytics_file}")
        
        return analytics_summary

def main():
    """Generate comprehensive mock data for WARPCORE dashboard"""
    generator = WARPCOREMockDataGenerator()
    
    # Generate 12 workflow runs with realistic progression
    summary = generator.generate_mock_dataset(12)
    
    print(f"\n🎯 Ready for dashboard testing!")
    print(f"🌐 Start the web server: python3 web/server.py")
    print(f"📊 Dashboard URL: http://localhost:8080")
    print(f"🔍 API endpoints:")
    print(f"   - /api/execution-logs")
    print(f"   - /api/workflow-files")  
    print(f"   - /data/analytics")

if __name__ == "__main__":
    main()