import { test, expect } from '@playwright/test';

test('Phase 1 happy path: project → task → cancel', async ({ page }) => {
  const name = `Playwright ${Date.now()}`;

  // 1. Dashboard loads with project list
  await page.goto('/');
  await expect(page.locator('h2')).toContainText('Dashboard');

  // 2. Go to Projects, create a new project
  await page.click('a[href="/projects"]');
  await page.waitForURL('**/projects');

  await page.fill('input[name="name"]', name);
  await page.click('button[type="submit"]');

  // 3. Lands on ProjectDetail after create (route: /projects/:id)
  await page.waitForURL(/\/projects\/[^/]+/);
  await expect(page.locator('h2')).toContainText('Project');

  // 4. Create a task
  await page.fill('input[name="user_request"]', 'playwright test task');
  await page.click('button:has-text("Create Task")');

  // 5. Task list refreshes, task visible
  await expect(page.locator('li a:has-text("playwright test task")').first()).toBeVisible();

  // 6. Open the task detail
  await page.click('li a:has-text("playwright test task")');
  await page.waitForURL(/\/tasks\/[^/]+/);
  await expect(page.locator('span:has-text("pending")').first()).toBeVisible();

  // 7. Cancel it
  await page.click('button:has-text("Cancel")');
  await expect(page.locator('span:has-text("cancelled")').first()).toBeVisible();
});
