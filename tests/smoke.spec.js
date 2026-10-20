const { test, expect } = require('@playwright/test');

test('home page loads without errors', async ({ page }) => {
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  await page.goto('/');
  await expect(page.locator('h1').first()).toBeVisible();
  expect(errors).toEqual([]);
});

test('launch links point to the trading app', async ({ page }) => {
  await page.goto('/');
  const hrefs = await page.$$eval('a[data-launch]', (links) => links.map((a) => a.href));
  expect(hrefs.length).toBeGreaterThan(5);
  for (const h of hrefs) expect(h).toBe('https://dex.vorqexa.xyz/');
});

test('docs open from the Docs link and close with Escape', async ({ page }) => {
  await page.goto('/');
  await page.locator('a[data-vorqexa-docs]:visible').first().click();
  const overlay = page.locator('#vorqexa-docs-overlay');
  await expect(overlay).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(overlay).toBeHidden();
});

test('no sideways scrolling on a phone', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 800 });
  await page.goto('/');
  const extra = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(extra).toBeLessThanOrEqual(1);
});
