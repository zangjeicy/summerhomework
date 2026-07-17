import { createHash } from 'node:crypto';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { expect, test, type Locator, type Page } from '@playwright/test';
import catalogData from './page-catalog.json' with { type: 'json' };

type ReadyTarget = {
  kind: 'placeholder' | 'testId' | 'heading' | 'css';
  value: string;
};

type PageCatalogItem = {
  path: string;
  id: string;
  name: string;
  screenshot: string;
  mode?: 'mocked-login';
  allowedApiResponses?: Array<{ path: string; statuses: number[] }>;
  ready: ReadyTarget;
};

type AuditResult = {
  id: string;
  name: string;
  route: string;
  ok: boolean;
  screenshot?: string;
  screenshotSha256?: string;
  viewportScreenshot?: string;
  viewportScreenshotSha256?: string;
  consoleErrors: string[];
  pageErrors: string[];
  failedRequests: string[];
  failedApiResponses: string[];
  allowedApiResponses: string[];
  error?: string;
};

const catalog = catalogData as PageCatalogItem[];
const currentDir = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(currentDir, '..');
const outputDir = path.resolve(
  process.env.DSA_PAGE_AUDIT_OUTPUT_DIR || path.join(webRoot, 'test-results', 'page-audit'),
);
const results: AuditResult[] = [];

function readyLocator(page: Page, target: ReadyTarget): Locator {
  if (target.kind === 'placeholder') return page.getByPlaceholder(target.value);
  if (target.kind === 'testId') return page.getByTestId(target.value);
  if (target.kind === 'heading') return page.getByRole('heading', { name: target.value, exact: true });
  return page.locator(target.value);
}

async function prepareLoginPreview(page: Page) {
  await page.route('**/api/v1/auth/status', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        authEnabled: true,
        loggedIn: false,
        passwordSet: false,
        passwordChangeable: false,
        setupState: 'no_password',
      }),
    });
  });
}

function redactLocators(page: Page): Locator[] {
  return [
    page.locator('input[type="password"]'),
    page.locator('input[name*="key" i], input[name*="token" i], input[name*="secret" i]'),
    page.locator('textarea[name*="key" i], textarea[name*="token" i], textarea[name*="secret" i]'),
  ];
}

function isAllowedApiResponse(item: PageCatalogItem, url: string, status?: number): boolean {
  return (item.allowedApiResponses || []).some((allowed) => (
    url.includes(allowed.path) && (status == null || allowed.statuses.includes(status))
  ));
}

test.describe.configure({ mode: 'serial' });

test.afterAll(async () => {
  await mkdir(outputDir, { recursive: true });
  await writeFile(
    path.join(outputDir, '页面验收报告.json'),
    `${JSON.stringify({ generatedAt: new Date().toISOString(), pages: results }, null, 2)}\n`,
    'utf8',
  );
});

for (const item of catalog) {
  test(`${item.name}可以正常访问并生成安全截图`, async ({ page }) => {
    const consoleErrors: string[] = [];
    const pageErrors: string[] = [];
    const failedRequests: string[] = [];
    const failedApiResponses: string[] = [];
    const allowedApiResponses: string[] = [];
    const result: AuditResult = {
      id: item.id,
      name: item.name,
      route: item.path,
      ok: false,
      consoleErrors,
      pageErrors,
      failedRequests,
      failedApiResponses,
      allowedApiResponses,
    };

    page.on('console', (message) => {
      if (message.type() !== 'error') return;
      const locationUrl = message.location().url || '';
      if (
        message.text().startsWith('Failed to load resource:')
        && isAllowedApiResponse(item, locationUrl)
      ) return;
      consoleErrors.push(locationUrl ? `${message.text()} @ ${locationUrl}` : message.text());
    });
    page.on('pageerror', (error) => pageErrors.push(error.message));
    page.on('requestfailed', (request) => {
      const failure = request.failure()?.errorText || 'unknown request failure';
      failedRequests.push(`${request.method()} ${request.url()} — ${failure}`);
    });
    page.on('response', (response) => {
      if (response.url().includes('/api/') && response.status() >= 400) {
        const detail = `${response.status()} ${response.request().method()} ${response.url()}`;
        if (isAllowedApiResponse(item, response.url(), response.status())) {
          allowedApiResponses.push(detail);
        } else {
          failedApiResponses.push(detail);
        }
      }
    });

    try {
      if (item.mode === 'mocked-login') await prepareLoginPreview(page);
      const response = await page.goto(item.path, { waitUntil: 'domcontentloaded', timeout: 30_000 });
      expect(response, `${item.name}没有主文档响应`).not.toBeNull();
      expect(response?.status(), `${item.name}主文档状态异常`).toBeLessThan(400);
      await expect(readyLocator(page, item.ready)).toBeVisible({ timeout: 20_000 });
      await page.waitForTimeout(1_500);

      await expect(page.getByText('页面加载失败', { exact: false })).toHaveCount(0);
      await expect(page.getByText('Route page failed to render or load', { exact: false })).toHaveCount(0);
      expect(pageErrors, `${item.name}存在页面运行时异常`).toEqual([]);
      expect(consoleErrors, `${item.name}存在 console.error`).toEqual([]);
      expect(failedRequests, `${item.name}存在网络请求失败`).toEqual([]);
      expect(failedApiResponses, `${item.name}存在失败 API 响应`).toEqual([]);

      await mkdir(outputDir, { recursive: true });
      const screenshotPath = path.join(outputDir, item.screenshot);
      const viewportPath = path.join(outputDir, item.screenshot.replace(/\.png$/i, '_首屏.png'));
      await page.evaluate(() => window.scrollTo(0, 0));
      const viewportScreenshot = await page.screenshot({
        path: viewportPath,
        fullPage: false,
        animations: 'disabled',
        mask: redactLocators(page),
      });
      const screenshot = await page.screenshot({
        path: screenshotPath,
        fullPage: true,
        animations: 'disabled',
        mask: redactLocators(page),
      });
      result.ok = true;
      result.screenshot = screenshotPath;
      result.screenshotSha256 = createHash('sha256').update(screenshot).digest('hex');
      result.viewportScreenshot = viewportPath;
      result.viewportScreenshotSha256 = createHash('sha256')
        .update(viewportScreenshot)
        .digest('hex');
    } catch (error) {
      result.error = error instanceof Error ? error.message : String(error);
      throw error;
    } finally {
      results.push(result);
    }
  });
}
