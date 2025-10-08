const { test, expect } = require('@playwright/test');

test.describe('License Modal Structure - Component Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should have license modal element in DOM', async ({ page }) => {
    const modal = page.locator('#license-modal');
    await expect(modal).toBeAttached();
  });

  test('should have modal title with correct text', async ({ page }) => {
    const title = page.locator('#license-modal .modal-title');
    await expect(title).toContainText('WARPCORE License Activation');
  });

  test('should have all required license tabs', async ({ page }) => {
    const activateTab = page.locator('.license-tab:has-text("Activate License")');
    const trialTab = page.locator('.license-tab:has-text("Start Trial")');
    const upgradeTab = page.locator('.license-tab:has-text("Upgrade")');

    await expect(activateTab).toBeAttached();
    await expect(trialTab).toBeAttached();
    await expect(upgradeTab).toBeAttached();
  });

  test('should have license key input field', async ({ page }) => {
    const licenseInput = page.locator('#license-key');
    await expect(licenseInput).toBeAttached();
    await expect(licenseInput).toHaveAttribute('placeholder');
  });

  test('should have user email input field', async ({ page }) => {
    const emailInput = page.locator('#user-email');
    await expect(emailInput).toBeAttached();
    await expect(emailInput).toHaveAttribute('type', 'email');
  });

  test('should have validate button', async ({ page }) => {
    const validateBtn = page.locator('button:has-text("Validate")');
    await expect(validateBtn).toBeAttached();
  });

  test('should have activate button', async ({ page }) => {
    const activateBtn = page.locator('button:has-text("Activate License")');
    await expect(activateBtn).toBeAttached();
  });

  test('should have trial email input', async ({ page }) => {
    const trialEmail = page.locator('#trial-email');
    await expect(trialEmail).toBeAttached();
    await expect(trialEmail).toHaveAttribute('type', 'email');
  });

  test('should have close button', async ({ page }) => {
    const closeBtn = page.locator('#license-modal .modal-close');
    await expect(closeBtn).toBeAttached();
  });

  test('should have license validation result div', async ({ page }) => {
    const resultDiv = page.locator('#license-validation-result');
    await expect(resultDiv).toBeAttached();
  });
});