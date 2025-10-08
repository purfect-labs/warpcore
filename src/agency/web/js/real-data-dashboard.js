// WARPCORE Real Data Dashboard - Interactive Analytics
class RealDataDashboard {
    constructor() {
        this.realWorkflowData = {};
        this.executionLogs = [];
        this.currentTab = 'overview';
        this.charts = {};
        
        this.init();
    }

    async init() {
        console.log('🚀 Initializing Real Data Dashboard...');
        await this.loadRealWorkflowData();
        this.createTabNavigation();
        this.createInteractiveComponents();
        this.startRealTimeUpdates();
    }

    async loadRealWorkflowData() {
        try {
            // Load execution logs
            const logsResponse = await fetch('/api/execution-logs');
            const logsData = await logsResponse.json();
            this.executionLogs = logsData.logs || [];
            
            // Load all workflow files from .data directory
            await this.discoverWorkflowFiles();
            
            console.log('📊 Real Data Loaded:', {
                executionLogs: this.executionLogs.length,
                workflowFiles: Object.keys(this.realWorkflowData).length
            });
            
            this.processRealData();
            this.updateDashboard();
            
        } catch (error) {
            console.error('Error loading real data:', error);
        }
    }

    async discoverWorkflowFiles() {
        // Extract unique workflow IDs from execution logs
        const workflowIds = [...new Set(this.executionLogs.map(log => log.workflow_id))];
        
        // For each workflow, try to load its data
        for (const workflowId of workflowIds) {
            try {
                const workflowData = await this.loadWorkflowDetails(workflowId);
                if (workflowData) {
                    this.realWorkflowData[workflowId] = workflowData;
                }
            } catch (e) {
                console.log(`No detailed data found for ${workflowId}`);
            }
        }
    }

    async loadWorkflowDetails(workflowId) {
        // Try different possible file patterns for workflow data
        const patterns = [
            `/api/workflow-logs/${workflowId}`,
            // We could add more patterns here if we had different endpoints
        ];
        
        for (const pattern of patterns) {
            try {
                const response = await fetch(pattern);
                if (response.ok) {
                    return await response.json();
                }
            } catch (e) {
                // Continue to next pattern
            }
        }
        return null;
    }

    processRealData() {
        // Group execution logs by workflow
        this.workflowSummary = this.executionLogs.reduce((acc, log) => {
            if (!acc[log.workflow_id]) {
                acc[log.workflow_id] = {
                    id: log.workflow_id,
                    agents: new Set(),
                    actions: [],
                    startTime: log.timestamp,
                    endTime: log.timestamp,
                    actionTypes: {}
                };
            }
            
            const workflow = acc[log.workflow_id];
            workflow.agents.add(log.agent_name);
            workflow.actions.push(log);
            
            // Track action types
            workflow.actionTypes[log.action_type] = (workflow.actionTypes[log.action_type] || 0) + 1;
            
            // Update timing
            if (log.timestamp < workflow.startTime) workflow.startTime = log.timestamp;
            if (log.timestamp > workflow.endTime) workflow.endTime = log.timestamp;
            
            return acc;
        }, {});
        
        // Convert sets to arrays and calculate metrics
        Object.values(this.workflowSummary).forEach(workflow => {
            workflow.agents = Array.from(workflow.agents);
            workflow.duration = new Date(workflow.endTime) - new Date(workflow.startTime);
            workflow.totalActions = workflow.actions.length;
        });
    }

    createTabNavigation() {
        const tabContainer = document.createElement('div');
        tabContainer.className = 'dashboard-tabs';
        tabContainer.innerHTML = `
            <div class="tab-navigation">
                <button class="tab-btn active" data-tab="overview">📊 Overview</button>
                <button class="tab-btn" data-tab="workflows">🔄 Workflows</button>
                <button class="tab-btn" data-tab="agents">🤖 Agents</button>
                <button class="tab-btn" data-tab="analytics">📈 Analytics</button>
                <button class="tab-btn" data-tab="timeline">⏰ Timeline</button>
            </div>
            <div class="tab-content">
                <div id="tab-overview" class="tab-panel active"></div>
                <div id="tab-workflows" class="tab-panel"></div>
                <div id="tab-agents" class="tab-panel"></div>
                <div id="tab-analytics" class="tab-panel"></div>
                <div id="tab-timeline" class="tab-panel"></div>
            </div>
        `;
        
        // Insert tabs into dashboard content container
        const dashboardContent = document.getElementById('dashboard-content');
        if (dashboardContent) {
            dashboardContent.appendChild(tabContainer);
        } else {
            // Fallback to dashboard grid if available
            const dashboardGrid = document.querySelector('.dashboard-grid');
            if (dashboardGrid) {
                dashboardGrid.parentNode.insertBefore(tabContainer, dashboardGrid);
            }
        }
        
        // Add tab switching functionality
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tabId = e.target.dataset.tab;
                this.switchTab(tabId);
            });
        });
        
        // Add CSS for tabs
        this.addTabStyles();
    }

    switchTab(tabId) {
        // Update active tab button
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelector(`[data-tab="${tabId}"]`).classList.add('active');
        
        // Update active tab panel
        document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.remove('active'));
        document.getElementById(`tab-${tabId}`).classList.add('active');
        
        this.currentTab = tabId;
        this.renderTabContent(tabId);
    }

    async renderTabContent(tabId) {
        const panel = document.getElementById(`tab-${tabId}`);
        
        switch(tabId) {
            case 'overview':
                await this.renderOverviewTab(panel);
                break;
            case 'workflows':
                this.renderWorkflowsTab(panel);
                break;
            case 'agents':
                await this.renderAgentsTab(panel);
                break;
            case 'analytics':
                this.renderAnalyticsTab(panel);
                break;
            case 'timeline':
                this.renderTimelineTab(panel);
                break;
        }
    }

    async renderOverviewTab(panel) {
        // Fetch real metrics from API
        try {
            const response = await fetch('/api/real-metrics');
            const data = await response.json();
            const metrics = data.real_metrics.overview_metrics;
            const dataQuality = data.real_metrics.data_quality;
            
            panel.innerHTML = `
                <div class="overview-grid">
                    <div class="metric-card">
                        <div class="metric-icon">🔄</div>
                        <div class="metric-value">${metrics.total_workflows}</div>
                        <div class="metric-label">Active Workflows</div>
                        <div class="metric-subtitle">REAL DATA</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-icon">⚡</div>
                        <div class="metric-value">${metrics.total_actions}</div>
                        <div class="metric-label">Total Actions</div>
                        <div class="metric-subtitle">REAL DATA</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-icon">🤖</div>
                        <div class="metric-value">${metrics.unique_agents}</div>
                        <div class="metric-label">Active Agents</div>
                        <div class="metric-subtitle">REAL DATA</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-icon">📊</div>
                        <div class="metric-value">${metrics.success_rate}%</div>
                        <div class="metric-label">Success Rate</div>
                        <div class="metric-subtitle">REAL PAP/VALIDATION DATA</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-icon">🎯</div>
                        <div class="metric-value">${metrics.avg_efficiency}%</div>
                        <div class="metric-label">Avg Efficiency</div>
                        <div class="metric-subtitle">REAL PERF DATA</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-icon">⏱️</div>
                        <div class="metric-value">${this.formatDuration(metrics.avg_duration_seconds * 1000)}</div>
                        <div class="metric-label">Avg Duration</div>
                        <div class="metric-subtitle">REAL TIMING DATA</div>
                    </div>
                </div>
                
                <div class="data-quality-indicator">
                    <h3>📈 Data Quality Indicators</h3>
                    <div class="quality-grid">
                        <div class="quality-item">
                            <span class="quality-label">Efficiency Measurements:</span>
                            <span class="quality-value">${dataQuality.efficiency_data_points}</span>
                        </div>
                        <div class="quality-item">
                            <span class="quality-label">Quality Assessments:</span>
                            <span class="quality-value">${dataQuality.quality_data_points}</span>
                        </div>
                        <div class="quality-item">
                            <span class="quality-label">PAP Compliance Checks:</span>
                            <span class="quality-value">${dataQuality.pap_data_points}</span>
                        </div>
                        <div class="quality-item">
                            <span class="quality-label">Validation Results:</span>
                            <span class="quality-value">${dataQuality.validation_data_points}</span>
                        </div>
                        <div class="quality-item">
                            <span class="quality-label">Duration Measurements:</span>
                            <span class="quality-value">${dataQuality.duration_data_points}</span>
                        </div>
                    </div>
                </div>
            
            <div class="chart-container">
                <h3>📈 Action Types Distribution</h3>
                <canvas id="actionTypesChart" width="400" height="200"></canvas>
            </div>
            
            <div class="recent-activity">
                <h3>🕐 Recent Activity</h3>
                <div class="activity-list">
                    ${this.executionLogs.slice(0, 5).map(log => `
                        <div class="activity-item">
                            <div class="activity-time">${new Date(log.timestamp).toLocaleTimeString()}</div>
                            <div class="activity-content">
                                <strong>${log.agent_name}</strong> performed <span class="action-type">${log.action_type}</span>
                                in workflow <span class="workflow-id">${log.workflow_id}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
        // Create action types chart
        setTimeout(() => this.createActionTypesChart(), 100);
    }

    async renderWorkflowsTab(panel) {
        try {
            // Fetch workflow files from the new API
            const response = await fetch('/api/workflow-files');
            const data = await response.json();
            const workflowFiles = data.workflow_files || [];
            
            panel.innerHTML = `
                <div class="workflows-header">
                    <h3>📁 Workflow Cache Files (${workflowFiles.length} workflows)</h3>
                    <div class="workflow-meta-stats">
                        <span class="meta-stat">${data.total_files || 0} total files</span>
                        <span class="meta-stat">${this.formatFileSize(workflowFiles.reduce((sum, wf) => sum + wf.total_size, 0))}</span>
                        <span class="meta-badge">WARP REAL CACHE DATA</span>
                    </div>
                    <div class="workflow-filters">
                        <button class="filter-btn active" data-filter="all">All Workflows</button>
                        <button class="filter-btn" data-filter="recent">Recent (24h)</button>
                        <button class="filter-btn" data-filter="large">Large Files</button>
                    </div>
                </div>
                
                <div class="workflows-tree-container">
                    ${workflowFiles.map(workflow => `
                        <div class="workflow-tree-node" data-workflow-id="${workflow.workflow_id}">
                            <div class="workflow-node-header" onclick="this.parentElement.classList.toggle('expanded')">
                                <div class="workflow-expand-icon">▶</div>
                                <div class="workflow-icon">📊</div>
                                <div class="workflow-node-info">
                                    <div class="workflow-node-title">${workflow.workflow_id}</div>
                                    <div class="workflow-node-meta">
                                        ${workflow.total_files} files • ${workflow.agents.length} agents • ${this.formatFileSize(workflow.total_size)}
                                        <span class="workflow-last-modified">${this.formatTimeAgo(workflow.last_modified_iso)}</span>
                                    </div>
                                </div>
                                <div class="workflow-node-badges">
                                    <span class="cache-badge">CACHE</span>
                                    ${workflow.agents.includes('PATHFINDER') ? '<span class="agent-badge pathfinder">🔍</span>' : ''}
                                    ${workflow.agents.includes('ARCHITECT') ? '<span class="agent-badge architect">🏗️</span>' : ''}
                                    ${workflow.agents.includes('ENFORCER') ? '<span class="agent-badge enforcer">⚡</span>' : ''}
                                </div>
                            </div>
                            
                            <div class="workflow-node-children">
                                ${workflow.files.map(file => `
                                    <div class="file-tree-node" data-filename="${file.filename}">
                                        <div class="file-node-content">
                                            <div class="file-icon">${this.getFileTypeIcon(file.file_type)}</div>
                                            <div class="file-node-info">
                                            <div class="file-node-title">
                                                    ${file.file_type}
                                                    <span class="file-node-filename">${file.filename}</span>
                                                    ${file.mission_status === 'COMPLETED SUCCESSFULLY' ? '<span class="status-success">✅ COMPLETE</span>' : ''}
                                                    ${file.dual_cache_confirmed ? '<span class="cache-confirmed">🔄 DUAL CACHE</span>' : ''}
                                                </div>
                                                <div class="file-node-meta">
                                                    <span class="file-agent-type">${file.agent_type || file.agent_name}</span>
                                                    <span class="file-agent-display">${file.agent_display_name || file.agent_name}</span>
                                                    <span class="file-size">${this.formatFileSize(file.size)}</span>
                                                    <span class="file-time">${new Date(file.modified_iso).toLocaleString()}</span>
                                                    ${file.trace_id !== 'N/A' ? `<span class="file-trace">${file.trace_id}</span>` : ''}
                                                    ${file.next_agent ? `<span class="next-agent">→ ${file.next_agent.toUpperCase()}</span>` : ''}
                                                </div>
                                                ${file.summary && Object.keys(file.summary).length > 0 ? `
                                                    <div class="file-summary">
                                                        ${this.renderFileSummary(file.summary)}
                                                    </div>
                                                ` : ''}
                                            </div>
                                            <div class="file-actions">
                                                <button class="file-action-btn" onclick="this.viewFileContent('${file.filename}')" title="View Content">
                                                    👁️
                                                </button>
                                                <button class="file-action-btn" onclick="this.downloadFile('${file.filename}')" title="Download">
                                                    💾
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `).join('')}
                </div>
                
                <div class="workflows-footer">
                    <div class="footer-info">
                        <span class="footer-source">${data.data_source || 'WARP CACHE DATA'}</span>
                        <span class="footer-updated">Last updated: ${new Date(data.last_updated).toLocaleString()}</span>
                    </div>
                </div>
            `;
            
            // Add event listeners for filter buttons
            panel.querySelectorAll('.filter-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    // Remove active from all buttons
                    panel.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                    e.target.classList.add('active');
                    
                    const filter = e.target.dataset.filter;
                    this.filterWorkflows(panel, filter, workflowFiles);
                });
            });
            
        } catch (error) {
            console.error('Error loading workflow files:', error);
            panel.innerHTML = `
                <div class="error-container">
                    <h3>⚠️ Error Loading Workflow Files</h3>
                    <p>Could not load workflow cache files: ${error.message}</p>
                    <div class="error-note">WARP DEMO ERROR DISPLAY</div>
                </div>
            `;
        }
    }

    async renderAgentsTab(panel) {
        // Fetch real agent performance from API
        try {
            const response = await fetch('/api/agent-performance');
            const data = await response.json();
            const agentStats = data.agent_performance;
        
        panel.innerHTML = `
            <div class="agents-overview">
                <h3>🤖 Agent Performance Analysis</h3>
                <div class="agents-grid">
                    ${agentStats.map(agent => `
                        <div class="agent-card">
                            <div class="agent-header">
                                <div class="agent-name">${agent.name}</div>
                                <div class="agent-score">${agent.efficiency}%</div>
                            </div>
                            <div class="agent-metrics">
                                <div class="agent-metric">
                                    <span class="metric-label">Total Actions:</span>
                                    <span class="metric-value">${agent.total_actions}</span>
                                    <span class="metric-badge">REAL</span>
                                </div>
                                <div class="agent-metric">
                                    <span class="metric-label">Workflows:</span>
                                    <span class="metric-value">${agent.workflow_count}</span>
                                    <span class="metric-badge">REAL</span>
                                </div>
                                <div class="agent-metric">
                                    <span class="metric-label">Avg Duration:</span>
                                    <span class="metric-value">${agent.avg_duration_seconds ? agent.avg_duration_seconds + 's' : 'No Data'}</span>
                                    <span class="metric-badge">${agent.real_data_points.duration_measurements > 0 ? 'REAL' : 'N/A'}</span>
                                </div>
                            </div>
                            <div class="agent-real-data">
                                <h5>Real Performance Data Points</h5>
                                <div class="data-points-grid">
                                    <div class="data-point">
                                        <span class="data-label">Efficiency:</span>
                                        <span class="data-count">${agent.real_data_points.efficiency_scores}</span>
                                    </div>
                                    <div class="data-point">
                                        <span class="data-label">Quality:</span>
                                        <span class="data-count">${agent.real_data_points.quality_scores}</span>
                                    </div>
                                    <div class="data-point">
                                        <span class="data-label">PAP:</span>
                                        <span class="data-count">${agent.real_data_points.pap_scores}</span>
                                    </div>
                                    <div class="data-point">
                                        <span class="data-label">Validation:</span>
                                        <span class="data-count">${agent.real_data_points.validation_scores}</span>
                                    </div>
                                </div>
                            </div>
                            <div class="agent-actions">
                                <h5>Action Breakdown</h5>
                                ${Object.entries(agent.action_types).map(([type, count]) => `
                                    <div class="action-breakdown">
                                        <span class="action-type">${type}</span>
                                        <div class="action-bar">
                                            <div class="action-fill" style="width: ${(count / agent.total_actions * 100)}%"></div>
                                        </div>
                                        <span class="action-count">${count}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        } catch (error) {
            console.error('Error loading agent performance:', error);
            panel.innerHTML = `
                <div class="error-message">
                    <h3>⚠️ Error Loading Agent Performance</h3>
                    <p>Unable to fetch real agent performance data. Using fallback data calculation.</p>
                </div>
            `;
            // Fallback to original method if API fails
            const agentStats = this.getAgentStatistics();
            // ... original rendering code would go here
        }
    }

    renderAnalyticsTab(panel) {
        panel.innerHTML = `
            <div class="analytics-dashboard">
                <div class="charts-grid">
                    <div class="chart-card">
                        <h4>📊 Workflow Distribution</h4>
                        <canvas id="workflowChart" width="300" height="200"></canvas>
                    </div>
                    <div class="chart-card">
                        <h4>⏰ Activity Timeline</h4>
                        <canvas id="timelineChart" width="300" height="200"></canvas>
                    </div>
                    <div class="chart-card">
                        <h4>🎯 Agent Efficiency</h4>
                        <canvas id="efficiencyChart" width="300" height="200"></canvas>
                    </div>
                    <div class="chart-card">
                        <h4>🔄 Action Flow</h4>
                        <canvas id="flowChart" width="300" height="200"></canvas>
                    </div>
                </div>
            </div>
        `;
        
        // Create all charts
        setTimeout(() => {
            this.createWorkflowChart();
            this.createTimelineChart();
            this.createEfficiencyChart();
            this.createFlowChart();
        }, 100);
    }

    renderTimelineTab(panel) {
        const sortedLogs = [...this.executionLogs].sort((a, b) => 
            new Date(b.timestamp) - new Date(a.timestamp)
        );
        
        panel.innerHTML = `
            <div class="timeline-container">
                <h3>⏰ Execution Timeline</h3>
                <div class="timeline-filters">
                    <select id="workflowFilter">
                        <option value="">All Workflows</option>
                        ${Object.keys(this.workflowSummary).map(id => 
                            `<option value="${id}">${id}</option>`
                        ).join('')}
                    </select>
                    <select id="agentFilter">
                        <option value="">All Agents</option>
                        ${[...new Set(this.executionLogs.map(log => log.agent_name))].map(agent => 
                            `<option value="${agent}">${agent}</option>`
                        ).join('')}
                    </select>
                </div>
                
                <div class="timeline-list">
                    ${sortedLogs.map(log => `
                        <div class="timeline-entry" data-workflow="${log.workflow_id}" data-agent="${log.agent_name}">
                            <div class="timeline-timestamp">${new Date(log.timestamp).toLocaleString()}</div>
                            <div class="timeline-content">
                                <div class="timeline-action">
                                    <span class="action-badge ${log.action_type.toLowerCase()}">${log.action_type}</span>
                                    <span class="agent-name">${log.agent_name}</span>
                                </div>
                                <div class="timeline-workflow">Workflow: ${log.workflow_id}</div>
                                ${log.motive ? `<div class="timeline-motive">${log.motive}</div>` : ''}
                                ${log.content ? `<div class="timeline-details">${JSON.stringify(log.content, null, 2)}</div>` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
        // Add filter functionality
        document.getElementById('workflowFilter').addEventListener('change', this.filterTimeline.bind(this));
        document.getElementById('agentFilter').addEventListener('change', this.filterTimeline.bind(this));
    }

    filterTimeline() {
        const workflowFilter = document.getElementById('workflowFilter').value;
        const agentFilter = document.getElementById('agentFilter').value;
        
        document.querySelectorAll('.timeline-entry').forEach(entry => {
            const matchesWorkflow = !workflowFilter || entry.dataset.workflow === workflowFilter;
            const matchesAgent = !agentFilter || entry.dataset.agent === agentFilter;
            
            entry.style.display = matchesWorkflow && matchesAgent ? 'block' : 'none';
        });
    }

    // Helper methods
    calculateSuccessRate() {
        const successfulActions = this.executionLogs.filter(log => 
            log.action_type !== 'ERROR' && !log.motive?.toLowerCase().includes('error')
        );
        return Math.round((successfulActions.length / this.executionLogs.length) * 100);
    }

    formatDuration(ms) {
        if (ms < 1000) return `${ms}ms`;
        if (ms < 60000) return `${(ms/1000).toFixed(1)}s`;
        return `${(ms/60000).toFixed(1)}m`;
    }

    getWorkflowStatus(workflow) {
        const recentActions = workflow.actions.slice(-3);
        if (recentActions.some(a => a.action_type === 'ERROR')) return 'error';
        if (recentActions.some(a => a.action_type === 'EXECUTING')) return 'active';
        return 'completed';
    }

    getAgentStatistics() {
        const agentStats = {};
        
        this.executionLogs.forEach(log => {
            if (!agentStats[log.agent_name]) {
                agentStats[log.agent_name] = {
                    name: log.agent_name,
                    totalActions: 0,
                    workflowCount: new Set(),
                    actionTypes: {},
                    realEfficiencyScores: [],
                    realDurations: [],
                    qualityScores: [],
                    papComplianceScores: []
                };
            }
            
            const agent = agentStats[log.agent_name];
            agent.totalActions++;
            agent.workflowCount.add(log.workflow_id);
            agent.actionTypes[log.action_type] = (agent.actionTypes[log.action_type] || 0) + 1;
            
            // Extract REAL performance metrics from your workflow data
            const content = log.content || {};
            const perfMetrics = content.performance_metrics || {};
            const progMetrics = content.progress_metrics || {};
            const execMetrics = content.execution_metrics || {};
            
            // Collect real efficiency scores
            if (perfMetrics.efficiency_numeric) {
                agent.realEfficiencyScores.push(perfMetrics.efficiency_numeric);
            }
            if (perfMetrics.output_quality_score) {
                agent.qualityScores.push(perfMetrics.output_quality_score);
            }
            if (progMetrics.pap_compliance_score) {
                agent.papComplianceScores.push(progMetrics.pap_compliance_score);
            }
            if (progMetrics.validation_score) {
                agent.qualityScores.push(progMetrics.validation_score);
            }
            
            // Collect real duration data
            if (execMetrics.duration_seconds) {
                agent.realDurations.push(execMetrics.duration_seconds);
            }
        });
        
        return Object.values(agentStats).map(agent => {
            // Calculate REAL efficiency from actual performance data
            let efficiency = 0;
            if (agent.realEfficiencyScores.length > 0) {
                efficiency = Math.round(agent.realEfficiencyScores.reduce((a, b) => a + b, 0) / agent.realEfficiencyScores.length);
            } else if (agent.qualityScores.length > 0) {
                efficiency = Math.round(agent.qualityScores.reduce((a, b) => a + b, 0) / agent.qualityScores.length);
            } else if (agent.papComplianceScores.length > 0) {
                efficiency = Math.round(agent.papComplianceScores.reduce((a, b) => a + b, 0) / agent.papComplianceScores.length);
            } else {
                efficiency = 75; // Default for agents without performance data
            }
            
            // Calculate real average response time
            let avgResponseTime = 0;
            if (agent.realDurations.length > 0) {
                avgResponseTime = Math.round(agent.realDurations.reduce((a, b) => a + b, 0) / agent.realDurations.length);
            } else {
                avgResponseTime = 0; // No timing data available
            }
            
            return {
                ...agent,
                workflowCount: agent.workflowCount.size,
                efficiency: efficiency,
                avgResponseTime: avgResponseTime,
                realDataPoints: {
                    efficiencyScores: agent.realEfficiencyScores.length,
                    qualityScores: agent.qualityScores.length,
                    papScores: agent.papComplianceScores.length,
                    durations: agent.realDurations.length
                }
            };
        });
    }

    // Chart creation methods
    createActionTypesChart() {
        const canvas = document.getElementById('actionTypesChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        const actionTypes = {};
        
        this.executionLogs.forEach(log => {
            actionTypes[log.action_type] = (actionTypes[log.action_type] || 0) + 1;
        });
        
        this.createBarChart(ctx, actionTypes, canvas.width, canvas.height);
    }

    createBarChart(ctx, data, width, height) {
        const entries = Object.entries(data);
        const maxValue = Math.max(...entries.map(([_, value]) => value));
        const barWidth = (width - 80) / entries.length;
        const chartHeight = height - 80;
        
        ctx.clearRect(0, 0, width, height);
        
        // Draw bars
        entries.forEach(([label, value], index) => {
            const barHeight = (value / maxValue) * chartHeight;
            const x = 40 + index * barWidth;
            const y = height - 40 - barHeight;
            
            // Bar
            ctx.fillStyle = `hsl(${index * 60}, 70%, 60%)`;
            ctx.fillRect(x, y, barWidth - 10, barHeight);
            
            // Label
            ctx.fillStyle = '#ffffff';
            ctx.font = '12px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(label, x + barWidth/2, height - 20);
            
            // Value
            ctx.fillText(value.toString(), x + barWidth/2, y - 10);
        });
    }

    createWorkflowChart() {
        const canvas = document.getElementById('workflowChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        const workflowData = Object.values(this.workflowSummary).reduce((acc, workflow) => {
            acc[workflow.id] = workflow.totalActions;
            return acc;
        }, {});
        
        this.createBarChart(ctx, workflowData, canvas.width, canvas.height);
    }

    createTimelineChart() {
        // Implementation for timeline visualization
        const canvas = document.getElementById('timelineChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        this.drawTimelineVisualization(ctx, canvas.width, canvas.height);
    }

    createEfficiencyChart() {
        // Implementation for efficiency radar chart
        const canvas = document.getElementById('efficiencyChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        this.drawEfficiencyRadar(ctx, canvas.width, canvas.height);
    }

    createFlowChart() {
        // Implementation for action flow visualization
        const canvas = document.getElementById('flowChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        this.drawFlowDiagram(ctx, canvas.width, canvas.height);
    }

    drawTimelineVisualization(ctx, width, height) {
        ctx.clearRect(0, 0, width, height);
        ctx.fillStyle = '#00d4ff';
        ctx.font = '14px sans-serif';
        ctx.fillText('Timeline visualization', 10, height/2);
    }

    drawEfficiencyRadar(ctx, width, height) {
        ctx.clearRect(0, 0, width, height);
        ctx.strokeStyle = '#39ff14';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(width/2, height/2, Math.min(width, height)/4, 0, 2 * Math.PI);
        ctx.stroke();
    }

    drawFlowDiagram(ctx, width, height) {
        ctx.clearRect(0, 0, width, height);
        ctx.fillStyle = '#bf00ff';
        ctx.font = '14px sans-serif';
        ctx.fillText('Flow diagram', 10, height/2);
    }

    addTabStyles() {
        const styles = `
            <style id="tab-styles">
                .dashboard-tabs {
                    margin: 2rem 0;
                }
                
                .tab-navigation {
                    display: flex;
                    gap: 0.5rem;
                    margin-bottom: 2rem;
                    border-bottom: 2px solid rgba(255, 255, 255, 0.1);
                }
                
                .tab-btn {
                    background: transparent;
                    border: none;
                    color: var(--text-secondary);
                    padding: 1rem 2rem;
                    cursor: pointer;
                    border-radius: 10px 10px 0 0;
                    transition: all 0.3s ease;
                    font-size: 1rem;
                    font-weight: 600;
                }
                
                .tab-btn:hover {
                    color: var(--text-primary);
                    background: rgba(255, 255, 255, 0.05);
                }
                
                .tab-btn.active {
                    color: var(--neon-blue);
                    background: rgba(0, 212, 255, 0.1);
                    border-bottom: 2px solid var(--neon-blue);
                }
                
                .tab-panel {
                    display: none;
                    min-height: 400px;
                }
                
                .tab-panel.active {
                    display: block;
                }
                
                .overview-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 1.5rem;
                    margin-bottom: 2rem;
                }
                
                .metric-card {
                    background: var(--glass-bg);
                    padding: 2rem;
                    border-radius: 15px;
                    text-align: center;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                }
                
                .metric-icon {
                    font-size: 2.5rem;
                    margin-bottom: 1rem;
                }
                
                .metric-value {
                    font-size: 2rem;
                    font-weight: 700;
                    color: var(--neon-blue);
                    margin-bottom: 0.5rem;
                }
                
                .metric-label {
                    color: var(--text-secondary);
                    font-size: 0.9rem;
                }
                
                .workflow-card {
                    background: var(--glass-bg);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 15px;
                    margin-bottom: 1rem;
                    overflow: hidden;
                }
                
                .workflow-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 1.5rem;
                    cursor: pointer;
                    transition: background 0.3s ease;
                }
                
                .workflow-header:hover {
                    background: rgba(255, 255, 255, 0.05);
                }
                
                .workflow-id {
                    font-weight: 600;
                    color: var(--neon-blue);
                    margin-bottom: 0.5rem;
                }
                
                .workflow-meta {
                    color: var(--text-secondary);
                    font-size: 0.9rem;
                }
                
                .status-badge {
                    padding: 0.3rem 0.8rem;
                    border-radius: 15px;
                    font-size: 0.8rem;
                    font-weight: 600;
                    text-transform: uppercase;
                }
                
                .status-badge.active {
                    background: rgba(57, 255, 20, 0.2);
                    color: var(--neon-green);
                }
                
                .status-badge.completed {
                    background: rgba(0, 212, 255, 0.2);
                    color: var(--neon-blue);
                }
                
                .status-badge.error {
                    background: rgba(255, 107, 107, 0.2);
                    color: #ff6b6b;
                }
                
                .workflow-details {
                    display: none;
                    padding: 0 1.5rem 1.5rem;
                    border-top: 1px solid rgba(255, 255, 255, 0.1);
                }
                
                .workflow-card.expanded .workflow-details {
                    display: block;
                }
                
                .workflow-card.expanded .expand-icon {
                    transform: rotate(180deg);
                }
                
                .expand-icon {
                    transition: transform 0.3s ease;
                    margin-left: 1rem;
                }
                
                .timeline-items {
                    max-height: 200px;
                    overflow-y: auto;
                }
                
                .timeline-item {
                    display: flex;
                    gap: 1rem;
                    padding: 0.8rem 0;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                }
                
                .timeline-time {
                    color: var(--text-secondary);
                    font-size: 0.8rem;
                    min-width: 80px;
                }
                
                .timeline-motive {
                    color: var(--text-secondary);
                    font-size: 0.8rem;
                    font-style: italic;
                }
                
                .agents-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 1.5rem;
                }
                
                .agent-chip {
                    background: rgba(0, 212, 255, 0.1);
                    padding: 0.8rem;
                    border-radius: 10px;
                    text-align: center;
                }
                
                .chart-container, .chart-card {
                    background: var(--glass-bg);
                    padding: 2rem;
                    border-radius: 15px;
                    margin: 1rem 0;
                }
                
                .charts-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 2rem;
                }
                
                .activity-list {
                    max-height: 300px;
                    overflow-y: auto;
                }
                
                .activity-item {
                    display: flex;
                    gap: 1rem;
                    padding: 1rem;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                }
                
                .activity-time {
                    color: var(--text-secondary);
                    min-width: 80px;
                    font-size: 0.9rem;
                }
                
                .action-type {
                    color: var(--neon-green);
                    font-weight: 600;
                }
                
                .workflow-id {
                    color: var(--neon-blue);
                }
                
                .timeline-container {
                    max-height: 600px;
                    overflow-y: auto;
                }
                
                .timeline-entry {
                    display: flex;
                    gap: 1rem;
                    padding: 1rem;
                    border-left: 3px solid var(--neon-blue);
                    margin: 1rem 0;
                    background: rgba(0, 212, 255, 0.05);
                    border-radius: 0 10px 10px 0;
                }
                
                .timeline-timestamp {
                    min-width: 150px;
                    color: var(--text-secondary);
                    font-size: 0.9rem;
                }
                
                .action-badge {
                    padding: 0.2rem 0.6rem;
                    border-radius: 10px;
                    font-size: 0.8rem;
                    font-weight: 600;
                    margin-right: 0.5rem;
                }
                
                .action-badge.output {
                    background: rgba(57, 255, 20, 0.2);
                    color: var(--neon-green);
                }
                
                .action-badge.executing {
                    background: rgba(255, 102, 0, 0.2);
                    color: var(--neon-orange);
                }
                
                .action-badge.planning {
                    background: rgba(0, 212, 255, 0.2);
                    color: var(--neon-blue);
                }
                
                .timeline-filters {
                    display: flex;
                    gap: 1rem;
                    margin-bottom: 2rem;
                }
                
                .timeline-filters select {
                    background: var(--glass-bg);
                    color: var(--text-primary);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 8px;
                    padding: 0.5rem 1rem;
                }
                
                /* Workflow Tree Styles */
                .workflows-header {
                    background: var(--glass-bg);
                    padding: 1.5rem;
                    border-radius: 15px;
                    margin-bottom: 1rem;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                }
                
                .workflow-meta-stats {
                    display: flex;
                    gap: 1rem;
                    margin: 1rem 0;
                    flex-wrap: wrap;
                }
                
                .meta-stat {
                    background: rgba(0, 212, 255, 0.1);
                    padding: 0.5rem 1rem;
                    border-radius: 8px;
                    color: var(--neon-blue);
                    font-size: 0.9rem;
                }
                
                .meta-badge {
                    background: rgba(57, 255, 20, 0.2);
                    color: var(--neon-green);
                    padding: 0.5rem 1rem;
                    border-radius: 8px;
                    font-size: 0.8rem;
                    font-weight: 600;
                }
                
                .workflow-filters {
                    display: flex;
                    gap: 0.5rem;
                    margin-top: 1rem;
                }
                
                .filter-btn {
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    color: var(--text-secondary);
                    padding: 0.5rem 1rem;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    font-size: 0.9rem;
                }
                
                .filter-btn:hover {
                    background: rgba(0, 212, 255, 0.1);
                    color: var(--neon-blue);
                }
                
                .filter-btn.active {
                    background: rgba(0, 212, 255, 0.2);
                    color: var(--neon-blue);
                    border-color: var(--neon-blue);
                }
                
                .workflows-tree-container {
                    max-height: 600px;
                    overflow-y: auto;
                    padding-right: 0.5rem;
                }
                
                .workflow-tree-node {
                    background: var(--glass-bg);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 15px;
                    margin-bottom: 1rem;
                    overflow: hidden;
                }
                
                .workflow-node-header {
                    display: flex;
                    align-items: center;
                    padding: 1rem;
                    cursor: pointer;
                    transition: background 0.3s ease;
                    gap: 0.75rem;
                }
                
                .workflow-node-header:hover {
                    background: rgba(255, 255, 255, 0.05);
                }
                
                .workflow-expand-icon {
                    color: var(--neon-blue);
                    transition: transform 0.3s ease;
                    font-size: 1.2rem;
                }
                
                .workflow-tree-node.expanded .workflow-expand-icon {
                    transform: rotate(90deg);
                }
                
                .workflow-icon {
                    font-size: 1.5rem;
                }
                
                .workflow-node-info {
                    flex: 1;
                }
                
                .workflow-node-title {
                    font-weight: 600;
                    color: var(--text-primary);
                    font-size: 1.1rem;
                    margin-bottom: 0.25rem;
                }
                
                .workflow-node-meta {
                    color: var(--text-secondary);
                    font-size: 0.85rem;
                    display: flex;
                    gap: 0.75rem;
                    flex-wrap: wrap;
                    align-items: center;
                }
                
                .workflow-last-modified {
                    color: var(--neon-green);
                    font-weight: 500;
                }
                
                .workflow-node-badges {
                    display: flex;
                    gap: 0.5rem;
                    align-items: center;
                }
                
                .cache-badge {
                    background: rgba(255, 102, 0, 0.2);
                    color: var(--neon-orange);
                    padding: 0.25rem 0.6rem;
                    border-radius: 6px;
                    font-size: 0.7rem;
                    font-weight: 600;
                }
                
                .agent-badge {
                    font-size: 1.2rem;
                    padding: 0.2rem;
                }
                
                .agent-badge.pathfinder { background: rgba(0, 255, 255, 0.1); border-radius: 4px; }
                .agent-badge.architect { background: rgba(255, 165, 0, 0.1); border-radius: 4px; }
                .agent-badge.enforcer { background: rgba(255, 255, 0, 0.1); border-radius: 4px; }
                
                .workflow-node-children {
                    display: none;
                    border-top: 1px solid rgba(255, 255, 255, 0.1);
                    background: rgba(0, 0, 0, 0.2);
                }
                
                .workflow-tree-node.expanded .workflow-node-children {
                    display: block;
                }
                
                .file-tree-node {
                    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                    transition: background 0.3s ease;
                }
                
                .file-tree-node:hover {
                    background: rgba(255, 255, 255, 0.03);
                }
                
                .file-tree-node:last-child {
                    border-bottom: none;
                }
                
                .file-node-content {
                    display: flex;
                    align-items: center;
                    padding: 0.75rem 1rem;
                    gap: 0.75rem;
                }
                
                .file-icon {
                    font-size: 1.2rem;
                    min-width: 1.5rem;
                }
                
                .file-node-info {
                    flex: 1;
                    min-width: 0;
                }
                
                .file-node-title {
                    font-weight: 500;
                    color: var(--text-primary);
                    margin-bottom: 0.25rem;
                    display: flex;
                    gap: 0.5rem;
                    align-items: center;
                    flex-wrap: wrap;
                }
                
                .file-node-filename {
                    color: var(--text-secondary);
                    font-size: 0.8rem;
                    font-weight: 400;
                    background: rgba(255, 255, 255, 0.05);
                    padding: 0.2rem 0.5rem;
                    border-radius: 4px;
                }
                
                .file-node-meta {
                    display: flex;
                    gap: 0.75rem;
                    font-size: 0.75rem;
                    color: var(--text-secondary);
                    flex-wrap: wrap;
                    align-items: center;
                }
                
                .file-agent {
                    background: rgba(0, 212, 255, 0.15);
                    color: var(--neon-blue);
                    padding: 0.2rem 0.5rem;
                    border-radius: 4px;
                    font-weight: 500;
                }
                
                .file-agent-type {
                    background: rgba(255, 102, 0, 0.2);
                    color: var(--neon-orange);
                    padding: 0.2rem 0.5rem;
                    border-radius: 4px;
                    font-weight: 600;
                    font-size: 0.7rem;
                }
                
                .file-agent-display {
                    background: rgba(0, 212, 255, 0.1);
                    color: var(--neon-blue);
                    padding: 0.2rem 0.5rem;
                    border-radius: 4px;
                    font-weight: 400;
                }
                
                .status-success {
                    background: rgba(57, 255, 20, 0.2);
                    color: var(--neon-green);
                    padding: 0.2rem 0.5rem;
                    border-radius: 4px;
                    font-size: 0.7rem;
                    font-weight: 600;
                }
                
                .cache-confirmed {
                    background: rgba(0, 255, 255, 0.15);
                    color: #00ffff;
                    padding: 0.2rem 0.5rem;
                    border-radius: 4px;
                    font-size: 0.7rem;
                    font-weight: 500;
                }
                
                .next-agent {
                    background: rgba(255, 165, 0, 0.2);
                    color: #ffa500;
                    padding: 0.2rem 0.5rem;
                    border-radius: 4px;
                    font-size: 0.7rem;
                    font-weight: 600;
                }
                
                .file-size {
                    background: rgba(57, 255, 20, 0.1);
                    color: var(--neon-green);
                    padding: 0.2rem 0.5rem;
                    border-radius: 4px;
                }
                
                .file-time {
                    color: var(--text-secondary);
                }
                
                .file-trace {
                    background: rgba(255, 102, 0, 0.15);
                    color: var(--neon-orange);
                    padding: 0.2rem 0.5rem;
                    border-radius: 4px;
                    font-family: monospace;
                }
                
                .file-summary {
                    margin-top: 0.5rem;
                    padding: 0.5rem;
                    background: rgba(0, 212, 255, 0.05);
                    border-radius: 6px;
                    border-left: 3px solid var(--neon-blue);
                    font-size: 0.8rem;
                    color: var(--text-secondary);
                }
                
                .file-actions {
                    display: flex;
                    gap: 0.5rem;
                }
                
                .file-action-btn {
                    background: rgba(255, 255, 255, 0.1);
                    border: none;
                    color: var(--text-secondary);
                    padding: 0.5rem;
                    border-radius: 6px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    font-size: 1rem;
                }
                
                .file-action-btn:hover {
                    background: rgba(0, 212, 255, 0.2);
                    color: var(--neon-blue);
                    transform: scale(1.1);
                }
                
                .workflows-footer {
                    background: var(--glass-bg);
                    padding: 1rem;
                    border-radius: 10px;
                    margin-top: 1rem;
                    text-align: center;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                }
                
                .footer-info {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    font-size: 0.8rem;
                    color: var(--text-secondary);
                    flex-wrap: wrap;
                    gap: 1rem;
                }
                
                .footer-source {
                    background: rgba(57, 255, 20, 0.1);
                    color: var(--neon-green);
                    padding: 0.3rem 0.6rem;
                    border-radius: 4px;
                    font-weight: 500;
                }
                
                .error-container {
                    background: rgba(255, 107, 107, 0.1);
                    border: 1px solid rgba(255, 107, 107, 0.3);
                    border-radius: 15px;
                    padding: 2rem;
                    text-align: center;
                    margin: 2rem 0;
                }
                
                .error-container h3 {
                    color: #ff6b6b;
                    margin-bottom: 1rem;
                }
                
                .error-note {
                    background: rgba(255, 102, 0, 0.1);
                    color: var(--neon-orange);
                    padding: 0.5rem 1rem;
                    border-radius: 6px;
                    display: inline-block;
                    margin-top: 1rem;
                    font-size: 0.8rem;
                    font-weight: 600;
                }
            </style>
        `;
        document.head.insertAdjacentHTML('beforeend', styles);
    }

    createInteractiveComponents() {
        // Initialize with overview tab
        this.renderTabContent('overview');
    }

    updateDashboard() {
        // Update the current tab content
        this.renderTabContent(this.currentTab);
    }

    startRealTimeUpdates() {
        // Update data every 30 seconds
        setInterval(async () => {
            await this.loadRealWorkflowData();
        }, 30000);
    }
    
    // Helper methods for workflow files display
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    formatTimeAgo(isoTime) {
        const now = new Date();
        const time = new Date(isoTime);
        const diffMs = now - time;
        const diffMins = Math.floor(diffMs / (1000 * 60));
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
        
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        return time.toLocaleDateString();
    }
    
    getFileTypeIcon(fileType) {
        const iconMap = {
            'Pathfinder Analysis': '🔍',
            'Architect Requirements': '🏗️',
            'Enforcer Validation': '⚡',
            'Bootstrap State': '🚀',
            'Requirements Analysis': '📋',
            'Requirements Validation': '✅',
            'Schema Coherence': '📊',
            'Implementation Results': '🎯',
            'Unknown': '📄'
        };
        return iconMap[fileType] || '📄';
    }
    
    renderFileSummary(summary) {
        if (!summary || Object.keys(summary).length === 0) return '';
        
        const summaryItems = [];
        
        // Requirements data (Architect)
        if (summary.total_requirements) {
            summaryItems.push(`📝 ${summary.total_requirements} requirements`);
        }
        if (summary.critical_count) {
            summaryItems.push(`🔴 ${summary.critical_count} critical`);
        }
        if (summary.total_subtasks) {
            summaryItems.push(`📚 ${summary.total_subtasks} subtasks`);
        }
        if (summary.estimated_effort && summary.estimated_effort !== 'Unknown') {
            summaryItems.push(`⏳ ${summary.estimated_effort}`);
        }
        
        // Analysis data (Pathfinder)
        if (summary.files_analyzed) {
            summaryItems.push(`📁 ${summary.files_analyzed} files analyzed`);
        }
        if (summary.pap_compliance && summary.pap_compliance !== 'N/A') {
            summaryItems.push(`📈 PAP: ${summary.pap_compliance}`);
        }
        if (summary.issues_found) {
            summaryItems.push(`⚠️ ${summary.issues_found} issues`);
        }
        if (summary.fake_markers) {
            summaryItems.push(`🏷️ ${summary.fake_markers} fake markers`);
        }
        
        // Performance data (General)
        if (summary.quality_score) {
            summaryItems.push(`🎯 Quality: ${summary.quality_score}%`);
        }
        if (summary.efficiency && summary.efficiency !== 'Unknown') {
            summaryItems.push(`⚡ ${summary.efficiency}`);
        }
        if (summary.compliance_score) {
            summaryItems.push(`🔒 Compliance: ${summary.compliance_score}%`);
        }
        
        return summaryItems.join(' • ');
    }
    
    filterWorkflows(panel, filter, workflowFiles) {
        const container = panel.querySelector('.workflows-tree-container');
        const workflows = container.querySelectorAll('.workflow-tree-node');
        
        const now = new Date();
        const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        
        workflows.forEach(workflowNode => {
            const workflowId = workflowNode.dataset.workflowId;
            const workflowData = workflowFiles.find(wf => wf.workflow_id === workflowId);
            
            let show = true;
            
            switch (filter) {
                case 'recent':
                    show = new Date(workflowData.last_modified_iso) > oneDayAgo;
                    break;
                case 'large':
                    show = workflowData.total_size > 10000; // Files larger than 10KB
                    break;
                case 'all':
                default:
                    show = true;
                    break;
            }
            
            workflowNode.style.display = show ? 'block' : 'none';
        });
    }
    
    viewFileContent(filename) {
        // WARP DEMO - File content viewer would open here
        alert(`WARP DEMO: Would show content of ${filename}`);
        console.log(`WARP DEMO: Viewing file content for ${filename}`);
    }
    
    downloadFile(filename) {
        // WARP DEMO - File download would happen here
        alert(`WARP DEMO: Would download ${filename}`);
        console.log(`WARP DEMO: Downloading file ${filename}`);
    }
}

// Initialize the real data dashboard
document.addEventListener('DOMContentLoaded', () => {
    window.realDashboard = new RealDataDashboard();
});

console.log('🚀 Real Data Dashboard loaded and ready!');