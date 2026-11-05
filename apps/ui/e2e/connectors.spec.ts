import { test, expect } from '@playwright/test';

test('SOLIDWORKS capability status appears on connectors page', async ({ page }) => {
  await page.goto('/connectors');
  await expect(page.locator('h2')).toContainText('Connectors');
  await expect(page.locator('li:has-text("SOLIDWORKS 2022")')).toBeVisible();
  await expect(page.locator('li:has-text("SOLIDWORKS 2022")').getByText(/unknown/)).toBeVisible();
});
