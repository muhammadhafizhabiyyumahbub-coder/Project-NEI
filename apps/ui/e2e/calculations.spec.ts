import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const THIS_DIR = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(THIS_DIR, '..', '..');

const API = 'http://127.0.0.1:8000/api/v1';

async function seedAndApproveFormula(name, equationText, implKey) {
  // Create a text source + register formula + advance to APPROVED_FOR_USE.
  // Playwright's `request` fixture can't be used at describe-level easily,
  // so use a real HTTP client with the app's default dev-mode auth (no cookie needed).
  const srcPath = path.join(REPO_ROOT, 'data', 'documents', `seed-${Date.now()}.txt`);
  fs.mkdirSync(path.dirname(srcPath), { recursive: true });
  fs.writeFileSync(srcPath, 'Reference material for engineering test.');

  async function postJSON(url, body) {
    const r = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error(`${url}: ${r.status} ${await r.text()}`);
    return r.json();
  }

  const src = await postJSON(`${API}/evidence/sources`, {
    title: 'Seed Source',
    source_type: 'textbook',
    authority_level: 'academic',
    local_file_path: srcPath,
  });
  const formula = await postJSON(`${API}/formulas`, {
    name: implKey,
    domain: name,
    equation_text: equationText,
    source_refs: [src.id],
  });
  for (const s of ['IMPLEMENTED', 'UNIT_TESTED', 'REFERENCE_CASE_TESTED', 'TECHNICAL_REVIEW', 'APPROVED_FOR_USE']) {
    await postJSON(`${API}/formulas/${formula.id}/advance`, { to_status: s, reason: 'e2e' });
  }
  return formula.id;
}

test.describe('Phase 5 calculations UI', () => {
  test('loads formulas, runs calculation, displays result + evidence_status', async ({ page }) => {
    await seedAndApproveFormula('geometry', 'V=L*W*H', 'box_volume');

    await page.goto('/calculations');
    await expect(page.locator('h2')).toContainText('Calculations');

    // Wait for the formula list to load
    await page.waitForTimeout(2000);

    // The formula list should include our seeded box_volume
    const formulaRow = page.locator('button.formula-row:has-text("box volume")').first();
    await expect(formulaRow).toBeVisible();
    await formulaRow.click();

    // Enter one field per quantity
    await page.locator('input[name="length"], input[placeholder="10"]').fill('10');
    await page.locator('input[name="width"], input[placeholder="3"]').fill('3');
    await page.locator('input[name="height"], input[placeholder="1"]').fill('1');
    await page.click('button:has-text("Run calculation")');
    await page.waitForTimeout(1500);

    // Result block with evidence_status should be visible
    await expect(page.locator('h4:has-text("Result")')).toBeVisible();
    const resultText = await page.locator('pre').first().textContent();
    expect(resultText).toContain('30');
  });
});
