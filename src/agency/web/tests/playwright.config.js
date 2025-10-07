// WARPCORE Analytics Dashboard - Playwright Test Configuration
const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './playwright',
  
  // Test execution configuration
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 0, // No retries - fail fast
  workers: process.env.CI ? 1 : undefined,
  maxFailures: process.env.CI ? 0 : 1, // Stop after first failure in dev
  
  // Reporting
  reporter: [
    ['html', { outputFolder: 'tests/results/html-report' }],
    ['json', { outputFile: 'tests/results/test-results.json' }],
    ['junit', { outputFile: 'tests/results/junit.xml' }],
    ['line']
  ],
  
  // Global test configuration
  use: {
    baseURL: 'http://localhost:8080',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 10000,
    navigationTimeout: 30000,
  },

  // Test projects for different browsers and scenarios
  projects: [
    {
      name: 'setup',
      testMatch: '**/setup/*.spec.js',
    },
    
    // Desktop browsers
    {
      name: 'chrome-desktop',
      use: { 
        ...devices['Desktop Chrome'],
        viewport: { width: 1920, height: 1080 }
      },
      dependencies: ['setup'],
    },
    
    {
      name: 'firefox-desktop',
      use: { 
        ...devices['Desktop Firefox'],
        viewport: { width: 1920, height: 1080 }
      },
      dependencies: ['setup'],
    },
    
    // Mobile devices
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
      dependencies: ['setup'],
    },
    
    // API-only tests
    {
      name: 'api-tests',
      testMatch: '**/api/*.spec.js',
      use: {
        baseURL: 'http://localhost:8080/api',
      },
      dependencies: ['setup'],
    },
    
    // Integration flows
    {
      name: 'user-flows',
      testMatch: '**/flows/*.spec.js',
      use: { 
        ...devices['Desktop Chrome'],
        viewport: { width: 1920, height: 1080 }
      },
      dependencies: ['setup'],
    }
  ],

  // Web server configuration
  webServer: {
    command: 'cd .. && nohup python3 server.py > /tmp/playwright_server.log 2>&1 &',
    port: 8080,
    reuseExistingServer: !process.env.CI,
    timeout: 30000,
    ignoreHTTPSErrors: true,
  },
});