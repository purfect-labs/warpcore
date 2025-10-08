const { test, expect } = require('@playwright/test');

test.describe('License Modal Display - Integration Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
  });

  test('should show license modal when showLicenseModal is called', async ({ page }) => {
    // Call the function directly
    await page.evaluate(() => showLicenseModal());
    
    // Modal should be visible
    const modal = page.locator('#license-modal');
    await expect(modal).toBeVisible({ timeout: 5000 });
    
    // Title should be correct
    const title = page.locator('#license-modal .modal-title');
    await expect(title).toBeVisible();
  });

  test('should close license modal when closeLicenseModal is called', async ({ page }) => {
    // Open modal first
    await page.evaluate(() => showLicenseModal());
    await page.waitForTimeout(500);
    
    // Verify it's open
    const modal = page.locator('#license-modal');
    await expect(modal).toBeVisible();
    
    // Close it
    await page.evaluate(() => closeLicenseModal());
    await page.waitForTimeout(500);
    
    // Should be hidden
    await expect(modal).not.toBeVisible();
  });

  test('should switch license tabs correctly', async ({ page }) => {
    // Open modal
    await page.evaluate(() => showLicenseModal());
    await page.waitForTimeout(500);
    
    // Switch to trial tab
    await page.evaluate(() => showLicenseTab('trial'));
    await page.waitForTimeout(500);
    
    // Trial tab should be active
    const trialTab = page.locator('.license-tab:has-text("Start Trial")');
    await expect(trialTab).toHaveClass(/active/);
    
    // Trial content should be visible
    const trialContent = page.locator('#license-tab-trial');
    await expect(trialContent).toHaveClass(/active/);
  });

  test('should access modal via profile dropdown manage button', async ({ page }) => {
    // Click profile dropdown first
    const profileBtn = page.locator('.profile-btn');
    await expect(profileBtn).toBeVisible();
    await profileBtn.click();
    await page.waitForTimeout(500);
    
    // Click manage license button
    const manageBtn = page.locator('button:has-text("🔑 Manage")');
    await expect(manageBtn).toBeVisible();
    await manageBtn.click();
    await page.waitForTimeout(500);
    
    // Modal should appear
    const modal = page.locator('#license-modal');
    await expect(modal).toBeVisible();
  });

  test('should close modal when clicking close button', async ({ page }) => {
    // Open modal
    await page.evaluate(() => showLicenseModal());
    await page.waitForTimeout(500);
    
    // Click close button
    const closeBtn = page.locator('#license-modal .modal-close');
    await expect(closeBtn).toBeVisible();
    await closeBtn.click();
    await page.waitForTimeout(500);
    
    // Modal should be hidden
    const modal = page.locator('#license-modal');
    await expect(modal).not.toBeVisible();
  });

  test('should have license key input field functional', async ({ page }) => {
    // Open modal
    await page.evaluate(() => showLicenseModal());
    await page.waitForTimeout(500);
    
    // Fill license key
    const licenseInput = page.locator('#license-key');
    await expect(licenseInput).toBeVisible();
    await licenseInput.fill('WARP-TEST-1234-5678');
    
    // Verify input value
    const inputValue = await licenseInput.inputValue();
    expect(inputValue).toBe('WARP-TEST-1234-5678');
  });

  test('should generate hardware signature', async ({ page }) => {
    const signature = await page.evaluate(() => getHardwareSignature());
    
    expect(typeof signature).toBe('string');
    expect(signature.length).toBeGreaterThan(5);
    
    // Should be consistent
    const signature2 = await page.evaluate(() => getHardwareSignature());
    expect(signature).toBe(signature2);
  });
});