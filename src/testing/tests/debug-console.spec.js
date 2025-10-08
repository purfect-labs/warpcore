const { test, expect } = require('@playwright/test');

test.describe('Debug Console Errors', () => {
  test('should check for JavaScript errors and console messages', async ({ page }) => {
    const consoleMessages = [];
    const errors = [];
    
    // Capture console messages
    page.on('console', msg => {
      consoleMessages.push({
        type: msg.type(),
        text: msg.text(),
        location: msg.location()
      });
      console.log(`CONSOLE ${msg.type().toUpperCase()}: ${msg.text()}`);
    });
    
    // Capture JavaScript errors
    page.on('pageerror', error => {
      errors.push(error.message);
      console.log(`PAGE ERROR: ${error.message}`);
    });
    
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
    
    // Try to click profile dropdown
    console.log('🔍 Testing profile dropdown click...');
    const profileBtn = page.locator('.profile-btn');
    if (await profileBtn.count() > 0) {
      await profileBtn.click();
      await page.waitForTimeout(1000);
      console.log('✅ Profile dropdown clicked');
    } else {
      console.log('❌ Profile dropdown not found');
    }
    
    // Try to access showLicenseModal function
    console.log('🔍 Testing showLicenseModal function...');
    const functionResult = await page.evaluate(() => {
      try {
        if (typeof showLicenseModal === 'function') {
          showLicenseModal();
          return 'SUCCESS: Function called';
        } else {
          return 'ERROR: Function not defined';
        }
      } catch (error) {
        return `ERROR: ${error.message}`;
      }
    });
    console.log(`Function test result: ${functionResult}`);
    
    // Check what JS files loaded
    const loadedScripts = await page.evaluate(() => {
      const scripts = Array.from(document.querySelectorAll('script[src]'));
      return scripts.map(script => script.src);
    });
    
    console.log('📜 Loaded JavaScript files:');
    loadedScripts.forEach(script => console.log(`  - ${script}`));
    
    // Check for license activation object
    const licenseActivationStatus = await page.evaluate(() => {
      return {
        LicenseActivation: typeof LicenseActivation,
        showLicenseModal: typeof showLicenseModal,
        closeLicenseModal: typeof closeLicenseModal,
        validateLicenseKey: typeof validateLicenseKey,
        getHardwareSignature: typeof getHardwareSignature
      };
    });
    
    console.log('🔧 JavaScript function availability:');
    Object.entries(licenseActivationStatus).forEach(([key, value]) => {
      console.log(`  - ${key}: ${value}`);
    });
    
    // Summary
    console.log(`\n📊 SUMMARY:`);
    console.log(`Console Messages: ${consoleMessages.length}`);
    console.log(`JavaScript Errors: ${errors.length}`);
    console.log(`Scripts Loaded: ${loadedScripts.length}`);
    
    if (errors.length > 0) {
      console.log('\n❌ JavaScript Errors Found:');
      errors.forEach(error => console.log(`  - ${error}`));
    }
    
    // Check if modal element exists in DOM
    const modalExists = await page.locator('#license-modal').count() > 0;
    console.log(`License Modal in DOM: ${modalExists ? '✅' : '❌'}`);
    
    if (modalExists) {
      const modalStyle = await page.locator('#license-modal').getAttribute('style');
      console.log(`Modal initial style: ${modalStyle}`);
    }
  });
});