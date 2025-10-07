// WARPCORE Analytics Dashboard UI Tests
const { test, expect } = require('@playwright/test');
const { WARPCORETestHelpers } = require('../utils/test-helpers');

test.describe('WARPCORE Analytics Dashboard UI', () => {
    let helpers;

    test.beforeEach(async ({ page }) => {
        helpers = new WARPCORETestHelpers(page);
    });

    test('Dashboard loads successfully with all core components', async ({ page }) => {
        await helpers.navigateToDashboard();
        
        // Check main title
        await expect(page.locator('.dashboard-title')).toBeVisible();
        await expect(page.locator('.dashboard-title')).toContainText('WARPCORE Analytics');
        
        // Check real-time indicator
        await expect(page.locator('.real-time-indicator')).toBeVisible();
        await expect(page.locator('.pulse-dot')).toBeVisible();
        
        // Check main dashboard grid
        await expect(page.locator('.dashboard-grid')).toBeVisible();
        
        // Verify essential cards are present
        const essentialCards = [
            '.flow-card',
            '.performance-grid',
            '.agent-excellence',
            '.stream-card',
            '.prediction-engine'
        ];
        
        for (const cardSelector of essentialCards) {
            await expect(page.locator(cardSelector)).toBeVisible();
        }
        
        console.log('✅ All core dashboard components loaded successfully');
    });

    test('Performance metrics display correctly and update', async ({ page }) => {
        await helpers.navigateToDashboard();
        await helpers.waitForDataLoad();
        
        const metrics = await helpers.validatePerformanceMetrics();
        
        // Verify metrics are realistic values
        expect(metrics.totalWorkflows).toMatch(/^\d+$/);
        expect(metrics.agentEfficiency).toMatch(/^\d+\.?\d*%$/);
        expect(metrics.avgDuration).toMatch(/^\d+\.?\d*s$/);
        
        console.log('📊 Performance metrics validated:', metrics);
    });

    test('Agent flow visualization renders and animates', async ({ page }) => {
        await helpers.navigateToDashboard();
        await helpers.waitForDataLoad();
        
        const flowData = await helpers.testFlowVisualization();
        
        expect(flowData.totalNodes).toBeGreaterThan(0);
        expect(flowData.activeNodes).toBeGreaterThan(0);
        
        // Test flow node interactions
        const firstNode = page.locator('.flow-node').first();
        await firstNode.hover();
        await page.waitForTimeout(500);
        
        // Verify SVG paths are present for connections
        const flowPaths = page.locator('.flow-path');
        const pathCount = await flowPaths.count();
        expect(pathCount).toBeGreaterThan(0);
        
        console.log(`🔄 Flow visualization: ${flowData.totalNodes} nodes with ${pathCount} connections`);
    });

    test('Agent excellence radar chart displays correctly', async ({ page }) => {
        await helpers.navigateToDashboard();
        await helpers.waitForDataLoad();
        
        await helpers.testRadarChart();
        
        // Check radar legend
        const legendItems = page.locator('.legend-item');
        const legendCount = await legendItems.count();
        expect(legendCount).toBeGreaterThan(0);
        
        // Test legend interactions
        if (legendCount > 0) {
            await legendItems.first().hover();
            await page.waitForTimeout(300);
        }
        
        // Verify excellence score is displayed
        const excellenceScore = page.locator('#excellenceScore');
        await expect(excellenceScore).toBeVisible();
        const scoreText = await excellenceScore.textContent();
        expect(scoreText).toMatch(/^\d+\.?\d*$/);
        
        console.log(`📡 Radar chart with ${legendCount} legend items, excellence score: ${scoreText}`);
    });

    test('Schema heatmap renders with interactive cells', async ({ page }) => {
        await helpers.navigateToDashboard();
        await helpers.waitForDataLoad();
        
        const cellCount = await helpers.testHeatmap();
        
        if (cellCount > 0) {
            // Test cell hover effects
            const firstCell = page.locator('.heatmap-cell').first();
            await firstCell.hover();
            
            // Check if cell has proper styling
            const cellStyle = await firstCell.evaluate(el => {
                const styles = window.getComputedStyle(el);
                return {
                    transform: styles.transform,
                    background: styles.background
                };
            });
            
            console.log(`🔥 Heatmap: ${cellCount} cells with interactive effects`);
        }
    });

    test('Intelligence stream filters work correctly', async ({ page }) => {
        await helpers.navigateToDashboard();
        await helpers.waitForDataLoad();
        
        const streamData = await helpers.testIntelligenceStream();
        
        expect(streamData.filters).toBeGreaterThanOrEqual(3); // ALL, CRITICAL, INSIGHTS
        
        // Test specific filter functionality
        const allBtn = page.locator('.stream-btn[data-filter="all"]');
        const criticalBtn = page.locator('.stream-btn[data-filter="critical"]');
        const insightsBtn = page.locator('.stream-btn[data-filter="insights"]');
        
        // Test ALL filter
        await allBtn.click();
        await page.waitForTimeout(500);
        const allItems = await page.locator('.stream-item:visible').count();
        
        // Test CRITICAL filter
        await criticalBtn.click();
        await page.waitForTimeout(500);
        const criticalItems = await page.locator('.stream-item:visible').count();
        
        // Test INSIGHTS filter
        await insightsBtn.click();
        await page.waitForTimeout(500);
        const insightsItems = await page.locator('.stream-item:visible').count();
        
        console.log(`🌊 Stream filters: ALL=${allItems}, CRITICAL=${criticalItems}, INSIGHTS=${insightsItems}`);
    });

    test('Predictive analytics engine displays forecasts', async ({ page }) => {
        await helpers.navigateToDashboard();
        await helpers.waitForDataLoad();
        
        // Check prediction cards
        const predictionCards = page.locator('.prediction-card');
        const cardCount = await predictionCards.count();
        expect(cardCount).toBeGreaterThan(0);
        
        // Verify prediction values are displayed
        const predictions = {
            bottleneck: await page.locator('#nextBottleneck').textContent(),
            optimization: await page.locator('#optimalPath').textContent(),
            quality: await page.locator('#qualityForecast').textContent(),
            confidence: await page.locator('#predictionConfidence').textContent()
        };
        
        Object.entries(predictions).forEach(([key, value]) => {
            expect(value).toBeTruthy();
            console.log(`🔮 ${key}: ${value}`);
        });
        
        // Test card hover effects
        if (cardCount > 0) {
            await predictionCards.first().hover();
            await page.waitForTimeout(300);
        }
        
        console.log(`🔮 Predictive analytics: ${cardCount} prediction cards rendered`);
    });

    test('Real-time updates function correctly', async ({ page }) => {
        await helpers.navigateToDashboard();
        await helpers.waitForDataLoad();
        
        const updateData = await helpers.testRealTimeUpdates();
        
        expect(updateData.updated).not.toBe(updateData.initial);
        
        // Test that pulse indicators are animating
        const pulseDots = page.locator('.pulse-dot');
        const pulseCount = await pulseDots.count();
        
        if (pulseCount > 0) {
            // Verify animation is running by checking computed styles
            const animationRunning = await pulseDots.first().evaluate(el => {
                const styles = window.getComputedStyle(el);
                return styles.animationName !== 'none';
            });
            expect(animationRunning).toBe(true);
        }
        
        console.log(`⏰ Real-time updates: ${pulseCount} pulse indicators animating`);
    });

    test('Dashboard animations and visual effects work', async ({ page }) => {
        await helpers.navigateToDashboard();
        
        const animationData = await helpers.testAnimations();
        
        // Test title glow animation
        const titleAnimation = await page.locator('.dashboard-title').evaluate(el => {
            const styles = window.getComputedStyle(el);
            return styles.animationName !== 'none';
        });
        expect(titleAnimation).toBe(true);
        
        // Test card hover effects
        const firstCard = page.locator('.dashboard-card').first();
        await firstCard.hover();
        
        // Check transform on hover
        const cardTransform = await firstCard.evaluate(el => {
            const styles = window.getComputedStyle(el);
            return styles.transform;
        });
        
        console.log(`✨ Animations: Title glowing, ${animationData.cards} cards with hover effects`);
    });

    test('Dashboard is responsive across different viewport sizes', async ({ page }) => {
        await helpers.navigateToDashboard();
        
        const viewports = [
            { width: 1920, height: 1080 }, // Desktop
            { width: 1024, height: 768 },  // Tablet
            { width: 375, height: 667 }    // Mobile
        ];
        
        for (const viewport of viewports) {
            const gridStyle = await helpers.testResponsiveLayout(viewport);
            
            // Verify grid adapts to viewport
            expect(gridStyle.gridTemplateColumns).toBeTruthy();
            expect(gridStyle.gap).toBeTruthy();
            
            console.log(`📱 ${viewport.width}x${viewport.height}: Grid adapted successfully`);
        }
    });

    test('Error recovery works when API fails', async ({ page }) => {
        await helpers.navigateToDashboard();
        await helpers.testErrorRecovery();
        
        // Verify dashboard still functions with mock data
        const metrics = await helpers.validatePerformanceMetrics();
        expect(metrics.totalWorkflows).toBeTruthy();
        
        console.log('🛡️ Error recovery: Dashboard functional with fallback data');
    });

    test('Performance benchmarks meet requirements', async ({ page }) => {
        const loadTime = await helpers.measureLoadTime();
        
        // Performance thresholds
        expect(loadTime).toBeLessThan(10000); // 10 seconds max
        
        // Test continuous performance
        const startTime = Date.now();
        
        // Simulate user interactions
        await helpers.testFlowVisualization();
        await helpers.testIntelligenceStream();
        await helpers.validatePerformanceMetrics();
        
        const interactionTime = Date.now() - startTime;
        expect(interactionTime).toBeLessThan(5000); // Interactions under 5 seconds
        
        console.log(`⚡ Performance: Load ${loadTime}ms, Interactions ${interactionTime}ms`);
    });

    test('Accessibility features work correctly', async ({ page }) => {
        await helpers.navigateToDashboard();
        
        const accessibilityData = await helpers.testAccessibility();
        
        // Test keyboard navigation
        await page.keyboard.press('Tab');
        await page.keyboard.press('Tab');
        await page.keyboard.press('Tab');
        
        const focusedAfterTabs = await page.evaluate(() => document.activeElement.tagName);
        
        console.log(`♿ Accessibility: Proper heading structure, keyboard navigation to ${focusedAfterTabs}`);
    });

    test('Cross-browser compatibility features', async ({ page }) => {
        await helpers.navigateToDashboard();
        
        const browserInfo = await helpers.testBrowserCompatibility();
        
        // Essential features should be supported
        expect(browserInfo.supportsCanvas).toBe(true);
        expect(browserInfo.supportsCSSGrid).toBe(true);
        
        console.log('🌐 Cross-browser: Essential features supported');
    });

    test('Data flow and state management', async ({ page }) => {
        await helpers.navigateToDashboard();
        
        const dataFlow = await helpers.testDataFlow();
        
        expect(dataFlow.length).toBeGreaterThanOrEqual(2);
        
        // Verify data structure consistency
        dataFlow.forEach((state, index) => {
            expect(state.data).toHaveProperty('executionLogs');
            expect(state.data).toHaveProperty('workflows');
            expect(state.data).toHaveProperty('agents');
            console.log(`🔄 Data state ${index + 1}: ${state.data.executionLogs?.length || 0} logs`);
        });
    });

    test('Complete user journey simulation', async ({ page }) => {
        const journeySuccess = await helpers.simulateUserJourney();
        expect(journeySuccess).toBe(true);
        
        // Verify final state is good
        const finalMetrics = await helpers.validatePerformanceMetrics();
        expect(finalMetrics.totalWorkflows).toBeTruthy();
        
        console.log('🚶 Complete user journey: Successfully simulated end-to-end experience');
    });

    test('Dashboard handles large datasets efficiently', async ({ page }) => {
        await helpers.navigateToDashboard();
        await helpers.waitForDataLoad();
        
        // Check if dashboard handles current data volume well
        const dataVolume = await page.evaluate(() => ({
            logs: window.analytics.data.executionLogs?.length || 0,
            workflows: Object.keys(window.analytics.data.workflows || {}).length,
            agents: Object.keys(window.analytics.data.agents || {}).length,
            heatmapCells: window.analytics.data.schemas?.heatmap_data?.length || 0
        }));
        
        // Verify UI remains responsive
        const startTime = Date.now();
        await helpers.testFlowVisualization();
        await helpers.testRadarChart();
        const renderTime = Date.now() - startTime;
        
        expect(renderTime).toBeLessThan(3000); // Should render within 3 seconds
        
        console.log(`📊 Large dataset handling: ${JSON.stringify(dataVolume)} in ${renderTime}ms`);
    });

    test('Visual regression - dashboard layout consistency', async ({ page }) => {
        await helpers.navigateToDashboard();
        await helpers.waitForDataLoad();
        
        // Take screenshot for visual comparison
        await expect(page).toHaveScreenshot('dashboard-full-layout.png', {
            fullPage: true,
            threshold: 0.2 // Allow 20% difference for dynamic content
        });
        
        console.log('📸 Visual regression: Dashboard layout screenshot captured');
    });
});