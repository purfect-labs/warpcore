/**
 * WARP E2E Tests Global Teardown
 * Runs after all tests to cleanup test environment
 */

const fs = require('fs');
const path = require('path');

async function globalTeardown() {
  console.log('🧹 WARP E2E Tests: Global teardown starting...');
  
  try {
    // Get test directory from environment
    const tmpTestDir = process.env.WARP_TEST_DATA_DIR;
    
    if (tmpTestDir && tmpTestDir.includes('/tmp') && fs.existsSync(tmpTestDir)) {
      // Safety check - only delete if in /tmp directory
      console.log(`🗑️  WARP E2E Tests: Cleaning up test directory: ${tmpTestDir}`);
      
      // Recursively remove test directory and all contents
      fs.rmSync(tmpTestDir, { recursive: true, force: true });
      
      console.log('✅ WARP E2E Tests: Test directory cleaned up successfully');
    } else {
      console.log('⚠️  WARP E2E Tests: No test directory to clean up or not in /tmp');
    }
    
    // Clean up environment variables
    delete process.env.WARP_TEST_DATA_DIR;
    delete process.env.WARP_TEST_MODE;
    
    console.log('🧹 WARP E2E Tests: Environment variables cleaned');
    
    // Log final cleanup status
    console.log('✅ WARP E2E Tests: Global teardown completed successfully');
    
  } catch (error) {
    console.error('❌ WARP E2E Tests: Global teardown failed:', error);
    // Don't throw error in teardown to avoid masking test failures
  }
}

module.exports = globalTeardown;