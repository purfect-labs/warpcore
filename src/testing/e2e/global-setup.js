/**
 * WARP E2E Tests Global Setup
 * Runs before all tests to setup test environment
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

async function globalSetup() {
  console.log('🚀 WARP E2E Tests: Global setup starting...');
  
  // Create temporary test directory
  const tmpTestDir = path.join(os.tmpdir(), `warp-e2e-tests-${Date.now()}`);
  
  try {
    // Create test directories
    fs.mkdirSync(tmpTestDir, { recursive: true });
    fs.mkdirSync(path.join(tmpTestDir, 'downloads'), { recursive: true });
    fs.mkdirSync(path.join(tmpTestDir, 'test-results'), { recursive: true });
    
    console.log(`✅ WARP E2E Tests: Test directory created: ${tmpTestDir}`);
    
    // Setup test environment variables
    process.env.WARP_TEST_DATA_DIR = tmpTestDir;
    process.env.WARP_TEST_MODE = 'true';
    
    // Log test environment
    console.log('📊 WARP E2E Tests: Environment configured');
    console.log(`   - Test data dir: ${tmpTestDir}`);
    console.log(`   - Test mode: ${process.env.WARP_TEST_MODE}`);
    
    // Create test license keys for demo
    const testLicenseKeys = {
      'WARP-TEST-DEMO-KEY1': { valid: true, tier: 'professional' },
      'TEST-LICENSE-DEMO-KEY': { valid: true, tier: 'basic' },
      'INVALID-KEY': { valid: false, tier: null }
    };
    
    // Write test data
    fs.writeFileSync(
      path.join(tmpTestDir, 'test-license-keys.json'),
      JSON.stringify(testLicenseKeys, null, 2)
    );
    
    console.log('🔑 WARP E2E Tests: Test license keys configured');
    
    // Additional test setup can be added here
    // For example: database setup, API mocking, etc.
    
    console.log('✅ WARP E2E Tests: Global setup completed successfully');
    
  } catch (error) {
    console.error('❌ WARP E2E Tests: Global setup failed:', error);
    throw error;
  }
}

module.exports = globalSetup;