const { chromium } = require('playwright');

(async () => {
  // Start WARPCORE server in background
  console.log('🚀 Starting WARPCORE server...');
  
  const { spawn } = require('child_process');
  const server = spawn('python3', ['-c', `
import sys
sys.path.append('/Users/shawn_meredith/code/pets/warpcore/src')
from main import app
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=8000, log_level='info')
  `], {
    detached: true,
    stdio: ['ignore', 'pipe', 'pipe']
  });

  // Wait for server to start
  await new Promise(resolve => setTimeout(resolve, 3000));

  try {
    // Launch browser
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();

    // Capture console logs and errors
    page.on('console', msg => {
      const type = msg.type();
      const text = msg.text();
      console.log(`🖥️  [${type.toUpperCase()}] ${text}`);
    });

    page.on('pageerror', error => {
      console.error('❌ PAGE ERROR:', error.message);
    });

    // Navigate to WARPCORE
    console.log('📍 Navigating to WARPCORE...');
    await page.goto('http://localhost:8000');
    await page.waitForLoadState('networkidle');

    console.log('✅ Page loaded successfully');

    // Check for license modal button
    const licenseButton = await page.locator('button:has-text("License")').first();
    const exists = await licenseButton.count() > 0;
    
    if (exists) {
      console.log('🔑 License button found!');
      
      // Try to click license button
      await licenseButton.click();
      await page.waitForTimeout(1000);
      
      // Check if modal opened
      const modal = await page.locator('#license-modal').first();
      const modalVisible = await modal.isVisible().catch(() => false);
      
      if (modalVisible) {
        console.log('✅ License modal opened successfully!');
      } else {
        console.log('❌ License modal did not open');
      }
    } else {
      console.log('❌ License button not found');
    }

    // Wait a moment to see any delayed JavaScript errors
    await page.waitForTimeout(3000);
    
    await browser.close();
    console.log('🏁 Test completed');
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  } finally {
    // Kill server
    server.kill();
    process.exit();
  }
})();