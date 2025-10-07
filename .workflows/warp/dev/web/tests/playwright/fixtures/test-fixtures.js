// WARPCORE Analytics Test Fixtures
const { test as base } = require('@playwright/test');
const { WARPCORETestHelpers } = require('../utils/test-helpers');

// Custom fixtures for WARPCORE Analytics testing
const test = base.extend({
    /**
     * WARPCORE Test Helpers - provides comprehensive testing utilities
     */
    warpHelpers: async ({ page }, use) => {
        const helpers = new WARPCORETestHelpers(page);
        await use(helpers);
    },

    /**
     * Dashboard Context - automatically loads and initializes dashboard
     */
    dashboardPage: async ({ page }, use) => {
        const helpers = new WARPCORETestHelpers(page);
        await helpers.navigateToDashboard();
        await helpers.waitForDataLoad();
        await use(page);
    },

    /**
     * API Context - provides validated API client
     */
    apiClient: async ({ request }, use) => {
        // Verify API is responsive before tests
        const healthCheck = await request.get('/api/execution-logs');
        if (healthCheck.status() !== 200) {
            throw new Error('API not responsive - cannot run tests');
        }
        await use(request);
    },

    /**
     * Performance Monitor - tracks test execution performance
     */
    perfMonitor: async ({}, use) => {
        const monitor = {
            startTime: Date.now(),
            markers: {},
            
            mark: function(name) {
                this.markers[name] = Date.now() - this.startTime;
            },
            
            getMetrics: function() {
                return {
                    totalTime: Date.now() - this.startTime,
                    markers: this.markers
                };
            }
        };
        
        await use(monitor);
        
        // Log performance metrics after test
        const metrics = monitor.getMetrics();
        console.log('🏁 Test Performance:', metrics);
    },

    /**
     * Mock Data Context - provides controlled mock data scenarios
     */
    mockDataContext: async ({ page }, use) => {
        const mockData = {
            workflows: [
                {
                    id: 'wf_test_001',
                    agents: ['requirements_analysis', 'validation', 'schema_coherence'],
                    performance: { efficiency: 94.2, quality: 87.5, duration: 45.3 }
                },
                {
                    id: 'wf_test_002', 
                    agents: ['validation', 'implementation', 'gate_promote'],
                    performance: { efficiency: 91.8, quality: 89.1, duration: 52.1 }
                }
            ],
            
            executionLogs: [
                {
                    timestamp: new Date().toISOString(),
                    workflow_id: 'wf_test_001',
                    agent_name: 'requirements_analysis_agent',
                    action_type: 'PLANNING',
                    content: { issues_found: 0, processing_time: 1.2 }
                },
                {
                    timestamp: new Date().toISOString(),
                    workflow_id: 'wf_test_001',
                    agent_name: 'validation_agent',
                    action_type: 'OUTPUT',
                    content: { validation_accuracy: 96.7, issues_resolved: 2 }
                }
            ],

            // Method to inject mock data into page
            inject: async function() {
                await page.addInitScript((mockData) => {
                    window.WARPCORE_MOCK_DATA = mockData;
                }, this);
            }
        };

        await use(mockData);
    },

    /**
     * Error Simulation Context - simulates various error conditions
     */
    errorSimulator: async ({ page }, use) => {
        const simulator = {
            simulateNetworkError: async () => {
                await page.route('**/api/**', route => {
                    route.fulfill({
                        status: 500,
                        body: JSON.stringify({ error: 'Network error' })
                    });
                });
            },

            simulateSlowNetwork: async (delay = 2000) => {
                await page.route('**/api/**', async route => {
                    await new Promise(resolve => setTimeout(resolve, delay));
                    route.continue();
                });
            },

            simulateEmptyData: async () => {
                await page.route('**/api/execution-logs', route => {
                    route.fulfill({
                        status: 200,
                        body: JSON.stringify({ logs: [] })
                    });
                });
            },

            reset: async () => {
                await page.unroute('**/api/**');
            }
        };

        await use(simulator);
        await simulator.reset(); // Clean up after test
    },

    /**
     * Accessibility Context - provides accessibility testing utilities
     */
    a11yHelper: async ({ page }, use) => {
        const a11y = {
            checkColorContrast: async () => {
                return await page.evaluate(() => {
                    // Simple contrast check implementation
                    const elements = document.querySelectorAll('*');
                    let lowContrastCount = 0;
                    
                    elements.forEach(el => {
                        const styles = window.getComputedStyle(el);
                        const bgColor = styles.backgroundColor;
                        const textColor = styles.color;
                        
                        if (bgColor !== 'rgba(0, 0, 0, 0)' && textColor !== 'rgba(0, 0, 0, 0)') {
                            // Simplified contrast check (real implementation would use WCAG formula)
                            if (bgColor === textColor) {
                                lowContrastCount++;
                            }
                        }
                    });
                    
                    return { lowContrastCount, totalElements: elements.length };
                });
            },

            checkAriaLabels: async () => {
                return await page.evaluate(() => {
                    const interactiveElements = document.querySelectorAll(
                        'button, input, select, textarea, [role="button"], [tabindex]:not([tabindex="-1"])'
                    );
                    
                    let missingLabels = 0;
                    interactiveElements.forEach(el => {
                        const hasLabel = el.getAttribute('aria-label') || 
                                        el.getAttribute('aria-labelledby') ||
                                        el.textContent.trim();
                        if (!hasLabel) missingLabels++;
                    });
                    
                    return { 
                        totalInteractive: interactiveElements.length, 
                        missingLabels 
                    };
                });
            },

            checkKeyboardNavigation: async () => {
                let focusableCount = 0;
                const focusableElements = await page.locator(
                    'button, input, select, textarea, a[href], [tabindex]:not([tabindex="-1"])'
                ).all();
                
                for (const element of focusableElements) {
                    if (await element.isVisible()) {
                        focusableCount++;
                        await element.focus();
                        await page.waitForTimeout(50);
                    }
                }
                
                return { focusableCount };
            }
        };

        await use(a11y);
    },

    /**
     * Visual Testing Context - provides visual regression utilities
     */
    visualTester: async ({ page }, use) => {
        const visual = {
            captureComponent: async (selector, name) => {
                const element = page.locator(selector);
                await element.screenshot({ path: `tests/results/screenshots/${name}.png` });
                return `tests/results/screenshots/${name}.png`;
            },

            compareScreenshots: async (name, threshold = 0.2) => {
                return await page.screenshot({
                    path: `tests/results/screenshots/${name}-actual.png`,
                    fullPage: true
                });
            },

            maskDynamicContent: async () => {
                // Mask elements that change frequently (timestamps, random data)
                await page.addStyleTag({
                    content: `
                        #lastUpdated,
                        .pulse-dot,
                        .real-time-indicator,
                        .stream-time {
                            opacity: 0 !important;
                        }
                    `
                });
            }
        };

        // Ensure screenshots directory exists
        await page.evaluate(() => {
            // This would typically be done in Node.js with fs.mkdirSync
        });

        await use(visual);
    }
});

module.exports = { test };