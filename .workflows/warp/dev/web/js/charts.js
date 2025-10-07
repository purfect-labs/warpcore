// WARPCORE Charts Manager - Real Data Visualizations

class ChartManager {
    constructor() {
        this.charts = {};
        this.initializeCharts();
    }

    initializeCharts() {
        this.initializeTimelineChart();
        this.initializeRadarChart();
        this.initializeGauges();
        this.initializeFunnelChart();
    }

    // Timeline Chart for Workflow Progress
    initializeTimelineChart() {
        const ctx = document.getElementById('timelineChart').getContext('2d');
        
        this.charts.timeline = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Execution Time (minutes)',
                    data: [],
                    backgroundColor: 'rgba(0, 212, 255, 0.6)',
                    borderColor: 'rgba(0, 212, 255, 1)',
                    borderWidth: 1
                }, {
                    label: 'Quality Score',
                    data: [],
                    type: 'line',
                    yAxisID: 'y1',
                    backgroundColor: 'rgba(124, 58, 237, 0.2)',
                    borderColor: 'rgba(124, 58, 237, 1)',
                    borderWidth: 2,
                    fill: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#f8fafc'
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: '#94a3b8'
                        },
                        grid: {
                            color: 'rgba(0, 212, 255, 0.1)'
                        }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: '#94a3b8'
                        },
                        grid: {
                            color: 'rgba(0, 212, 255, 0.1)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            color: '#94a3b8'
                        },
                        grid: {
                            drawOnChartArea: false,
                        }
                    }
                }
            }
        });
    }

    // Agent Performance Radar Chart
    initializeRadarChart() {
        const ctx = document.getElementById('radarChart').getContext('2d');
        
        this.charts.radar = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['Speed', 'Accuracy', 'Completeness', 'Innovation', 'Efficiency'],
                datasets: []
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#f8fafc'
                        }
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            color: '#94a3b8',
                            backdropColor: 'transparent'
                        },
                        grid: {
                            color: 'rgba(0, 212, 255, 0.2)'
                        },
                        angleLines: {
                            color: 'rgba(0, 212, 255, 0.2)'
                        },
                        pointLabels: {
                            color: '#f8fafc'
                        }
                    }
                }
            }
        });
    }

    // Gauge Charts for Health Metrics
    initializeGauges() {
        this.initializeGauge('complianceGauge', 'PAP Compliance', '#10b981');
        this.initializeGauge('resolutionGauge', 'Resolution Rate', '#00d4ff');
        this.initializeGauge('velocityGauge', 'Velocity', '#7c3aed');
    }

    initializeGauge(canvasId, label, color) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        this.charts[canvasId] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [0, 100],
                    backgroundColor: [color, 'rgba(255, 255, 255, 0.1)'],
                    borderWidth: 0,
                    cutout: '70%'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        enabled: false
                    }
                },
                circumference: 180,
                rotation: -90
            },
            plugins: [{
                id: 'gaugeText',
                beforeDraw: (chart) => {
                    const { ctx, chartArea } = chart;
                    const value = chart.data.datasets[0].data[0];
                    
                    ctx.save();
                    ctx.font = 'bold 16px Inter';
                    ctx.fillStyle = color;
                    ctx.textAlign = 'center';
                    ctx.fillText(
                        `${value}%`, 
                        chartArea.left + (chartArea.right - chartArea.left) / 2,
                        chartArea.top + (chartArea.bottom - chartArea.top) / 2 + 10
                    );
                    ctx.restore();
                }
            }]
        });
    }

    // Funnel Chart using D3.js
    initializeFunnelChart() {
        this.createFunnelChart([]);
    }

    // Update Methods for Real Data
    updateTimeline(timelineData) {
        if (!timelineData || !timelineData.data) return;

        const chart = this.charts.timeline;
        const data = timelineData.data;

        chart.data.labels = data.map(item => item.sequence);
        chart.data.datasets[0].data = data.map(item => item.duration_minutes || 0);
        chart.data.datasets[1].data = data.map(item => item.output_score || 0);
        
        chart.update('none');
    }

    updateRadarChart(radarData) {
        if (!radarData || !radarData.agents) return;

        const chart = this.charts.radar;
        const colors = [
            { bg: 'rgba(0, 212, 255, 0.2)', border: 'rgba(0, 212, 255, 1)' },
            { bg: 'rgba(16, 185, 129, 0.2)', border: 'rgba(16, 185, 129, 1)' },
            { bg: 'rgba(124, 58, 237, 0.2)', border: 'rgba(124, 58, 237, 1)' }
        ];

        chart.data.datasets = radarData.agents.map((agent, index) => ({
            label: agent.agent,
            data: [
                agent.metrics?.speed || 0,
                agent.metrics?.accuracy || 0,
                agent.metrics?.completeness || 0,
                agent.metrics?.innovation || 0,
                agent.metrics?.efficiency || 0
            ],
            backgroundColor: colors[index]?.bg || 'rgba(255, 255, 255, 0.2)',
            borderColor: colors[index]?.border || '#ffffff',
            borderWidth: 2,
            pointBackgroundColor: colors[index]?.border || '#ffffff'
        }));

        chart.update('none');
    }

    updateGauges(healthMetrics) {
        if (!healthMetrics || !healthMetrics.metrics) return;

        healthMetrics.metrics.forEach(metric => {
            let canvasId;
            switch (metric.name) {
                case 'PAP Compliance':
                    canvasId = 'complianceGauge';
                    break;
                case 'Issue Resolution Rate':
                    canvasId = 'resolutionGauge';
                    break;
                case 'Workflow Velocity':
                    canvasId = 'velocityGauge';
                    break;
            }

            if (canvasId && this.charts[canvasId]) {
                this.updateSingleGauge(canvasId, metric.current_value || 0);
            }
        });
    }

    updateSingleGauge(canvasId, value) {
        const chart = this.charts[canvasId];
        chart.data.datasets[0].data = [value, 100 - value];
        chart.update('none');
    }

    updateFunnelChart(funnelData) {
        if (!funnelData || !funnelData.stages) return;
        this.createFunnelChart(funnelData.stages);
    }

    createFunnelChart(stages) {
        const container = d3.select('#funnelChart');
        container.selectAll('*').remove();

        if (!stages || stages.length === 0) {
            container.append('div')
                .style('text-align', 'center')
                .style('color', '#94a3b8')
                .style('padding', '50px')
                .text('No funnel data available');
            return;
        }

        const svg = container.append('svg')
            .attr('width', '100%')
            .attr('height', '300px');

        const containerWidth = container.node().offsetWidth;
        const margin = { top: 20, right: 20, bottom: 20, left: 20 };
        const width = containerWidth - margin.left - margin.right;
        const height = 260;

        const g = svg.append('g')
            .attr('transform', `translate(${margin.left},${margin.top})`);

        const maxCount = Math.max(...stages.map(s => s.count));
        
        stages.forEach((stage, index) => {
            const stageHeight = 40;
            const stageWidth = (stage.count / maxCount) * width;
            const y = index * (stageHeight + 10);
            
            // Create funnel stage
            const stageGroup = g.append('g')
                .attr('class', 'funnel-stage-group');
            
            // Background rectangle
            stageGroup.append('rect')
                .attr('x', (width - stageWidth) / 2)
                .attr('y', y)
                .attr('width', stageWidth)
                .attr('height', stageHeight)
                .attr('rx', 4)
                .attr('fill', stage.color || '#00d4ff')
                .attr('opacity', 0.8)
                .style('cursor', 'pointer')
                .on('mouseover', function() {
                    d3.select(this).attr('opacity', 1);
                })
                .on('mouseout', function() {
                    d3.select(this).attr('opacity', 0.8);
                });

            // Stage text
            stageGroup.append('text')
                .attr('x', width / 2)
                .attr('y', y + stageHeight / 2)
                .attr('dy', '0.35em')
                .attr('text-anchor', 'middle')
                .attr('fill', 'white')
                .attr('font-weight', '500')
                .attr('font-size', '14px')
                .text(`${stage.stage}: ${stage.count}`);

            // Percentage text
            stageGroup.append('text')
                .attr('x', width / 2)
                .attr('y', y + stageHeight / 2 + 15)
                .attr('dy', '0.35em')
                .attr('text-anchor', 'middle')
                .attr('fill', 'white')
                .attr('font-size', '12px')
                .attr('opacity', 0.8)
                .text(`${(stage.percentage || 0).toFixed(1)}%`);
        });
    }

    // Utility method to destroy all charts (for cleanup)
    destroyCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart && chart.destroy) {
                chart.destroy();
            }
        });
        this.charts = {};
    }

    // Method to update all charts with new data
    updateAllCharts(dashboardData) {
        if (dashboardData?.workflow_progress_chart) {
            this.updateTimeline(dashboardData.workflow_progress_chart);
        }
        
        if (dashboardData?.agent_performance_radar) {
            this.updateRadarChart(dashboardData.agent_performance_radar);
        }
        
        if (dashboardData?.issue_resolution_funnel) {
            this.updateFunnelChart(dashboardData.issue_resolution_funnel);
        }
        
        if (dashboardData?.workflow_health_metrics) {
            this.updateGauges(dashboardData.workflow_health_metrics);
        }
    }
}

// Initialize chart manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.chartManager = new ChartManager();
});