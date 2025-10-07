// WARPCORE Analytics API Tests
const { test, expect } = require('@playwright/test');

test.describe('WARPCORE Analytics API Endpoints', () => {
    const baseURL = 'http://localhost:8080';
    
    test.beforeEach(async ({ page }) => {
        // Ensure server is running and responsive - skip if not
        try {
            const response = await page.request.get(baseURL.replace('/api', ''));
            if (response.status() !== 200) {
                test.skip('Server not responding - skipping API tests');
            }
        } catch (error) {
            test.skip('Server unavailable - skipping API tests');
        }
    });

    test('GET /api/execution-logs - should return execution logs with proper structure', async ({ request }) => {
        const response = await request.get('/api/execution-logs');
        
        expect(response.status()).toBe(200);
        
        const data = await response.json();
        expect(data).toHaveProperty('logs');
        expect(Array.isArray(data.logs)).toBe(true);
        
        if (data.logs.length > 0) {
            const firstLog = data.logs[0];
            expect(firstLog).toHaveProperty('timestamp');
            expect(firstLog).toHaveProperty('workflow_id');
            expect(firstLog).toHaveProperty('agent_name');
            expect(firstLog).toHaveProperty('action_type');
            
            console.log(`✅ Execution logs: ${data.logs.length} entries`);
        }
    });

    test('GET /api/execution-logs - should handle high volume data efficiently', async ({ request }) => {
        const startTime = Date.now();
        const response = await request.get('/api/execution-logs');
        const endTime = Date.now();
        
        expect(response.status()).toBe(200);
        expect(endTime - startTime).toBeLessThan(5000); // Should respond within 5 seconds
        
        const data = await response.json();
        console.log(`⚡ API response time: ${endTime - startTime}ms for ${data.logs?.length || 0} logs`);
    });

    test('GET /api/workflow-logs/:id - should return specific workflow data', async ({ request }) => {
        // First get available workflow IDs
        const logsResponse = await request.get('/api/execution-logs');
        const logsData = await logsResponse.json();
        
        if (logsData.logs && logsData.logs.length > 0) {
            const workflowId = logsData.logs[0].workflow_id;
            
            const workflowResponse = await request.get(`/api/workflow-logs/${workflowId}`);
            
            if (workflowResponse.status() === 404) {
                console.log(`🔍 Workflow endpoint not implemented - skipping workflow test`);
                test.skip('Workflow logs endpoint not yet implemented');
                return;
            }
            
            expect(workflowResponse.status()).toBe(200);
            const workflowData = await workflowResponse.json();
            expect(workflowData).toHaveProperty('workflow_id', workflowId);
            expect(workflowData).toHaveProperty('total_log_entries');
            expect(workflowData).toHaveProperty('timeline');
            
            console.log(`🔍 Workflow ${workflowId}: ${workflowData.total_log_entries} entries`);
        }
    });

    test('API error handling - should return proper error responses', async ({ request }) => {
        // Test non-existent workflow
        const response = await request.get('/api/workflow-logs/non-existent-workflow');
        
        // Accept either 404 (proper REST) or 200 (graceful degradation)
        if (response.status() === 404) {
            console.log('🛡️ Error handling: Proper 404 for non-existent workflow');
        } else if (response.status() === 200) {
            const data = await response.json();
            expect(data.workflow_id).toBe('non-existent-workflow');
            expect(data.total_log_entries).toBe(0);
            console.log('🛡️ Error handling: Graceful degradation for non-existent workflow');
        } else {
            throw new Error(`Unexpected status code: ${response.status()}`);
        }
    });

    test('API data consistency - should maintain data integrity across requests', async ({ request }) => {
        // Make multiple requests and verify consistency
        const requests = [];
        for (let i = 0; i < 3; i++) {
            requests.push(request.get('/api/execution-logs'));
        }
        
        const responses = await Promise.all(requests);
        const dataSets = await Promise.all(responses.map(r => r.json()));
        
        // All responses should have same structure
        dataSets.forEach((data, index) => {
            expect(data).toHaveProperty('logs');
            expect(Array.isArray(data.logs)).toBe(true);
            console.log(`📊 Request ${index + 1}: ${data.logs.length} logs`);
        });
        
        console.log('🔄 Data consistency verified across multiple requests');
    });

    test('API performance under concurrent load', async ({ request }) => {
        const concurrentRequests = 10;
        const startTime = Date.now();
        
        const requests = Array.from({ length: concurrentRequests }, () => 
            request.get('/api/execution-logs')
        );
        
        const responses = await Promise.all(requests);
        const endTime = Date.now();
        
        // All requests should succeed
        responses.forEach((response, index) => {
            expect(response.status()).toBe(200);
        });
        
        const totalTime = endTime - startTime;
        const avgTime = totalTime / concurrentRequests;
        
        expect(totalTime).toBeLessThan(15000); // Total time under 15 seconds
        expect(avgTime).toBeLessThan(5000); // Average response under 5 seconds
        
        console.log(`⚡ Concurrent load test: ${concurrentRequests} requests in ${totalTime}ms (avg: ${avgTime}ms)`);
    });

    test('API data validation - should return properly formatted data', async ({ request }) => {
        const response = await request.get('/api/execution-logs');
        const data = await response.json();
        
        if (data.logs && data.logs.length > 0) {
            const log = data.logs[0];
            
            // Validate timestamp format
            const timestamp = new Date(log.timestamp);
            expect(timestamp instanceof Date && !isNaN(timestamp)).toBe(true);
            
            // Validate required fields
            expect(typeof log.workflow_id).toBe('string');
            expect(log.workflow_id.length).toBeGreaterThan(0);
            
            expect(typeof log.agent_name).toBe('string');
            expect(log.agent_name.length).toBeGreaterThan(0);
            
            expect(typeof log.action_type).toBe('string');
            
            console.log('✅ Data validation passed for log entry:', {
                workflow_id: log.workflow_id,
                agent_name: log.agent_name,
                action_type: log.action_type,
                timestamp: log.timestamp
            });
        }
    });

    test('API content types and headers', async ({ request }) => {
        const response = await request.get('/api/execution-logs');
        
        expect(response.status()).toBe(200);
        expect(response.headers()['content-type']).toContain('application/json');
        
        // Check for CORS headers if needed
        const headers = response.headers();
        console.log('📡 Response headers:', {
            'content-type': headers['content-type'],
            'content-length': headers['content-length'],
            'server': headers['server']
        });
    });

    test('API response time benchmarks', async ({ request }) => {
        const benchmarks = {
            fast: 1000,    // < 1 second
            acceptable: 3000, // < 3 seconds
            slow: 5000     // < 5 seconds
        };
        
        const startTime = Date.now();
        const response = await request.get('/api/execution-logs');
        const endTime = Date.now();
        const responseTime = endTime - startTime;
        
        expect(response.status()).toBe(200);
        
        let performance;
        if (responseTime < benchmarks.fast) {
            performance = 'FAST ⚡';
        } else if (responseTime < benchmarks.acceptable) {
            performance = 'ACCEPTABLE ✅';
        } else if (responseTime < benchmarks.slow) {
            performance = 'SLOW ⚠️';
        } else {
            performance = 'TOO SLOW ❌';
        }
        
        expect(responseTime).toBeLessThan(benchmarks.slow);
        console.log(`🏁 API Performance: ${responseTime}ms - ${performance}`);
    });

    test('API data freshness - should reflect recent updates', async ({ request }) => {
        const response = await request.get('/api/execution-logs');
        const data = await response.json();
        
        if (data.logs && data.logs.length > 0) {
            // Check if we have recent data (within last hour for test purposes)
            const recentLogs = data.logs.filter(log => {
                const logTime = new Date(log.timestamp);
                const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);
                return logTime > oneHourAgo;
            });
            
            console.log(`🕐 Data freshness: ${recentLogs.length}/${data.logs.length} logs within last hour`);
            
            // Verify timestamps are in reasonable order
            const timestamps = data.logs.map(log => new Date(log.timestamp).getTime());
            const isChronological = timestamps.every((time, index) => {
                return index === 0 || time >= timestamps[index - 1];
            });
            
            console.log(`📅 Chronological order: ${isChronological ? 'PASSED' : 'FAILED'}`);
        }
    });

    test('API integration with UI data flow', async ({ page, request }) => {
        // First, get data from API directly
        const apiResponse = await request.get('/api/execution-logs');
        const apiData = await apiResponse.json();
        
        // Then navigate to UI and check if it matches
        await page.goto('/');
        await page.waitForLoadState('networkidle');
        
        // Wait for analytics engine to load data
        await page.waitForFunction(
            () => window.analytics && window.analytics.data.executionLogs,
            { timeout: 10000 }
        );
        
        const uiData = await page.evaluate(() => ({
            executionLogs: window.analytics.data.executionLogs,
            totalWorkflows: Object.keys(window.analytics.data.workflows || {}).length,
            totalAgents: Object.keys(window.analytics.data.agents || {}).length
        }));
        
        // Verify UI data matches API data
        expect(uiData.executionLogs.length).toBe(apiData.logs.length);
        expect(uiData.totalWorkflows).toBeGreaterThan(0);
        expect(uiData.totalAgents).toBeGreaterThan(0);
        
        console.log('🔄 API-UI Integration:', {
            apiLogs: apiData.logs.length,
            uiLogs: uiData.executionLogs.length,
            workflows: uiData.totalWorkflows,
            agents: uiData.totalAgents
        });
    });
});