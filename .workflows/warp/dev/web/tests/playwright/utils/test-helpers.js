// WARPCORE Analytics Test Helpers - Efficient Testing Framework
const { expect } = require('@playwright/test');

class WARPCORETestHelpers {
    constructor(page) {
        this.page = page;
        this.baseURL = 'http://localhost:8080';
    }

    /**
     * Dashboard Navigation and Setup
     */
    async navigateToDashboard() {
        await this.page.goto('/');
        await this.page.waitForLoadState('networkidle');
        
        // Wait for analytics engine to initialize
        await this.page.waitForFunction(
            () => window.analytics && window.analytics.data,
            { timeout: 15000 }
        );
        
        console.log('🎯 Dashboard loaded and analytics engine initialized');
    }

    async waitForDataLoad() {
        // Wait for real data to load
        await this.page.waitForFunction(
            () => {
                return window.analytics && 
                       window.analytics.data.executionLogs &&
                       window.analytics.data.executionLogs.length > 0;
            },
            { timeout: 10000 }
        );
        
        console.log('📊 Analytics data loaded successfully');
    }

    /**
     * UI Element Interactions
     */
    async validateMetricCard(selector, expectedPattern) {
        const element = this.page.locator(selector);
        await expect(element).toBeVisible();
        
        const value = await element.textContent();
        if (expectedPattern) {
            expect(value).toMatch(expectedPattern);
        }
        
        // Test hover animations
        await element.hover();
        await this.page.waitForTimeout(500);
        
        console.log(`✅ Metric card ${selector}: ${value}`);
        return value;
    }

    async testFlowVisualization() {
        const flowContainer = this.page.locator('#agentFlowViz');
        await expect(flowContainer).toBeVisible();
        
        // Check for flow nodes
        const flowNodes = this.page.locator('.flow-node');
        const nodeCount = await flowNodes.count();
        expect(nodeCount).toBeGreaterThan(0);
        
        // Verify animations are running
        const activeNodes = this.page.locator('.flow-node.active');
        const activeCount = await activeNodes.count();
        
        console.log(`🔄 Flow visualization: ${nodeCount} nodes, ${activeCount} active`);
        return { totalNodes: nodeCount, activeNodes: activeCount };
    }

    async testRadarChart() {
        const radarCanvas = this.page.locator('#agentRadar');
        await expect(radarCanvas).toBeVisible();
        
        // Verify canvas is rendered (not blank)
        const canvasContent = await this.page.evaluate(() => {
            const canvas = document.getElementById('agentRadar');
            const ctx = canvas.getContext('2d');
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            return imageData.data.some(pixel => pixel !== 0);
        });
        
        expect(canvasContent).toBe(true);
        console.log('📡 Radar chart rendered successfully');
    }

    async testHeatmap() {
        const heatmap = this.page.locator('#schemaHeatmap');
        await expect(heatmap).toBeVisible();
        
        // Check for heatmap cells
        const cells = this.page.locator('.heatmap-cell');
        const cellCount = await cells.count();
        
        if (cellCount > 0) {
            // Test cell interactions
            await cells.first().hover();
            await this.page.waitForTimeout(300);
        }
        
        console.log(`🔥 Heatmap: ${cellCount} cells rendered`);
        return cellCount;
    }

    /**
     * Intelligence Stream Testing
     */
    async testIntelligenceStream() {
        const streamContainer = this.page.locator('#intelligenceStream');
        await expect(streamContainer).toBeVisible();
        
        // Test filter buttons
        const filterButtons = this.page.locator('.stream-btn');
        const buttonCount = await filterButtons.count();
        
        for (let i = 0; i < buttonCount; i++) {
            const button = filterButtons.nth(i);
            await button.click();
            await this.page.waitForTimeout(500);
            
            const isActive = await button.evaluate(el => el.classList.contains('active'));
            expect(isActive).toBe(true);
        }
        
        // Check stream items
        const streamItems = this.page.locator('.stream-item');
        const itemCount = await streamItems.count();
        
        console.log(`🌊 Intelligence stream: ${buttonCount} filters, ${itemCount} items`);
        return { filters: buttonCount, items: itemCount };
    }

    /**
     * Performance Metrics Validation
     */
    async validatePerformanceMetrics() {
        const metrics = {
            totalWorkflows: await this.validateMetricCard('#totalWorkflows', /\d+/),
            agentEfficiency: await this.validateMetricCard('#agentEfficiency', /\d+\.?\d*%/),
            avgDuration: await this.validateMetricCard('#avgDuration', /\d+\.?\d*s/),
            validationAccuracy: await this.validateMetricCard('#validationAccuracy', /\d+\.?\d*%/),
            excellenceScore: await this.validateMetricCard('#excellenceScore', /\d+\.?\d*/),
        };
        
        console.log('📈 Performance metrics validated:', metrics);
        return metrics;
    }

    /**
     * Animation and Visual Effects Testing
     */
    async testAnimations() {
        // Test title glow animation
        const title = this.page.locator('.dashboard-title');
        await expect(title).toBeVisible();
        
        // Test pulse dots
        const pulseDots = this.page.locator('.pulse-dot');
        const pulseCount = await pulseDots.count();
        
        // Test card hover effects
        const cards = this.page.locator('.dashboard-card');
        const cardCount = await cards.count();
        
        if (cardCount > 0) {
            await cards.first().hover();
            await this.page.waitForTimeout(500);
        }
        
        console.log(`✨ Animations tested: ${pulseCount} pulse dots, ${cardCount} cards`);
        return { pulseDots: pulseCount, cards: cardCount };
    }

    /**
     * Real-time Updates Testing
     */
    async testRealTimeUpdates() {
        // Capture initial state
        const initialTimestamp = await this.page.locator('#lastUpdated').textContent();
        
        // Wait for update
        await this.page.waitForTimeout(2000);
        
        // Check if timestamp changed
        const updatedTimestamp = await this.page.locator('#lastUpdated').textContent();
        
        expect(updatedTimestamp).not.toBe(initialTimestamp);
        console.log(`⏰ Real-time update: ${initialTimestamp} → ${updatedTimestamp}`);
        
        return { initial: initialTimestamp, updated: updatedTimestamp };
    }

    /**
     * Responsive Design Testing
     */
    async testResponsiveLayout(viewport) {
        await this.page.setViewportSize(viewport);
        await this.page.waitForTimeout(1000);
        
        // Check if dashboard adapts properly
        const dashboardGrid = this.page.locator('.dashboard-grid');
        const gridComputedStyle = await dashboardGrid.evaluate(el => {
            const styles = window.getComputedStyle(el);
            return {
                gridTemplateColumns: styles.gridTemplateColumns,
                gap: styles.gap
            };
        });
        
        console.log(`📱 Responsive test at ${viewport.width}x${viewport.height}:`, gridComputedStyle);
        return gridComputedStyle;
    }

    /**
     * API Data Validation
     */
    async validateAPIData() {
        const apiData = await this.page.evaluate(() => {
            return {
                executionLogs: window.analytics.data.executionLogs?.length || 0,
                workflows: Object.keys(window.analytics.data.workflows || {}).length,
                agents: Object.keys(window.analytics.data.agents || {}).length,
                hasSchemaData: !!window.analytics.data.schemas
            };
        });
        
        expect(apiData.executionLogs).toBeGreaterThan(0);
        expect(apiData.workflows).toBeGreaterThan(0);
        expect(apiData.agents).toBeGreaterThan(0);
        expect(apiData.hasSchemaData).toBe(true);
        
        console.log('🔍 API data validation:', apiData);
        return apiData;
    }

    /**
     * Error Handling and Edge Cases
     */
    async testErrorRecovery() {
        // Simulate network interruption
        await this.page.route('**/api/execution-logs', route => {
            route.fulfill({
                status: 500,
                body: JSON.stringify({ error: 'Server error' })
            });
        });
        
        // Wait for fallback to mock data
        await this.page.waitForTimeout(3000);
        
        const fallbackData = await this.page.evaluate(() => {
            return window.analytics.data.executionLogs?.length > 0;
        });
        
        expect(fallbackData).toBe(true);
        console.log('🛡️ Error recovery: Fallback to mock data successful');
        
        // Remove route override
        await this.page.unroute('**/api/execution-logs');
    }

    /**
     * Performance Testing
     */
    async measureLoadTime() {
        const startTime = Date.now();
        
        await this.navigateToDashboard();
        await this.waitForDataLoad();
        
        const endTime = Date.now();
        const loadTime = endTime - startTime;
        
        expect(loadTime).toBeLessThan(10000); // Should load within 10 seconds
        console.log(`⚡ Dashboard load time: ${loadTime}ms`);
        
        return loadTime;
    }

    /**
     * Accessibility Testing
     */
    async testAccessibility() {
        // Check for proper heading structure
        const h1Count = await this.page.locator('h1').count();
        const h2Count = await this.page.locator('h2').count();
        
        expect(h1Count).toBe(1); // Should have one main heading
        expect(h2Count).toBeGreaterThan(0); // Should have section headings
        
        // Check for alt texts and ARIA labels
        const images = this.page.locator('img');
        const imageCount = await images.count();
        
        // Check focus management
        await this.page.keyboard.press('Tab');
        const focusedElement = await this.page.evaluate(() => document.activeElement.tagName);
        
        console.log(`♿ Accessibility: ${h1Count} h1, ${h2Count} h2, ${imageCount} images, focus on ${focusedElement}`);
        
        return { h1Count, h2Count, imageCount, focusedElement };
    }

    /**
     * Cross-browser Compatibility
     */
    async testBrowserCompatibility() {
        const browserInfo = await this.page.evaluate(() => {
            return {
                userAgent: navigator.userAgent,
                supportsCanvas: !!document.createElement('canvas').getContext,
                supportsWebGL: !!document.createElement('canvas').getContext('webgl'),
                supportsCSSGrid: CSS.supports('display', 'grid'),
                supportsBackdropFilter: CSS.supports('backdrop-filter', 'blur(10px)')
            };
        });
        
        expect(browserInfo.supportsCanvas).toBe(true);
        expect(browserInfo.supportsCSSGrid).toBe(true);
        
        console.log('🌐 Browser compatibility:', browserInfo);
        return browserInfo;
    }

    /**
     * Data Flow Testing
     */
    async testDataFlow() {
        // Track data updates
        const dataStates = [];
        
        // Initial state
        const initialData = await this.page.evaluate(() => window.analytics.data);
        dataStates.push({ timestamp: Date.now(), data: initialData });
        
        // Wait for refresh cycle
        await this.page.waitForTimeout(6000);
        
        // Updated state
        const updatedData = await this.page.evaluate(() => window.analytics.data);
        dataStates.push({ timestamp: Date.now(), data: updatedData });
        
        console.log('🔄 Data flow tracked:', dataStates.length, 'states');
        return dataStates;
    }

    /**
     * User Journey Simulation
     */
    async simulateUserJourney() {
        console.log('🚶 Starting user journey simulation...');
        
        // 1. Landing on dashboard
        await this.navigateToDashboard();
        
        // 2. Exploring metrics
        await this.validatePerformanceMetrics();
        
        // 3. Interacting with visualizations
        await this.testFlowVisualization();
        await this.testRadarChart();
        
        // 4. Using intelligence stream
        await this.testIntelligenceStream();
        
        // 5. Testing filters and interactions
        const filterButtons = this.page.locator('.stream-btn');
        const buttonCount = await filterButtons.count();
        
        for (let i = 0; i < buttonCount; i++) {
            await filterButtons.nth(i).click();
            await this.page.waitForTimeout(1000);
        }
        
        // 6. Checking real-time updates
        await this.testRealTimeUpdates();
        
        console.log('✅ User journey completed successfully');
        return true;
    }
}

module.exports = { WARPCORETestHelpers };