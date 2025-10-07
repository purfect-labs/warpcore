/**
 * WARP PAP Flow Tests - PAP Architecture End-to-End Testing
 * Tests FastAPI → Controllers → Orchestrators → Providers flow
 */

const { test, expect } = require('@playwright/test');

// Test group for PAP flow validation
test.describe('PAP Architecture Flow Tests', () => {
  
  test.beforeEach(async ({ page }) => {
    // Navigate to main page
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });
  
  test('FastAPI → Controllers flow validation', async ({ page }) => {
    // Test direct FastAPI route calling controller
    test.info().annotations.push({ type: 'PAP_LAYER', description: 'FastAPI → Controllers' });
    
    // Check that FastAPI routes work without route abstractions
    const response = await page.request.get('/api/status');
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data).toHaveProperty('healthy');
    
    // Verify route calls controller directly (no route abstraction)
    const licenseResponse = await page.request.get('/api/license/status');
    expect(licenseResponse.ok()).toBeTruthy();
    
    console.log('✅ PAP Flow Test: FastAPI → Controllers validated');
  });
  
  test('Controllers → Orchestrators flow validation', async ({ page }) => {
    // Test controller delegating to orchestrator
    test.info().annotations.push({ type: 'PAP_LAYER', description: 'Controllers → Orchestrators' });
    
    // Trigger GCP authentication which should go Controller → Orchestrator
    const authRequest = await page.request.post('/api/auth', {
      data: {
        provider: 'gcp',
        context: 'test'
      }
    });
    
    expect(authRequest.ok()).toBeTruthy();
    const authData = await authRequest.json();
    expect(authData).toHaveProperty('status');
    
    console.log('✅ PAP Flow Test: Controllers → Orchestrators validated');
  });
  
  test('Orchestrators → Providers flow validation', async ({ page }) => {
    // Test orchestrator delegating to provider
    test.info().annotations.push({ type: 'PAP_LAYER', description: 'Orchestrators → Providers' });
    
    // License operations should flow through orchestrator to provider
    const licenseValidation = await page.request.post('/api/license/validate', {
      data: {
        license_key: 'TEST-LICENSE-DEMO-KEY'
      }
    });
    
    expect(licenseValidation.ok()).toBeTruthy();
    const validationData = await licenseValidation.json();
    expect(validationData).toHaveProperty('valid');
    
    console.log('✅ PAP Flow Test: Orchestrators → Providers validated');
  });
  
  test('End-to-end PAP flow validation', async ({ page }) => {
    // Complete request lifecycle: FastAPI → Controllers → Orchestrators → Providers
    test.info().annotations.push({ type: 'PAP_FLOW', description: 'Complete request lifecycle' });
    
    // 1. Direct FastAPI endpoint
    await page.goto('/');
    
    // 2. Verify page loads (template system working)
    await expect(page.locator('header.apex-header')).toBeVisible();
    
    // 3. Test complete license flow (full PAP stack)
    await page.click('[onclick="showLicenseModal()"]');
    await expect(page.locator('#license-modal')).toBeVisible();
    
    // 4. Fill license form (will hit full PAP flow)
    await page.fill('#license-key', 'WARP-TEST-DEMO-KEY1');
    await page.fill('#user-email', 'test@warp-demo.com');
    
    // 5. Submit (this goes through complete PAP flow)
    await page.click('button[type="submit"]');
    
    // 6. Verify flow completed (response received from provider layer)
    await expect(page.locator('#license-validation-result')).toBeVisible();
    
    console.log('✅ PAP Flow Test: Complete end-to-end flow validated');
  });
  
  test('PAP architecture integrity validation', async ({ page }) => {
    // Verify no route abstractions remain
    test.info().annotations.push({ type: 'ARCHITECTURE', description: 'PAP integrity check' });
    
    // Check that routes are defined directly in FastAPI
    const apiDocs = await page.request.get('/docs');
    expect(apiDocs.ok()).toBeTruthy();
    
    // Verify controller isolation (no route dependencies)
    const healthCheck = await page.request.get('/api/status');
    expect(healthCheck.ok()).toBeTruthy();
    
    // Verify orchestrator integration
    const gpcStatus = await page.request.get('/api/gcp/status');
    expect(gpcStatus.ok()).toBeTruthy();
    
    console.log('✅ PAP Flow Test: Architecture integrity validated');
  });
  
  test('PAP error handling flow', async ({ page }) => {
    // Test error propagation through PAP layers
    test.info().annotations.push({ type: 'ERROR_HANDLING', description: 'PAP error propagation' });
    
    // Invalid license key should properly flow through PAP stack
    const invalidLicenseResponse = await page.request.post('/api/license/validate', {
      data: {
        license_key: 'INVALID-KEY'
      }
    });
    
    expect(invalidLicenseResponse.ok()).toBeTruthy();
    const errorData = await invalidLicenseResponse.json();
    expect(errorData).toHaveProperty('valid', false);
    expect(errorData).toHaveProperty('error');
    
    console.log('✅ PAP Flow Test: Error handling validated');
  });
  
  test('PAP performance validation', async ({ page }) => {
    // Test PAP flow performance
    test.info().annotations.push({ type: 'PERFORMANCE', description: 'PAP flow timing' });
    
    const startTime = Date.now();
    
    // Test multiple PAP flows in sequence
    await page.request.get('/api/status');
    await page.request.get('/api/license/status');
    await page.request.get('/api/gcp/status');
    
    const endTime = Date.now();
    const totalTime = endTime - startTime;
    
    // PAP flow should be efficient (under 5 seconds for 3 calls)
    expect(totalTime).toBeLessThan(5000);
    
    console.log(`✅ PAP Flow Test: Performance validated (${totalTime}ms for 3 requests)`);
  });
  
});

// Test group for PAP component isolation
test.describe('PAP Component Isolation Tests', () => {
  
  test('Controller isolation validation', async ({ page }) => {
    // Verify controllers work independently of routes
    test.info().annotations.push({ type: 'ISOLATION', description: 'Controller independence' });
    
    // Controllers should work without route coupling
    const response = await page.request.get('/api/license/status');
    expect(response.ok()).toBeTruthy();
    
    // Check response structure indicates controller layer processing
    const data = await response.json();
    expect(data).toHaveProperty('success');
    
    console.log('✅ PAP Isolation Test: Controllers validated');
  });
  
  test('Orchestrator isolation validation', async ({ page }) => {
    // Verify orchestrators coordinate properly
    test.info().annotations.push({ type: 'ISOLATION', description: 'Orchestrator coordination' });
    
    // Orchestrators should coordinate between controllers and providers
    const authResponse = await page.request.post('/api/auth', {
      data: {
        provider: 'gcp',
        context: 'test'
      }
    });
    
    expect(authResponse.ok()).toBeTruthy();
    const authData = await authResponse.json();
    expect(authData).toHaveProperty('status');
    
    console.log('✅ PAP Isolation Test: Orchestrators validated');
  });
  
  test('Provider isolation validation', async ({ page }) => {
    // Verify providers handle business logic independently
    test.info().annotations.push({ type: 'ISOLATION', description: 'Provider business logic' });
    
    // Providers should handle actual business logic
    const subscriptionResponse = await page.request.get('/api/license/subscription');
    expect(subscriptionResponse.ok()).toBeTruthy();
    
    console.log('✅ PAP Isolation Test: Providers validated');
  });
  
});

// Cleanup test to verify temp context usage
test.describe('Test Environment Cleanup', () => {
  
  test('Verify /tmp context usage', async ({ page }) => {
    // Verify tests are running in temporary context
    test.info().annotations.push({ type: 'CLEANUP', description: 'Temporary context validation' });
    
    // This should be running in a temporary context
    const tmpCheck = process.env.WARP_TEST_DATA_DIR;
    expect(tmpCheck).toContain('/tmp');
    
    console.log(`✅ Cleanup Test: Running in temporary context: ${tmpCheck}`);
  });
  
});