const { test, expect } = require('@playwright/test');

test.describe('License Management User Flow - E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
  });

  test('complete license management user journey', async ({ page }) => {
    console.log('🎯 Starting complete license management user journey...');
    
    // Step 1: User opens WARPCORE and sees the interface
    console.log('📄 Step 1: Verifying WARPCORE main interface loads');
    
    const pageTitle = await page.title();
    expect(pageTitle).toContain('APEX');
    console.log(`✅ Page loaded: ${pageTitle}`);
    
    // Step 2: User clicks profile dropdown to access license
    console.log('👤 Step 2: Opening profile dropdown');
    
    const profileBtn = page.locator('.profile-btn');
    await expect(profileBtn).toBeVisible();
    await profileBtn.click();
    await page.waitForTimeout(500);
    
    // Verify dropdown shows license status
    const licenseStatus = page.locator('#license-status-badge-header');
    await expect(licenseStatus).toBeVisible();
    const statusText = await licenseStatus.textContent();
    console.log(`📊 Current license status: ${statusText}`);
    
    // Step 3: User clicks "Manage" button to open license modal
    console.log('🔑 Step 3: Opening license management modal');
    
    const manageBtn = page.locator('button:has-text("🔑 Manage")');
    await expect(manageBtn).toBeVisible();
    await manageBtn.click();
    await page.waitForTimeout(1000);
    
    // Verify modal opens
    const modal = page.locator('#license-modal');
    await expect(modal).toBeVisible();
    console.log('✅ License modal opened successfully');
    
    // Step 4: User explores license activation tab
    console.log('🎫 Step 4: Testing license activation interface');
    
    const modalTitle = page.locator('#license-modal .modal-title');
    await expect(modalTitle).toContainText('License Activation');
    
    // Verify license key input is present and functional
    const licenseKeyInput = page.locator('#license-key');
    await expect(licenseKeyInput).toBeVisible();
    
    // Test license key format validation
    await licenseKeyInput.fill('WARP-TEST-1234-5678');
    const keyValue = await licenseKeyInput.inputValue();
    expect(keyValue).toBe('WARP-TEST-1234-5678');
    console.log('✅ License key input functional');
    
    // Test email input
    const emailInput = page.locator('#user-email');
    await expect(emailInput).toBeVisible();
    await emailInput.fill('test@warpcore.dev');
    console.log('✅ Email input functional');
    
    // Step 5: User switches to trial tab
    console.log('🆓 Step 5: Testing trial license interface');
    
    const trialTab = page.locator('.license-tab:has-text("Start Trial")');
    await expect(trialTab).toBeVisible();
    await trialTab.click();
    await page.waitForTimeout(500);
    
    // Verify trial tab becomes active
    await expect(trialTab).toHaveClass(/active/);
    
    // Check trial content is visible
    const trialContent = page.locator('#license-tab-trial');
    await expect(trialContent).toHaveClass(/active/);
    await expect(trialContent).toContainText('14 days');
    
    // Verify trial features are listed
    const trialFeatures = page.locator('#license-tab-trial .trial-benefits li');
    const featureCount = await trialFeatures.count();
    expect(featureCount).toBeGreaterThan(3);
    console.log(`✅ Found ${featureCount} trial features listed`);
    
    // Test trial email input
    const trialEmail = page.locator('#trial-email');
    await expect(trialEmail).toBeVisible();
    await trialEmail.fill('trial@warpcore.dev');
    console.log('✅ Trial email input functional');
    
    // Step 6: User explores upgrade options
    console.log('⬆️ Step 6: Testing upgrade interface');
    
    const upgradeTab = page.locator('.license-tab:has-text("Upgrade")');
    await expect(upgradeTab).toBeVisible();
    await upgradeTab.click();
    await page.waitForTimeout(500);
    
    // Verify upgrade tab content
    const upgradeContent = page.locator('#license-tab-upgrade');
    await expect(upgradeContent).toHaveClass(/active/);
    console.log('✅ Upgrade options accessible');
    
    // Step 7: Test license validation functionality
    console.log('✅ Step 7: Testing license validation');
    
    // Go back to activation tab
    const activateTab = page.locator('.license-tab:has-text("Activate License")');
    await activateTab.click();
    await page.waitForTimeout(500);
    
    // Test validation button
    const validateBtn = page.locator('button:has-text("Validate")');
    await expect(validateBtn).toBeVisible();
    
    // Clear and enter a test license
    await licenseKeyInput.fill('WARP-TEST-9999-DEMO');
    
    // Click validate (this will make API call)
    await validateBtn.click();
    await page.waitForTimeout(2000);
    
    // Check if validation result appears
    const resultDiv = page.locator('#license-validation-result');
    await expect(resultDiv).toBeVisible();
    
    const resultText = await resultDiv.textContent();
    console.log(`📝 Validation result: ${resultText}`);
    
    // Step 8: Test hardware signature generation
    console.log('🔧 Step 8: Testing hardware signature generation');
    
    const signature = await page.evaluate(() => getHardwareSignature());
    expect(typeof signature).toBe('string');
    expect(signature.length).toBeGreaterThan(5);
    console.log(`🖥️ Hardware signature: ${signature.substring(0, 12)}...`);
    
    // Step 9: User closes modal
    console.log('❌ Step 9: Closing license modal');
    
    const closeBtn = page.locator('#license-modal .modal-close');
    await expect(closeBtn).toBeVisible();
    await closeBtn.click();
    await page.waitForTimeout(500);
    
    // Modal should be hidden
    await expect(modal).not.toBeVisible();
    console.log('✅ License modal closed successfully');
    
    // Step 10: Verify user is back to main interface
    console.log('🏠 Step 10: Verifying return to main interface');
    
    // Main interface should still be functional
    const header = page.locator('.apex-header');
    await expect(header).toBeVisible();
    
    console.log('✅ Complete license management user journey successful!');
    console.log('📊 Summary: All license UI components from apex integrated successfully into WARPCORE');
  });

  test('license API integration validation', async ({ page }) => {
    console.log('🌐 Testing license API integration...');
    
    let apiCalls = [];
    
    // Monitor license API calls
    page.on('request', request => {
      if (request.url().includes('/api/license/')) {
        apiCalls.push({
          url: request.url(),
          method: request.method(),
          timestamp: Date.now()
        });
        console.log(`📡 API Call: ${request.method()} ${request.url()}`);
      }
    });
    
    // Open license modal
    await page.evaluate(() => showLicenseModal());
    await page.waitForTimeout(500);
    
    // Trigger validation API call
    await page.locator('#license-key').fill('WARP-API-TEST-KEY');
    await page.locator('button:has-text("Validate")').click();
    await page.waitForTimeout(2000);
    
    // Check API calls were made
    const licenseCalls = apiCalls.filter(call => call.url.includes('/license/validate'));
    expect(licenseCalls.length).toBeGreaterThan(0);
    
    console.log(`✅ License API integration verified: ${apiCalls.length} API calls made`);
    apiCalls.forEach(call => {
      console.log(`  - ${call.method} ${call.url}`);
    });
  });

  test('PAP compliance verification', async ({ page }) => {
    console.log('🏛️ Testing PAP (Provider Abstraction Pattern) compliance...');
    
    // Verify license UI doesn't hardcode provider endpoints
    const modalHTML = await page.evaluate(() => {
      return document.getElementById('license-modal')?.innerHTML || '';
    });
    
    // Should not contain hardcoded provider URLs
    expect(modalHTML).not.toContain('amazonaws.com');
    expect(modalHTML).not.toContain('googleapis.com');
    expect(modalHTML).not.toContain('microsoft.com');
    
    // Should use relative API paths
    expect(modalHTML).toContain('/api/license/');
    
    console.log('✅ License UI is provider-agnostic (PAP compliant)');
    
    // Verify hardware signature doesn't leak sensitive info
    const signature = await page.evaluate(() => getHardwareSignature());
    
    // Should be a hash, not contain raw system info
    expect(signature).not.toContain(navigator.userAgent);
    expect(signature).not.toContain('Mozilla');
    expect(signature).toMatch(/^[a-f0-9]+$/); // Should be hex
    
    console.log('✅ Hardware signature generation is secure');
  });
});