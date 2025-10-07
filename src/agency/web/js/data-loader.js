// WARPCORE Analytics Data Loader - Real Data Processing

class WorkflowDataLoader {
    constructor() {
        this.analyticsData = null;
        this.workflowFiles = [];
        this.lastUpdateTime = null;
        this.refreshInterval = 10000; // 10 seconds
        this.init();
    }

    async init() {
        await this.loadWorkflowData();
        this.startAutoRefresh();
    }

    async loadWorkflowData() {
        try {
            // Load analytics orchestrator data first
            const analyticsResponse = await fetch('/data/analytics');
            if (analyticsResponse.ok) {
                this.analyticsData = await analyticsResponse.json();
                this.lastUpdateTime = new Date();
                this.processAnalyticsData();
                return;
            }

            // Fallback: load individual workflow files
            await this.loadIndividualFiles();
            
        } catch (error) {
            console.error('Error loading workflow data:', error);
            this.loadFallbackData();
        }
    }

    async loadIndividualFiles() {
        try {
            const filesResponse = await fetch('/api/workflow-files');
            if (!filesResponse.ok) {
                throw new Error('Cannot access workflow files');
            }
            
            const files = await filesResponse.json();
            this.workflowFiles = files;

            // Load each file
            const workflowData = {};
            for (const fileInfo of files) {
                try {
                    const response = await fetch(`/data/${fileInfo.filename}`);
                    if (response.ok) {
                        const data = await response.json();
                        workflowData[fileInfo.filename] = data;
                    }
                } catch (err) {
                    console.warn(`Failed to load ${fileInfo.filename}:`, err);
                }
            }

            this.processWorkflowFiles(workflowData);
            this.lastUpdateTime = new Date();

        } catch (error) {
            console.error('Error loading individual files:', error);
            this.loadFallbackData();
        }
    }

    processAnalyticsData() {
        if (!this.analyticsData) return;

        const data = this.analyticsData;
        
        // Update workflow status
        this.updateWorkflowStatus(data.workflow_analytics);
        
        // Update key metrics
        this.updateKeyMetrics(data.progress_metrics);
        
        // Update charts
        if (window.chartManager) {
            window.chartManager.updateTimeline(data.visualization_dashboard_data?.workflow_progress_chart);
            window.chartManager.updateRadarChart(data.visualization_dashboard_data?.agent_performance_radar);
            window.chartManager.updateFunnelChart(data.visualization_dashboard_data?.issue_resolution_funnel);
            window.chartManager.updateGauges(data.visualization_dashboard_data?.workflow_health_metrics);
        }
        
        // Update sequence table
        this.updateSequenceTable(data.workflow_analytics?.agent_performance);
        
        // Update predictions
        this.updatePredictions(data.predictive_analytics);
        
        // Update last updated time
        this.updateLastUpdatedTime();
    }

    processWorkflowFiles(workflowData) {
        const aggregatedData = this.aggregateWorkflowData(workflowData);
        this.updateDashboardWithAggregated(aggregatedData);
    }

    aggregateWorkflowData(workflowData) {
        const sequences = [];
        let totalIssues = 0;
        let totalRequirements = 0;
        let totalEffortHours = '';
        let papComplianceScore = 0;
        let workflowVelocity = 0;

        // Process each file
        Object.entries(workflowData).forEach(([filename, data]) => {
            if (data.sequence_id) {
                sequences.push({
                    sequence_id: data.sequence_id,
                    agent: data.agent_name,
                    timestamp: data.timestamp,
                    filename: filename,
                    progress_metrics: data.progress_metrics || {}
                });
            }

            // Get latest metrics
            if (data.progress_metrics) {
                totalIssues = data.progress_metrics.coherence_issues_identified || totalIssues;
                totalRequirements = data.progress_metrics.requirements_generated || data.progress_metrics.requirements_validated || totalRequirements;
                totalEffortHours = data.progress_metrics.total_effort_hours_estimated || totalEffortHours;
                papComplianceScore = data.progress_metrics.pap_compliance_score || papComplianceScore;
                workflowVelocity = data.progress_metrics.workflow_completion_percentage || workflowVelocity;
            }
        });

        return {
            sequences: sequences.sort((a, b) => a.sequence_id.localeCompare(b.sequence_id)),
            metrics: {
                totalIssues,
                totalRequirements,
                totalEffortHours,
                papComplianceScore,
                workflowVelocity,
                sequencesCompleted: sequences.length
            }
        };
    }

    updateDashboardWithAggregated(data) {
        // Update metrics with real data
        document.getElementById('papCompliance').textContent = `${data.metrics.papComplianceScore}%`;
        document.getElementById('issuesResolved').textContent = data.metrics.totalIssues;
        document.getElementById('totalEffort').textContent = data.metrics.totalEffortHours;
        document.getElementById('workflowVelocity').textContent = `${data.sequences.length} seq`;

        // Update workflow status
        const statusText = data.sequences.length > 0 ? `Active - ${data.sequences.length} sequences` : 'No Data';
        document.getElementById('statusText').textContent = statusText;

        this.updateSequenceTableFromAggregated(data.sequences);
    }

    updateWorkflowStatus(workflowAnalytics) {
        const statusElement = document.getElementById('statusText');
        const statusIndicator = document.getElementById('workflowStatus');
        
        if (workflowAnalytics?.workflow_status === 'IN_PROGRESS') {
            statusElement.textContent = `In Progress (${workflowAnalytics.completion_percentage}%)`;
            statusIndicator.style.background = '#10b981';
        } else if (workflowAnalytics?.workflow_status) {
            statusElement.textContent = workflowAnalytics.workflow_status;
        }

        // Update progress summary
        if (workflowAnalytics) {
            const progressSummary = document.getElementById('progressSummary');
            progressSummary.innerHTML = `
                <span class="progress-badge">${workflowAnalytics.sequences_completed || 0}/${workflowAnalytics.total_estimated_sequences || 5} Sequences</span>
                <span class="progress-badge">${workflowAnalytics.completion_percentage || 0}% Complete</span>
            `;
        }
    }

    updateKeyMetrics(progressMetrics) {
        if (!progressMetrics) return;

        // PAP Compliance
        const papElement = document.getElementById('papCompliance');
        papElement.textContent = `${progressMetrics.pap_compliance_score || 0}%`;
        
        // Issues Resolved  
        const issuesElement = document.getElementById('issuesResolved');
        issuesElement.textContent = progressMetrics.coherence_issues_identified || 0;
        
        // Total Effort
        const effortElement = document.getElementById('totalEffort');
        const effortHours = progressMetrics.total_effort_hours_estimated || '0';
        effortElement.textContent = effortHours.toString().split('-')[0] + 'h';
        
        // Workflow Velocity
        const velocityElement = document.getElementById('workflowVelocity');
        velocityElement.textContent = `${progressMetrics.requirements_generated || progressMetrics.requirements_validated || 0} req`;
    }

    updateSequenceTable(agentPerformance) {
        if (!agentPerformance) return;
        
        const tableContainer = document.getElementById('sequencesTable');
        
        const sequences = Object.entries(agentPerformance).map(([key, data]) => {
            const sequenceId = key.split('_')[0];
            return {
                sequence: sequenceId,
                agent: key.split('_').slice(1).join(' ').replace('_', ' '),
                duration: `${data.execution_time_minutes?.toFixed(1) || 0}m`,
                score: data.output_quality_score || 0,
                rating: data.performance_rating || 'UNKNOWN',
                deliverable: data.issues_identified || data.requirements_generated || data.enhancements_added || '--'
            };
        });

        const table = `
            <table>
                <thead>
                    <tr>
                        <th>Sequence</th>
                        <th>Agent</th>
                        <th>Duration</th>
                        <th>Quality Score</th>
                        <th>Output</th>
                        <th>Rating</th>
                    </tr>
                </thead>
                <tbody>
                    ${sequences.map(seq => `
                        <tr>
                            <td>${seq.sequence}</td>
                            <td>${seq.agent}</td>
                            <td>${seq.duration}</td>
                            <td>${seq.score}%</td>
                            <td>${seq.deliverable}</td>
                            <td><span class="rating-${seq.rating.toLowerCase()}">${seq.rating}</span></td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        tableContainer.innerHTML = table;
    }

    updateSequenceTableFromAggregated(sequences) {
        const tableContainer = document.getElementById('sequencesTable');
        
        const table = `
            <table>
                <thead>
                    <tr>
                        <th>Sequence</th>
                        <th>Agent</th>
                        <th>Timestamp</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    ${sequences.map(seq => `
                        <tr>
                            <td>${seq.sequence_id}</td>
                            <td>${seq.agent.replace('_agent', '').replace(/_/g, ' ')}</td>
                            <td>${new Date(seq.timestamp).toLocaleTimeString()}</td>
                            <td><span class="rating-excellent">COMPLETED</span></td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        tableContainer.innerHTML = table;
    }

    updatePredictions(predictiveAnalytics) {
        if (!predictiveAnalytics) return;
        
        const completionElement = document.getElementById('estimatedCompletion');
        if (predictiveAnalytics.estimated_completion?.projected_completion) {
            completionElement.textContent = new Date(predictiveAnalytics.estimated_completion.projected_completion).toLocaleString();
        }
        
        const riskContainer = document.getElementById('riskIndicators');
        if (predictiveAnalytics.risk_indicators) {
            riskContainer.innerHTML = predictiveAnalytics.risk_indicators.map(risk => `
                <div class="risk-item ${risk.impact?.toLowerCase() || 'medium'}">
                    <strong>${risk.risk || 'Unknown Risk'}</strong>
                    <div>Probability: ${((risk.probability || 0) * 100).toFixed(0)}% | Impact: ${risk.impact || 'UNKNOWN'}</div>
                    <div>Mitigation: ${risk.mitigation || 'None specified'}</div>
                </div>
            `).join('');
        }
    }

    updateLastUpdatedTime() {
        const element = document.getElementById('lastUpdated');
        element.textContent = this.lastUpdateTime ? this.lastUpdateTime.toLocaleTimeString() : '--:--';
    }

    loadFallbackData() {
        // Show loading state instead of fake data
        console.warn('Loading fallback state - real workflow files not accessible');
        
        document.getElementById('statusText').textContent = 'No Data Available';
        document.getElementById('estimatedCompletion').textContent = 'Run workflow to generate data';
        
        ['papCompliance', 'issuesResolved', 'totalEffort', 'workflowVelocity'].forEach(id => {
            document.getElementById(id).textContent = '--';
        });
    }

    startAutoRefresh() {
        setInterval(() => {
            this.loadWorkflowData();
        }, this.refreshInterval);
    }

    async refresh() {
        const elements = document.querySelectorAll('.dashboard-card');
        elements.forEach(el => el.classList.add('loading'));
        
        await this.loadWorkflowData();
        
        elements.forEach(el => el.classList.remove('loading'));
    }
}

// Initialize data loader when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.dataLoader = new WorkflowDataLoader();
});