import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const THIS_DIR = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(THIS_DIR, '..', '..');

test.describe('Phase 4 evidence UI', () => {
  test('loads /evidence, shows sources section, and can submit a search', async ({ page, request }) => {
    // Navigate to the Evidence page
    await page.goto('/evidence');
    await expect(page.locator('h2')).toContainText('Evidence');

    // Sources section header is always visible
    await expect(page.locator('h3:has-text("Sources")')).toBeVisible();
    await expect(page.locator('h3:has-text("Search")')).toBeVisible();

    // Ingest a sample source via the API so the list is non-empty
    const seedFile = path.join(REPO_ROOT, 'data', 'documents', `seed-${Date.now()}.txt`);
    const content = '# Test Section\nSome search-able content with unique words: metacentric stability example\n';
    fs.mkdirSync(path.dirname(seedFile), { recursive: true });
    fs.writeFileSync(seedFile, content, 'utf-8');

    const r = await request.post('http://127.0.0.1:8000/api/v1/evidence/sources', {
      data: {
        title: 'Seeded Stability Doc',
        source_type: 'textbook',
        authority_level: 'academic',
        local_file_path: seedFile,
      },
    });
    expect(r.status()).toBe(200);

    // Reload the page so the query refetches
    await page.reload();
    await expect(
      page.locator('li:has-text("Seeded Stability Doc")').first(),
    ).toBeVisible();

    // Type a query and submit
    await page.fill('input[placeholder="Search evidence..."]', 'metacentric');
    await page.click('button:has-text("Search")');
    await expect(page.locator('h3:has-text("Results")').first()).toBeVisible();
  });

  test('evidence sidebar link is present', async ({ page }) => {
    await page.goto('/');
    await expect(
      page.locator('a[href="/evidence"]:has-text("Evidence")').first(),
    ).toBeVisible();
  });
});
