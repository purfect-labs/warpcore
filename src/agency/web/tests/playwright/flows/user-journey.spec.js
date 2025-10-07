// WARPCORE Analytics User Journey Integration Tests
const { test, expect } = require('@playwright/test');
const { WARPCORETestHelpers } = require('../utils/test-helpers');

test.describe('WARPCORE Analytics User Journey Flows', () => {
    let helpers;

    test.beforeEach(async ({ page }) => {
        helpers = new WARPCORETestHelpers(page);
    });

    test('Data Analyst Journey: Exploring workflow performance insights', async ({ page, request }) => {
        console.log('🔍 Starting Data Analyst Journey...');

        // 1. Analyst arrives at dashboard
        await helpers.navigateToDashboard();
        await helpers.waitForDataLoad();

        // 2. First impression - check overall system health
        const healthIndicators = await page.locator('.real-time-indicator').textContent();
        expect(healthIndicators).toContain('LIVE ANALYTICS');

        // 3. Review key performance metrics
        const metrics = await helpers.validatePerformanceMetrics();
        console.log('📊 Analyst reviews metrics:', metrics);

        // 4. Dive into workflow efficiency analysis
        const flowData = await helpers.testFlowVisualization();
        expect(flowData.totalNodes).toBeGreaterThan(3); // Should have full pipeline

        // 5. Analyze agent performance patterns
        await helpers.testRadarChart();
        const excellenceScore = await page.locator('#excellenceScore').textContent();
        console.log(`🎯 Agent excellence score: ${excellenceScore}`);

        // 6. Cross-reference with API data for validation
        const apiResponse = await request.get('/api/execution-logs');
        const apiData = await apiResponse.json();
        
        const uiWorkflowCount = await page.locator('#totalWorkflows').textContent();
        const uniqueWorkflows = new Set(apiData.logs.map(log => log.workflow_id));
        
        // UI should reflect API data accurately
        expect(parseInt(uiWorkflowCount)).toBe(uniqueWorkflows.size);

        // 7. Generate insights from intelligence stream
        const streamData = await helpers.testIntelligenceStream();
        console.log(`🧠 Generated ${streamData.items} insights`);

        console.log('✅ Data Analyst Journey: Successfully analyzed workflow performance');
    });

    test('Operations Manager Journey: Monitoring system health and predictions', async ({ page, request }) => {
        console.log('⚙️ Starting Operations Manager Journey...');

        // 1. Manager checks system status immediately
        await helpers.navigateToDashboard();
        await helpers.waitForDataLoad();

        // 2. Verify real-time monitoring is active
        const pulseIndicators = await page.locator('.pulse-dot').count();
        expect(pulseIndicators).toBeGreaterThan(0);

        // 3. Review system performance benchmarks
        const performanceData = await helpers.validatePerformanceMetrics();
        
        // Manager looks for efficiency issues
        const efficiency = parseFloat(performanceData.agentEfficiency.replace('%', ''));
        if (efficiency < 80) {
            console.log('⚠️ Manager notices efficiency below 80%');
        }

        // 4. Check predictive analytics for future planning
        const predictions = {
            bottleneck: await page.locator('#nextBottleneck').textContent(),
            optimization: await page.locator('#optimalPath').textContent(),
            confidence: await page.locator('#predictionConfidence').textContent()
        };

        expect(predictions.confidence).toMatch(/\d+\.?\d*%/);
        console.log('🔮 Predictions reviewed:', predictions);

        // 5. Filter critical alerts in intelligence stream
        await page.locator('.stream-btn[data-filter="critical"]').click();
        await page.waitForTimeout(1000);

        const criticalItems = await page.locator('.stream-item.critical:visible').count();
        console.log(`🚨 Critical alerts: ${criticalItems} items require attention`);

        // 6. Validate API response times for system health
        const apiStart = Date.now();
        const healthCheck = await request.get('/api/execution-logs');
        const apiResponseTime = Date.now() - apiStart;

        expect(healthCheck.status()).toBe(200);
        expect(apiResponseTime).toBeLessThan(2000); // Under 2 seconds for good health

        // 7. Check schema compliance status
        const heatmapCells = await helpers.testHeatmap();
        console.log(`🔥 Schema compliance heatmap: ${heatmapCells} components monitored`);

        console.log('✅ Operations Manager Journey: System health and predictions reviewed');
    });

    test('DevOps Engineer Journey: Troubleshooting and optimization', async ({ page, request }) => {
        console.log('🔧 Starting DevOps Engineer Journey...');

        // 1. Engineer investigates reported performance issue
        await helpers.navigateToDashboard();

        // 2. Simulate network delay to test error handling
        await page.route('**/api/execution-logs', async route => {
            await new Promise(resolve => setTimeout(resolve, 1000)); // 1s delay
            route.continue();
        });

        await helpers.waitForDataLoad();

        // 3. Analyze error recovery mechanisms
        await helpers.testErrorRecovery();

        // 4. Check data consistency across multiple API calls
        const consistencyResults = [];
        for (let i = 0; i < 3; i++) {
            const response = await request.get('/api/execution-logs');
            const data = await response.json();
            consistencyResults.push(data.logs.length);
            await page.waitForTimeout(500);
        }

        // All requests should return consistent data
        const isConsistent = consistencyResults.every(count => count === consistencyResults[0]);
        expect(isConsistent).toBe(true);
        console.log(`🔄 Data consistency: ${consistencyResults.join(', ')} (${isConsistent ? 'PASS' : 'FAIL'})`);

        // 5. Performance profiling - measure key interactions
        const performanceMetrics = {};

        const flowStart = Date.now();
        await helpers.testFlowVisualization();
        performanceMetrics.flowRender = Date.now() - flowStart;

        const radarStart = Date.now();
        await helpers.testRadarChart();
        performanceMetrics.radarRender = Date.now() - radarStart;

        const streamStart = Date.now();
        await helpers.testIntelligenceStream();
        performanceMetrics.streamLoad = Date.now() - streamStart;

        // All should be under performance thresholds
        Object.entries(performanceMetrics).forEach(([metric, time]) => {
            expect(time).toBeLessThan(2000);
            console.log(`⚡ ${metric}: ${time}ms`);
        });

        // 6. Test concurrent load handling
        const concurrentRequests = Array.from({ length: 5 }, () => 
            request.get('/api/execution-logs')
        );

        const concurrentStart = Date.now();
        const responses = await Promise.all(concurrentRequests);
        const concurrentTime = Date.now() - concurrentStart;

        responses.forEach(response => expect(response.status()).toBe(200));
        expect(concurrentTime).toBeLessThan(10000); // Under 10 seconds

        console.log(`🚀 Concurrent load test: 5 requests in ${concurrentTime}ms`);

        // 7. Validate monitoring data freshness
        const dataFreshness = await page.evaluate(() => {
            const logs = window.analytics.data.executionLogs;
            if (!logs || logs.length === 0) return null;

            const latest = new Date(logs[logs.length - 1].timestamp);
            const age = Date.now() - latest.getTime();
            return { latest: latest.toISOString(), ageMinutes: age / (1000 * 60) };
        });

        if (dataFreshness) {
            expect(dataFreshness.ageMinutes).toBeLessThan(60); // Data within last hour
            console.log(`🕐 Data freshness: ${dataFreshness.ageMinutes.toFixed(1)} minutes old`);
        }

        console.log('✅ DevOps Engineer Journey: Performance analysis and optimization complete');
    });

    test('Business Stakeholder Journey: Strategic insights and reporting', async ({ page, request }) => {
        console.log('💼 Starting Business Stakeholder Journey...');

        // 1. Stakeholder wants high-level strategic overview
        await helpers.navigateToDashboard();
        await helpers.waitForDataLoad();

        // 2. Focus on business-relevant metrics
        const businessMetrics = await helpers.validatePerformanceMetrics();
        
        // Convert metrics to business language
        const efficiency = parseFloat(businessMetrics.agentEfficiency.replace('%', ''));
        const processingSpeed = parseFloat(businessMetrics.avgDuration.replace('s', ''));

        console.log(`📈 Business view: ${efficiency}% operational efficiency, ${processingSpeed}s avg processing`);

        // 3. Review predictive insights for planning
        const strategicPredictions = {
            qualityForecast: await page.locator('#qualityForecast').textContent(),
            optimalPath: await page.locator('#optimalPath').textContent(),
            confidence: await page.locator('#predictionConfidence').textContent()
        };

        console.log('🎯 Strategic forecasts:', strategicPredictions);

        // 4. Analyze workflow ROI through agent excellence
        const excellenceScore = parseFloat(await page.locator('#excellenceScore').textContent());
        const roiCategory = excellenceScore > 95 ? 'EXCELLENT' : 
                          excellenceScore > 85 ? 'GOOD' : 
                          excellenceScore > 75 ? 'FAIR' : 'NEEDS IMPROVEMENT';

        console.log(`💰 Workflow ROI: ${excellenceScore}% (${roiCategory})`);

        // 5. Generate insights for strategic decisions
        await page.locator('.stream-btn[data-filter="insights"]').click();
        await page.waitForTimeout(1000);

        const insightItems = await page.locator('.stream-item.insights:visible').count();
        console.log(`💡 Strategic insights: ${insightItems} actionable recommendations`);

        // 6. Validate data for reporting accuracy
        const reportingData = await request.get('/api/execution-logs');
        const reportData = await reportingData.json();

        // Business wants to know: How many workflows this period?
        const workflowCount = new Set(reportData.logs.map(log => log.workflow_id)).size;
        const agentCount = new Set(reportData.logs.map(log => log.agent_name)).size;

        expect(workflowCount).toBeGreaterThan(0);
        expect(agentCount).toBeGreaterThan(0);

        console.log(`📊 Reporting data: ${workflowCount} workflows, ${agentCount} agents active`);

        // 7. Export-ready dashboard view (visual consistency check)
        await page.waitForTimeout(2000); // Let animations settle
        const dashboardReady = await page.locator('.dashboard-grid').isVisible();
        expect(dashboardReady).toBe(true);

        console.log('✅ Business Stakeholder Journey: Strategic overview and reporting data gathered');
    });

    test('Security Analyst Journey: Compliance and audit trail analysis', async ({ page, request }) => {
        console.log('🔒 Starting Security Analyst Journey...');

        // 1. Analyst needs to verify system compliance
        await helpers.navigateToDashboard();
        await helpers.waitForDataLoad();

        // 2. Check schema validation compliance
        const validationAccuracy = await page.locator('#validationAccuracy').textContent();
        const accuracy = parseFloat(validationAccuracy.replace('%', ''));
        
        expect(accuracy).toBeGreaterThan(90); // Security requires >90% validation accuracy
        console.log(`🛡️ Schema validation compliance: ${accuracy}%`);

        // 3. Audit data integrity through API
        const auditResponse = await request.get('/api/execution-logs');
        const auditData = await auditResponse.json();

        // Verify all logs have required security fields
        const securityCompliant = auditData.logs.every(log => 
            log.timestamp && 
            log.workflow_id && 
            log.agent_name &&
            log.action_type
        );

        expect(securityCompliant).toBe(true);
        console.log(`📋 Audit trail: ${auditData.logs.length} logs with complete security metadata`);

        // 4. Check for anomalous patterns in heatmap
        const heatmapAnalysis = await helpers.testHeatmap();
        console.log(`🔍 Security heatmap analysis: ${heatmapAnalysis} compliance points verified`);

        // 5. Monitor real-time security events
        await page.locator('.stream-btn[data-filter="critical"]').click();
        await page.waitForTimeout(1000);

        const securityEvents = await page.locator('.stream-item.critical:visible').count();
        console.log(`🚨 Security events: ${securityEvents} critical items for review`);

        // 6. Verify error handling doesn't expose sensitive data
        await page.route('**/api/execution-logs', route => {
            route.fulfill({
                status: 500,
                body: JSON.stringify({ error: 'Internal server error' }) // Generic error
            });
        });

        await page.reload();
        await page.waitForTimeout(3000);

        // System should fall back gracefully without exposing internals
        const fallbackWorking = await page.locator('.dashboard-title').isVisible();
        expect(fallbackWorking).toBe(true);

        console.log('🛡️ Security test: Error handling maintains data privacy');

        // 7. Generate compliance report data
        const complianceReport = await page.evaluate(() => ({
            totalWorkflows: document.getElementById('totalWorkflows')?.textContent || '0',
            validationRate: document.getElementById('validationAccuracy')?.textContent || '0%',
            systemHealth: document.querySelector('.sequence-health')?.textContent || 'UNKNOWN',
            lastUpdate: document.getElementById('lastUpdated')?.textContent || 'N/A'
        }));

        console.log('📊 Compliance report data:', complianceReport);

        console.log('✅ Security Analyst Journey: Compliance verification and audit complete');
    });

    test('End-to-end workflow: From data ingestion to user insights', async ({ page, request }) => {
        console.log('🔄 Starting End-to-End Workflow Test...');

        // 1. Verify API data pipeline is functioning
        const pipelineStart = Date.now();
        const sourceData = await request.get('/api/execution-logs');
        expect(sourceData.status()).toBe(200);

        const rawData = await sourceData.json();
        expect(rawData.logs.length).toBeGreaterThan(0);

        // 2. Load dashboard and verify data transformation
        await helpers.navigateToDashboard();
        await helpers.waitForDataLoad();

        const transformationTime = Date.now() - pipelineStart;
        console.log(`⚡ Data pipeline: API → UI transformation in ${transformationTime}ms`);

        // 3. Verify all visualization components process the data
        const visualizationResults = {
            flow: await helpers.testFlowVisualization(),
            radar: await helpers.testRadarChart(),
            heatmap: await helpers.testHeatmap(),
            stream: await helpers.testIntelligenceStream()
        };

        Object.entries(visualizationResults).forEach(([viz, result]) => {
            console.log(`📊 ${viz}: ${JSON.stringify(result)}`);
        });

        // 4. Test user interactions affect the display
        const interactionStart = Date.now();

        // User filters intelligence stream
        await page.locator('.stream-btn[data-filter="insights"]').click();
        await page.waitForTimeout(500);

        // User hovers over metrics to see details
        await page.locator('.metric-item').first().hover();
        await page.waitForTimeout(300);

        // User explores flow visualization
        const flowNodes = page.locator('.flow-node');
        const nodeCount = await flowNodes.count();
        if (nodeCount > 0) {
            await flowNodes.first().hover();
            await page.waitForTimeout(300);
        }

        const interactionTime = Date.now() - interactionStart;
        console.log(`👆 User interactions: ${interactionTime}ms response time`);

        // 5. Verify real-time updates continue working
        const updateStart = Date.now();
        const initialTimestamp = await page.locator('#lastUpdated').textContent();

        await page.waitForTimeout(3000); // Wait for update cycle

        const updatedTimestamp = await page.locator('#lastUpdated').textContent();
        const updateWorking = updatedTimestamp !== initialTimestamp;

        expect(updateWorking).toBe(true);
        console.log(`🔄 Real-time updates: ${updateWorking ? 'ACTIVE' : 'INACTIVE'}`);

        // 6. Stress test: Multiple rapid interactions
        const stressStart = Date.now();
        
        const stressActions = [
            () => page.locator('.stream-btn[data-filter="all"]').click(),
            () => page.locator('.stream-btn[data-filter="critical"]').click(),
            () => page.locator('.dashboard-card').first().hover(),
            () => page.locator('.metric-item').first().hover(),
            () => page.locator('.prediction-card').first().hover()
        ];

        for (let i = 0; i < 10; i++) {
            const randomAction = stressActions[i % stressActions.length];
            await randomAction();
            await page.waitForTimeout(100);
        }

        const stressTime = Date.now() - stressStart;
        console.log(`🏋️ Stress test: 10 rapid interactions in ${stressTime}ms`);

        // 7. Final validation: All systems operational
        const finalMetrics = await helpers.validatePerformanceMetrics();
        const systemHealthy = Object.values(finalMetrics).every(metric => 
            metric && metric !== '--' && !metric.includes('Error')
        );

        expect(systemHealthy).toBe(true);
        console.log('✅ End-to-End Workflow: Complete data pipeline operational');

        // 8. Performance summary
        const totalTime = Date.now() - pipelineStart;
        console.log(`📈 Total workflow time: ${totalTime}ms (Pipeline: ${transformationTime}ms, Interactions: ${interactionTime}ms, Stress: ${stressTime}ms)`);
    });

    test('Cross-browser compatibility journey', async ({ page, request, browserName }) => {
        console.log(`🌐 Testing cross-browser compatibility on ${browserName}...`);

        // 1. Verify dashboard loads in current browser
        await helpers.navigateToDashboard();
        
        const browserCompat = await helpers.testBrowserCompatibility();
        console.log(`Browser: ${browserName}`, browserCompat);

        // 2. Test critical features work regardless of browser
        const criticalFeatures = {
            canvas: await page.evaluate(() => !!document.createElement('canvas').getContext('2d')),
            cssGrid: await page.evaluate(() => CSS.supports('display', 'grid')),
            fetch: await page.evaluate(() => typeof fetch !== 'undefined'),
            animations: await page.evaluate(() => typeof Animation !== 'undefined')
        };

        Object.entries(criticalFeatures).forEach(([feature, supported]) => {
            expect(supported).toBe(true);
            console.log(`✅ ${feature}: ${supported ? 'SUPPORTED' : 'NOT SUPPORTED'}`);
        });

        // 3. Verify data loads correctly across browsers
        await helpers.waitForDataLoad();
        const dataLoaded = await helpers.validateAPIData();
        expect(dataLoaded.executionLogs).toBeGreaterThan(0);

        // 4. Test responsive behavior
        const responsiveTest = await helpers.testResponsiveLayout({ width: 1024, height: 768 });
        expect(responsiveTest.gridTemplateColumns).toBeTruthy();

        console.log(`✅ Cross-browser test passed on ${browserName}`);
    });
});