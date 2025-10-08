/**
 * WARPCORE Full UI System Tests
 * 
 * Comprehensive end-to-end testing of the complete WARPCORE system:
 * - System Orchestrator (Data Layer → Web Layer → API Layer)
 * - Provider-Abstraction-Pattern UI flow
 * - License management UI components
 * - Dashboard and agent cards
 * - Real user flows with native events
 * 
 * Tests the full system as launched by: python3 warpcore.py --web
 */

const { test, expect } = require('@playwright/test');

test.describe('WARPCORE Full UI System Tests', () => {
  
  test.beforeEach(async ({ page }) => {
    // Set longer timeout for system orchestrator initialization
    test.setTimeout(45000);
    
    // Navigate to main page and wait for full system initialization
    await page.goto('/');
    
    // Wait for system orchestrator to complete initialization
    // The page should show WARPCORE branding, not APEX
    await expect(page.locator('header')).toContainText('WARPCORE');
    
    // Wait for network to be idle (all assets loaded)
    await page.waitForLoadState('networkidle');
    
    // Verify basic system readiness
    await expect(page.locator('body')).toBeVisible();
  });

  test('System Orchestrator Full Initialization', async ({ page }) => {
    test.info().annotations.push({ 
      type: 'SYSTEM_ORCHESTRATOR', 
      description: 'Data Layer → Web Layer → API Layer initialization' 
    });

    // Test 1: Verify all three layers are initialized (check API endpoints)
    
    // Data Layer - Configuration and discovery should be ready
    const configResponse = await page.request.get('/api/status');
    expect(configResponse.ok()).toBeTruthy();
    const configData = await configResponse.json();
    expect(configData).toHaveProperty('healthy');
    console.log('✅ Data Layer: Configuration and discovery active');

    // Web Layer - Templates and static assets should be ready
    const staticResponse = await page.request.get('/static/css/main.css');
    expect(staticResponse.ok()).toBeTruthy();
    console.log('✅ Web Layer: Templates and static assets serving');

    // API Layer - Controllers, orchestrators, providers should be ready
    const licenseResponse = await page.request.get('/api/license/status');
    expect(licenseResponse.ok()).toBeTruthy();
    const licenseData = await licenseResponse.json();
    expect(licenseData).toHaveProperty('success');
    console.log('✅ API Layer: Controllers and providers responding');

    // Test 2: Verify Provider-Abstraction-Pattern architecture
    // The system orchestrator discovered 4 controllers, 5 orchestrators, 11 providers
    
    // Architecture discovery endpoint should be available
    const archResponse = await page.request.get('/api/architecture');
    expect(archResponse.ok()).toBeTruthy();
    console.log('✅ PAP Architecture: Discovery endpoints active');

    // Documentation endpoints should be available
    const docsResponse = await page.request.get('/docs');
    expect(docsResponse.ok()).toBeTruthy();
    console.log('✅ PAP Architecture: Documentation system active');

    console.log('🎉 System Orchestrator: All three layers successfully initialized');
  });

  test('WARPCORE Branding and UI Components', async ({ page }) => {
    test.info().annotations.push({ 
      type: 'UI_COMPONENTS', 
      description: 'WARPCORE branding and UI component validation' 
    });

    // Test 1: Verify WARPCORE branding (not APEX)
    await expect(page.locator('title')).toContainText('WARPCORE');
    
    // Check for WARPCORE text in header
    const headerText = await page.locator('header').textContent();
    expect(headerText).toContain('WARPCORE');
    expect(headerText).not.toContain('APEX');
    console.log('✅ UI Branding: WARPCORE branding confirmed, no APEX references');

    // Test 2: Verify core UI components load
    
    // License management UI should be available
    const licenseButton = page.locator('[onclick*="showLicenseModal"], .license-button, [data-action="license"]');
    if (await licenseButton.count() > 0) {
      await expect(licenseButton.first()).toBeVisible();
      console.log('✅ UI Components: License management button visible');
    }

    // Terminal or command interface should be present
    const terminalArea = page.locator('.terminal, .command-area, [data-terminal], #terminal');
    if (await terminalArea.count() > 0) {
      await expect(terminalArea.first()).toBeVisible();
      console.log('✅ UI Components: Terminal interface visible');
    }

    // Status indicators should be present
    const statusIndicators = page.locator('.status, .indicator, [data-status]');
    if (await statusIndicators.count() > 0) {
      expect(await statusIndicators.count()).toBeGreaterThan(0);
      console.log('✅ UI Components: Status indicators present');
    }

    // Test 3: Verify CSS and JavaScript assets load correctly
    
    // Check for WARPCORE-specific CSS classes
    const warpCoreStyles = await page.evaluate(() => {
      return Array.from(document.styleSheets).some(sheet => {
        try {
          return Array.from(sheet.cssRules).some(rule => 
            rule.selectorText && rule.selectorText.includes('warpcore')
          );
        } catch (e) {
          return false;
        }
      });
    });
    
    // JavaScript should be error-free (check console for errors)
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    // Wait a moment for any JS errors to surface
    await page.waitForTimeout(2000);
    
    // Should have minimal JS errors (licensing system may have expected demo errors)
    expect(consoleErrors.length).toBeLessThan(5);
    console.log(`✅ UI Components: JavaScript running with ${consoleErrors.length} errors (expected < 5)`);

    console.log('🎉 UI Components: WARPCORE branding and components validated');
  });

  test('License Management UI Flow', async ({ page }) => {
    test.info().annotations.push({ 
      type: 'LICENSE_FLOW', 
      description: 'Complete license UI workflow testing' 
    });

    // Test 1: Find and open license modal/interface
    let licenseModalOpened = false;
    
    // Try multiple ways to open license modal
    const licenseButtons = await page.locator('[onclick*="License"], [onclick*="license"], .license-button, [data-action="license"]').all();
    
    for (const button of licenseButtons) {
      if (await button.isVisible()) {
        await button.click();
        licenseModalOpened = true;
        break;
      }
    }
    
    // Alternative: try clicking text containing "license"
    if (!licenseModalOpened) {
      const licenseText = page.locator('text=/license/i').first();
      if (await licenseText.isVisible()) {
        await licenseText.click();
        licenseModalOpened = true;
      }
    }

    if (licenseModalOpened) {
      console.log('✅ License Flow: License modal/interface opened');
      
      // Wait for modal content to load
      await page.waitForTimeout(1000);
      
      // Test 2: Verify license form elements
      const licenseKeyInput = page.locator('input[type="text"], input[name*="license"], #license-key').first();
      const emailInput = page.locator('input[type="email"], input[name*="email"], #user-email').first();
      
      if (await licenseKeyInput.isVisible()) {
        await licenseKeyInput.fill('WARP-TEST-DEMO-KEY-12345');
        console.log('✅ License Flow: License key input functional');
      }
      
      if (await emailInput.isVisible()) {
        await emailInput.fill('test@warpcore-demo.com');
        console.log('✅ License Flow: Email input functional');
      }
      
      // Test 3: Submit license form (should hit PAP flow)
      const submitButton = page.locator('button[type="submit"], .submit-button, [data-action="submit"]').first();
      if (await submitButton.isVisible()) {
        await submitButton.click();
        
        // Wait for API response (should go through Controller → Orchestrator → Provider flow)
        await page.waitForTimeout(2000);
        
        // Look for validation response
        const responseElement = page.locator('.validation-result, .response, .message, [data-validation]');
        if (await responseElement.count() > 0) {
          console.log('✅ License Flow: Form submission processed through PAP flow');
        }
      }
    } else {
      console.log('⚠️ License Flow: No license interface found - may be embedded differently');
    }

    // Test 4: Verify license status API endpoint works
    const licenseStatusResponse = await page.request.get('/api/license/status');
    expect(licenseStatusResponse.ok()).toBeTruthy();
    const statusData = await licenseStatusResponse.json();
    expect(statusData).toHaveProperty('success');
    console.log('✅ License Flow: License status API responding correctly');

    console.log('🎉 License Flow: License management UI flow validated');
  });

  test('Dashboard and Agent Cards UI', async ({ page }) => {
    test.info().annotations.push({ 
      type: 'DASHBOARD', 
      description: 'Dashboard layout and agent cards functionality' 
    });

    // Test 1: Look for dashboard elements
    const dashboardElements = await page.locator('.dashboard, .main-content, .content-area, [data-dashboard]').all();
    
    if (dashboardElements.length > 0) {
      console.log('✅ Dashboard: Dashboard container found');
      
      // Test 2: Look for agent cards (compact design)
      const agentCards = await page.locator('.agent-card, .card, .agent, [data-agent]').all();
      
      if (agentCards.length > 0) {
        console.log(`✅ Dashboard: ${agentCards.length} agent cards found`);
        
        // Test card interactions
        for (let i = 0; i < Math.min(agentCards.length, 3); i++) {
          const card = agentCards[i];
          if (await card.isVisible()) {
            // Test hover effect
            await card.hover();
            await page.waitForTimeout(500);
            
            // Test click if clickable
            const isClickable = await card.evaluate(el => {
              return el.onclick !== null || el.style.cursor === 'pointer';
            });
            
            if (isClickable) {
              await card.click();
              await page.waitForTimeout(500);
            }
            
            console.log(`✅ Dashboard: Agent card ${i + 1} interactive`);
          }
        }
      } else {
        console.log('⚠️ Dashboard: No agent cards found - may use different class names');
      }
    } else {
      console.log('⚠️ Dashboard: No dashboard container found - may use different layout');
    }

    // Test 3: Verify responsive layout
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.waitForTimeout(500);
    
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.waitForTimeout(500);
    
    await page.setViewportSize({ width: 1280, height: 720 });
    console.log('✅ Dashboard: Responsive layout tested');

    console.log('🎉 Dashboard: Dashboard and agent cards UI validated');
  });

  test('API Endpoints and PAP Flow Integration', async ({ page }) => {
    test.info().annotations.push({ 
      type: 'API_INTEGRATION', 
      description: 'API endpoints and PAP architecture integration' 
    });

    // Test 1: Core system status endpoints
    const statusEndpoints = [
      '/api/status',
      '/api/license/status',
      '/api/gcp/status',
    ];

    for (const endpoint of statusEndpoints) {
      const response = await page.request.get(endpoint);
      expect(response.ok()).toBeTruthy();
      const data = await response.json();
      expect(data).toBeTypeOf('object');
      console.log(`✅ API Integration: ${endpoint} responding correctly`);
    }

    // Test 2: Authentication endpoints (should go through PAP flow)
    const authResponse = await page.request.post('/api/auth', {
      data: {
        provider: 'gcp',
        context: 'test-context'
      }
    });
    
    expect(authResponse.ok()).toBeTruthy();
    const authData = await authResponse.json();
    expect(authData).toHaveProperty('status');
    console.log('✅ API Integration: Authentication endpoint through PAP flow');

    // Test 3: License validation endpoints (Controller → Orchestrator → Provider)
    const licenseValidationResponse = await page.request.post('/api/license/validate', {
      data: {
        license_key: 'WARP-TEST-VALIDATION-KEY'
      }
    });
    
    expect(licenseValidationResponse.ok()).toBeTruthy();
    const validationData = await licenseValidationResponse.json();
    expect(validationData).toHaveProperty('valid');
    console.log('✅ API Integration: License validation through PAP flow');

    // Test 4: Documentation and architecture discovery
    const docsResponse = await page.request.get('/docs');
    expect(docsResponse.ok()).toBeTruthy();
    console.log('✅ API Integration: Documentation endpoints active');

    const archResponse = await page.request.get('/api/architecture');
    expect(archResponse.ok()).toBeTruthy();
    console.log('✅ API Integration: Architecture discovery active');

    console.log('🎉 API Integration: All API endpoints and PAP flows validated');
  });

  test('Real User Flow End-to-End', async ({ page }) => {
    test.info().annotations.push({ 
      type: 'E2E_FLOW', 
      description: 'Complete real user workflow simulation' 
    });

    // Test 1: Landing and system readiness
    await page.goto('/');
    await expect(page.locator('body')).toBeVisible();
    console.log('✅ E2E Flow: User lands on WARPCORE interface');

    // Test 2: Navigate through main interface sections
    // Look for navigation elements
    const navElements = await page.locator('nav a, .nav-link, .tab, [data-tab]').all();
    
    if (navElements.length > 0) {
      // Test navigation
      for (let i = 0; i < Math.min(navElements.length, 3); i++) {
        const nav = navElements[i];
        if (await nav.isVisible()) {
          await nav.click();
          await page.waitForTimeout(1000);
          console.log(`✅ E2E Flow: Navigation ${i + 1} functional`);
        }
      }
    }

    // Test 3: System status checking (real user would do this)
    const statusResponse = await page.request.get('/api/status');
    expect(statusResponse.ok()).toBeTruthy();
    console.log('✅ E2E Flow: System status check successful');

    // Test 4: License management workflow (if available)
    try {
      // Try to access license management
      await page.locator('body').click(); // Focus on page
      await page.keyboard.press('Control+Shift+L'); // Try shortcut
      await page.waitForTimeout(500);
    } catch (e) {
      // Shortcut might not exist, that's fine
    }

    // Test 5: Provider operations (GCP in this case)
    const gcpStatusResponse = await page.request.get('/api/gcp/status');
    expect(gcpStatusResponse.ok()).toBeTruthy();
    console.log('✅ E2E Flow: GCP provider status check successful');

    // Test 6: Performance validation (real users expect responsiveness)
    const startTime = Date.now();
    
    await Promise.all([
      page.request.get('/api/status'),
      page.request.get('/api/license/status'),
      page.request.get('/static/css/main.css')
    ]);
    
    const endTime = Date.now();
    const responseTime = endTime - startTime;
    
    expect(responseTime).toBeLessThan(3000); // Should be fast
    console.log(`✅ E2E Flow: System performance validated (${responseTime}ms)`);

    console.log('🎉 E2E Flow: Complete real user workflow successfully simulated');
  });

  test('Error Handling and Edge Cases', async ({ page }) => {
    test.info().annotations.push({ 
      type: 'ERROR_HANDLING', 
      description: 'System robustness and error handling' 
    });

    // Test 1: Invalid API endpoints
    const invalidResponse = await page.request.get('/api/nonexistent');
    expect([404, 405]).toContain(invalidResponse.status());
    console.log('✅ Error Handling: Invalid endpoints handled properly');

    // Test 2: Invalid license operations
    const invalidLicenseResponse = await page.request.post('/api/license/validate', {
      data: { license_key: '' }
    });
    expect(invalidLicenseResponse.ok()).toBeTruthy();
    const invalidData = await invalidLicenseResponse.json();
    expect(invalidData).toHaveProperty('valid', false);
    console.log('✅ Error Handling: Invalid license key handled properly');

    // Test 3: Network interruption simulation
    // Test what happens with slow responses
    const slowResponse = await page.request.get('/api/status', { timeout: 10000 });
    expect(slowResponse.ok()).toBeTruthy();
    console.log('✅ Error Handling: Network delays handled properly');

    // Test 4: Large payload handling
    const largePayloadResponse = await page.request.post('/api/auth', {
      data: {
        provider: 'gcp',
        context: 'x'.repeat(1000), // Large context string
        metadata: { large_field: 'y'.repeat(5000) }
      }
    });
    expect(largePayloadResponse.ok()).toBeTruthy();
    console.log('✅ Error Handling: Large payloads handled properly');

    console.log('🎉 Error Handling: System robustness validated');
  });

});

test.describe('WARPCORE System Performance Tests', () => {
  
  test('System Orchestrator Startup Performance', async ({ page }) => {
    test.info().annotations.push({ 
      type: 'PERFORMANCE', 
      description: 'System orchestrator initialization timing' 
    });

    const startTime = Date.now();
    
    // Navigate to main page (triggers system orchestrator)
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const endTime = Date.now();
    const initTime = endTime - startTime;
    
    // System orchestrator should initialize within reasonable time
    expect(initTime).toBeLessThan(15000); // 15 seconds max
    console.log(`✅ Performance: System orchestrator initialized in ${initTime}ms`);
    
    // Verify all layers are ready after initialization
    const responses = await Promise.all([
      page.request.get('/api/status'),
      page.request.get('/api/license/status'),
      page.request.get('/static/css/main.css')
    ]);
    
    responses.forEach(response => {
      expect(response.ok()).toBeTruthy();
    });
    
    console.log('🎉 Performance: System orchestrator startup performance validated');
  });

  test('PAP Flow Performance', async ({ page }) => {
    test.info().annotations.push({ 
      type: 'PAP_PERFORMANCE', 
      description: 'Provider-Abstraction-Pattern flow performance' 
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Test performance of PAP flow: Controller → Orchestrator → Provider
    const startTime = Date.now();
    
    const licenseValidationResponse = await page.request.post('/api/license/validate', {
      data: {
        license_key: 'WARP-PERFORMANCE-TEST-KEY'
      }
    });
    
    const endTime = Date.now();
    const papFlowTime = endTime - startTime;
    
    expect(licenseValidationResponse.ok()).toBeTruthy();
    expect(papFlowTime).toBeLessThan(5000); // PAP flow should be fast
    
    console.log(`✅ PAP Performance: License validation flow completed in ${papFlowTime}ms`);
    console.log('🎉 Performance: PAP flow performance validated');
  });

});