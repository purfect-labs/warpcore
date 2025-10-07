/**
 * WARP PAP Flow Testing - Playwright Configuration
 * Tests run in /tmp context for automatic cleanup
 */

const { defineConfig } = require('@playwright/test');
const path = require('path');
const os = require('os');

// Create temporary test directory in /tmp for automatic cleanup
const tmpTestDir = path.join(os.tmpdir(), `warp-e2e-tests-${Date.now()}`);

module.exports = defineConfig({
  // Test directory
  testDir: '.',
  
  // Run tests in parallel
  fullyParallel: true,
  
  // Fail build on CI if any test failed
  forbidOnly: !!process.env.CI,
  
  // Retry failed tests
  retries: process.env.CI ? 2 : 1,
  
  // Test workers
  workers: process.env.CI ? 1 : undefined,
  
  // Global test timeout
  timeout: 60000,
  
  // Global setup timeout
  globalTimeout: 300000,
  
  // Reporter configuration
  reporter: [
    ['list'],
    ['json', { outputFile: path.join(tmpTestDir, 'test-results.json') }],
    ['html', { outputFolder: path.join(tmpTestDir, 'playwright-report') }]
  ],
  
  // Global test configuration
  use: {
    // Base URL for tests
    baseURL: process.env.TEST_BASE_URL || 'http://localhost:8000',
    
    // Browser context options
    headless: process.env.CI ? true : false,
    viewport: { width: 1280, height: 720 },
    
    // Test artifacts
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
    
    // Store artifacts in temp directory
    outputDir: path.join(tmpTestDir, 'test-results'),
  },
  
  // Browser projects
  projects: [
    {
      name: 'chromium',
      use: { 
        ...require('@playwright/test').devices['Desktop Chrome'],
        // Use temporary directory for downloads
        downloadsPath: path.join(tmpTestDir, 'downloads'),
      },
    },
    {
      name: 'firefox',
      use: { 
        ...require('@playwright/test').devices['Desktop Firefox'],
        downloadsPath: path.join(tmpTestDir, 'downloads'),
      },
    },
  ],
  
  // Global setup and teardown
  globalSetup: path.join(__dirname, 'global-setup.js'),
  globalTeardown: path.join(__dirname, 'global-teardown.js'),
  
  // Test environment variables
  expect: {
    // Timeout for assertions
    timeout: 10000
  },
  
  // Web server configuration for local testing
  webServer: process.env.CI ? undefined : {
    command: 'cd ../.. && python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000',
    port: 8000,
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
    env: {
      ...process.env,
      // Use temporary directory for test data
      WARP_TEST_DATA_DIR: tmpTestDir,
      WARP_TEST_MODE: 'true'
    }
  }
});

// Export temp directory for use in tests
module.exports.tmpTestDir = tmpTestDir;