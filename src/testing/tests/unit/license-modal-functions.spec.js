const { test, expect } = require('@playwright/test');

test.describe('License Modal Functions - Unit Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should have showLicenseModal function available', async ({ page }) => {
    const functionExists = await page.evaluate(() => {
      return typeof showLicenseModal === 'function';
    });
    
    expect(functionExists).toBe(true);
  });

  test('should have closeLicenseModal function available', async ({ page }) => {
    const functionExists = await page.evaluate(() => {
      return typeof closeLicenseModal === 'function';
    });
    
    expect(functionExists).toBe(true);
  });

  test('should have validateLicenseKey function available', async ({ page }) => {
    const functionExists = await page.evaluate(() => {
      return typeof validateLicenseKey === 'function';
    });
    
    expect(functionExists).toBe(true);
  });

  test('should have getHardwareSignature function available', async ({ page }) => {
    const functionExists = await page.evaluate(() => {
      return typeof getHardwareSignature === 'function';
    });
    
    expect(functionExists).toBe(true);
  });

  test('getHardwareSignature should return a string', async ({ page }) => {
    const signature = await page.evaluate(() => {
      return getHardwareSignature();
    });
    
    expect(typeof signature).toBe('string');
    expect(signature.length).toBeGreaterThan(0);
  });
});