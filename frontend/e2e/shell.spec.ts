import { expect, test, type Page } from '@playwright/test';

/** Collects console errors and CSP violations so tests can assert the page runs cleanly. */
async function watchForProblems(page: Page): Promise<string[]> {
  const problems: string[] = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') problems.push(`console: ${msg.text()}`);
  });
  page.on('pageerror', (err) => problems.push(`pageerror: ${err.message}`));
  await page.addInitScript(() => {
    document.addEventListener('securitypolicyviolation', (event) => {
      console.error(`CSP violation: ${event.violatedDirective} ${event.blockedURI}`);
    });
  });
  return problems;
}

test('home page renders under the strict CSP with no errors', async ({ page }) => {
  const problems = await watchForProblems(page);

  await page.goto('/');

  await expect(page.getByRole('heading', { level: 1 })).toContainText('Less typing');
  await expect(page.getByTestId('workflow-card')).toHaveCount(2);
  expect(problems).toEqual([]);
});

test('self-hosted fonts load', async ({ page }) => {
  await page.goto('/');

  const fontFamily = await page
    .getByRole('heading', { level: 1 })
    .evaluate((el) => getComputedStyle(el).fontFamily);
  expect(fontFamily).toContain('Source Serif 4');
  await page.evaluate(() => document.fonts.ready);
  const loaded = await page.evaluate(() =>
    [...document.fonts].some((f) => f.family.includes('Source Serif 4') && f.status === 'loaded'),
  );
  expect(loaded).toBe(true);
});

test('navigation reaches Inbox and Ask, and deep links work', async ({ page }) => {
  const problems = await watchForProblems(page);

  await page.goto('/');
  await page.getByRole('navigation', { name: 'Main' }).getByRole('link', { name: 'Inbox' }).click();
  await expect(page).toHaveURL(/\/inbox$/);
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Inbox');

  await page.goto('/ask');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Ask');
  expect(problems).toEqual([]);
});

test('no horizontal scroll at this viewport', async ({ page }) => {
  await page.goto('/');

  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow).toBeLessThanOrEqual(0);
});

test('screenshot for review', async ({ page }, testInfo) => {
  await page.goto('/');
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: testInfo.outputPath('home.png'), fullPage: true });
});
