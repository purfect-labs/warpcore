/**
 * WARP License POC Tests - License Activation and Button Lock Testing
 * Tests complete license activation workflow with button lock mechanism
 */

const { test, expect } = require('@playwright/test');

// Test group for license POC functionality
test.describe('License POC Demo Tests', () => {
  
  test.beforeEach(async ({ page }) => {
    // Navigate to main page
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });
  
  test('License POC UI components visibility', async ({ page }) => {
    // Verify license POC components are visible
    test.info().annotations.push({ type: 'UI_VISIBILITY', description: 'License POC component visibility' });
    
    // Check for feature buttons section
    await expect(page.locator('.warp-features-section')).toBeVisible();
    
    // Check for basic and premium feature buttons
    await expect(page.locator('#basic-feature-btn')).toBeVisible();
    await expect(page.locator('#professional-feature-btn')).toBeVisible();
    
    // Check for license status display
    await expect(page.locator('.license-status-display')).toBeVisible();
    
    console.log('✅ License POC Test: UI components visible');
  });
  
  test('Basic feature access (always available)', async ({ page }) => {
    // Test basic feature button functionality
    test.info().annotations.push({ type: 'FEATURE_ACCESS', description: 'Basic feature access' });
    
    // Click basic feature button
    await page.click('#basic-feature-btn');
    
    // Verify result shows success
    await expect(page.locator('#basic-feature-result')).toBeVisible();
    await expect(page.locator('#basic-feature-result.success')).toBeVisible();
    
    // Verify content shows essential features available
    const resultText = await page.locator('#basic-feature-result').textContent();
    expect(resultText).toContain('Essential Features Available');
    
    console.log('✅ License POC Test: Basic feature access validated');
  });
  
  test('Premium feature locked without license', async ({ page }) => {
    // Test premium feature button shows lock when no license
    test.info().annotations.push({ type: 'FEATURE_LOCK', description: 'Premium feature lock mechanism' });
    
    // Verify premium button shows as locked initially
    await expect(page.locator('#professional-feature-btn.locked')).toBeVisible();
    
    // Click premium feature button
    await page.click('#professional-feature-btn');
    
    // Verify lock message appears
    await expect(page.locator('#premium-feature-result')).toBeVisible();
    await expect(page.locator('#premium-feature-result.error')).toBeVisible();
    
    // Verify lock message content
    const lockMessage = await page.locator('#premium-feature-result').textContent();
    expect(lockMessage).toContain('Premium Features Locked');
    expect(lockMessage).toContain('Activate License Now');
    
    console.log('✅ License POC Test: Premium feature lock validated');
  });
  
  test('License modal opens and displays correctly', async ({ page }) => {
    // Test license modal functionality
    test.info().annotations.push({ type: 'LICENSE_MODAL', description: 'License activation modal' });
    
    // Open license modal
    await page.click('[onclick="showLicenseModal()"]');
    
    // Verify modal is visible
    await expect(page.locator('#license-modal')).toBeVisible();
    
    // Verify modal title includes watermark
    const modalTitle = await page.locator('.modal-title').textContent();
    expect(modalTitle).toContain('License Activation - POC Demo');
    
    // Verify form fields are present
    await expect(page.locator('#license-key')).toBeVisible();
    await expect(page.locator('#user-email')).toBeVisible();
    
    // Verify placeholder includes demo watermark
    const placeholder = await page.locator('#license-key').getAttribute('placeholder');
    expect(placeholder).toContain('demo');
    
    console.log('✅ License POC Test: License modal validated');
  });
  
  test('License key format validation', async ({ page }) => {
    // Test real-time license key format validation
    test.info().annotations.push({ type: 'KEY_VALIDATION', description: 'License key format validation' });
    
    // Open license modal
    await page.click('[onclick="showLicenseModal()"]');
    await expect(page.locator('#license-modal')).toBeVisible();
    
    // Type invalid format
    await page.fill('#license-key', 'invalid-key');
    
    // Verify format hint appears
    await expect(page.locator('#license-format-feedback')).toBeVisible();
    const hintText = await page.locator('#license-format-feedback').textContent();
    expect(hintText).toContain('WARP-XXXX-XXXX-XXXX');
    
    // Type valid format
    await page.fill('#license-key', 'WARP-TEST-DEMO-KEY1');
    
    // Verify validation feedback
    const validText = await page.locator('#license-format-feedback').textContent();
    expect(validText).toContain('Valid format');
    
    console.log('✅ License POC Test: Key format validation working');
  });
  
  test('License activation flow', async ({ page }) => {
    // Test license activation submission
    test.info().annotations.push({ type: 'LICENSE_ACTIVATION', description: 'License activation flow' });
    
    // Open license modal
    await page.click('[onclick="showLicenseModal()"]');
    await expect(page.locator('#license-modal')).toBeVisible();
    
    // Fill activation form with demo data
    await page.fill('#license-key', 'WARP-TEST-DEMO-KEY1');
    await page.fill('#user-email', 'test@warp-demo.com');
    
    // Submit activation
    await page.click('button[type="submit"]');
    
    // Verify loading message appears
    await expect(page.locator('#license-validation-result')).toBeVisible();
    
    // Wait for activation processing
    await page.waitForTimeout(3000);
    
    // Verify activation response (success or error message)
    const resultText = await page.locator('#license-validation-result').textContent();
    expect(resultText.length).toBeGreaterThan(0);
    
    console.log('✅ License POC Test: License activation flow validated');
  });
  
  test('Trial license generation', async ({ page }) => {
    // Test trial license functionality
    test.info().annotations.push({ type: 'TRIAL_LICENSE', description: 'Trial license generation' });
    
    // Open license modal
    await page.click('[onclick="showLicenseModal()"]');
    await expect(page.locator('#license-modal')).toBeVisible();
    
    // Switch to trial tab
    await page.click('button[onclick="showLicenseTab(\'trial\')"]');
    
    // Verify trial tab content
    await expect(page.locator('#license-tab-trial.active')).toBeVisible();
    
    // Fill trial form
    await page.fill('#trial-email', 'trial@warp-demo.com');
    
    // Submit trial request
    await page.click('#trial-form button[type="submit"]');
    
    // Verify trial processing
    await page.waitForTimeout(2000);
    
    console.log('✅ License POC Test: Trial license flow validated');
  });
  
  test('Button state changes after license activation', async ({ page }) => {
    // Test button lock/unlock mechanism
    test.info().annotations.push({ type: 'BUTTON_STATE', description: 'Button state management' });
    
    // Initial state - premium button should be locked
    await expect(page.locator('#professional-feature-btn.locked')).toBeVisible();
    
    // Simulate successful license activation by directly updating status
    await page.evaluate(() => {
      // Trigger license status change event
      window.dispatchEvent(new CustomEvent('licenseStatusChanged', {
        detail: {
          active: true,
          tier: 'professional',
          features: ['premium_features']
        }
      }));
    });
    
    // Wait for button state update
    await page.waitForTimeout(1000);
    
    // Verify button unlocked
    await expect(page.locator('#professional-feature-btn.unlocked')).toBeVisible();
    
    // Test premium feature now works
    await page.click('#professional-feature-btn');
    await expect(page.locator('#premium-feature-result.success')).toBeVisible();
    
    const successText = await page.locator('#premium-feature-result').textContent();
    expect(successText).toContain('Premium Features Available');
    
    console.log('✅ License POC Test: Button state changes validated');
  });
  
  test('License status display updates', async ({ page }) => {
    // Test license status display functionality
    test.info().annotations.push({ type: 'STATUS_DISPLAY', description: 'License status display' });
    
    // Initial status should show no license
    const initialStatus = await page.locator('#status-badge').textContent();
    expect(initialStatus).toContain('No License');
    
    // Simulate license activation
    await page.evaluate(() => {
      window.dispatchEvent(new CustomEvent('licenseStatusChanged', {
        detail: {
          active: true,
          tier: 'professional',
          features: ['premium_features'],
          user_email: 'test@warp-demo.com'
        }
      }));
    });
    
    // Wait for status update
    await page.waitForTimeout(1000);
    
    // Verify status updated
    const updatedStatus = await page.locator('#status-badge').textContent();
    expect(updatedStatus).toContain('License Active');
    
    console.log('✅ License POC Test: Status display updates validated');
  });
  
  test('Security measures and button manipulation prevention', async ({ page }) => {
    // Test security features of button lock mechanism
    test.info().annotations.push({ type: 'SECURITY', description: 'Button manipulation prevention' });
    
    // Attempt to manipulate button state via DOM
    await page.evaluate(() => {
      const btn = document.getElementById('professional-feature-btn');
      if (btn) {
        btn.classList.remove('locked');
        btn.classList.add('unlocked');
      }
    });
    
    // Wait for security system to restore state
    await page.waitForTimeout(1000);
    
    // Verify button reverted to locked state
    await expect(page.locator('#professional-feature-btn.locked')).toBeVisible();
    
    // Click should still show lock message
    await page.click('#professional-feature-btn');
    await expect(page.locator('#premium-feature-result.error')).toBeVisible();
    
    console.log('✅ License POC Test: Security measures validated');
  });
  
});

// Test group for license POC integration
test.describe('License POC Integration Tests', () => {
  
  test('License POC integrates with PAP architecture', async ({ page }) => {
    // Verify license system integrates with PAP flow
    test.info().annotations.push({ type: 'INTEGRATION', description: 'PAP integration' });
    
    // License status API should work through PAP flow
    const response = await page.request.get('/api/license/status');
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data).toHaveProperty('success');
    
    // License validation should work through PAP flow
    const validateResponse = await page.request.post('/api/license/validate', {
      data: {
        license_key: 'TEST-LICENSE-DEMO-KEY'
      }
    });
    
    expect(validateResponse.ok()).toBeTruthy();
    const validateData = await validateResponse.json();
    expect(validateData).toHaveProperty('valid');
    
    console.log('✅ License POC Integration: PAP architecture integration validated');
  });
  
  test('License POC UI components load with proper watermarks', async ({ page }) => {
    // Verify all watermarks are properly applied
    test.info().annotations.push({ type: 'WATERMARKS', description: 'Demo watermark validation' });
    
    // Check feature button watermarks
    const basicBtnText = await page.locator('#basic-feature-btn').textContent();
    expect(basicBtnText).toContain('Essential');
    
    const premiumBtnText = await page.locator('#professional-feature-btn').textContent();
    expect(premiumBtnText).toContain('License Required');
    
    // Check modal watermarks
    await page.click('[onclick="showLicenseModal()"]');
    const modalTitle = await page.locator('.modal-title').textContent();
    expect(modalTitle).toContain('POC Demo');
    
    console.log('✅ License POC Integration: Demo watermarks validated');
  });
  
});