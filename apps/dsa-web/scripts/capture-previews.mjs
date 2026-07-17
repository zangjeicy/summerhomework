// 前端页面预览截图脚本
// 用途：连真实后端（默认 http://127.0.0.1:8000，同源 serve 前端 SPA + API），
//       用 Playwright 遍历所有页面路由逐页截图，输出到 assets/preview/<version>/。
// 运行：node scripts/capture-previews.mjs [--base http://127.0.0.1:8000] [--version v0.1.0] [--theme both]
// 前置：后端已启动（python main.py --serve-only），Chromium 已装（npx playwright install chromium）。

import { chromium } from '@playwright/test';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { mkdir } from 'node:fs/promises';
import PAGE_CATALOG from '../e2e/page-catalog.json' with { type: 'json' };

const __dirname = dirname(fileURLToPath(import.meta.url));
// 仓库根目录：apps/dsa-web/scripts -> 上溯三级
const repoRoot = resolve(__dirname, '..', '..', '..');

// 解析命令行参数
function arg(name, fallback) {
  const idx = process.argv.indexOf(`--${name}`);
  return idx !== -1 && process.argv[idx + 1] ? process.argv[idx + 1] : fallback;
}

const BASE = arg('base', 'http://127.0.0.1:8000').replace(/\/$/, '');
const VERSION = arg('version', 'v0.1.0');
const THEME = arg('theme', 'both'); // light | dark | both
const ONLY = arg('only', ''); // 逗号分隔的页面名，只截这些页（如 --only login）；留空截全部
const OUT_DIR = resolve(repoRoot, 'assets', 'preview', VERSION);

// 路由 -> 文件名（与 src/App.tsx 的 <Route path> 保持一致）
const ROUTES = [
  ...PAGE_CATALOG.map((page) => ({ path: page.path, name: page.id })),
  { path: '/__not_found__', name: 'notfound' }, // 任意不存在路径命中 * -> NotFoundPage
];

const THEMES = THEME === 'both' ? ['light', 'dark'] : [THEME];
const onlyNames = ONLY ? ONLY.split(',').map((s) => s.trim()).filter(Boolean) : null;
const activeRoutes = onlyNames ? ROUTES.filter((r) => onlyNames.includes(r.name)) : ROUTES;

// 通过 next-themes 的 localStorage key 强制主题，避免依赖系统偏好
async function applyTheme(page, theme) {
  await page.addInitScript((t) => {
    try {
      window.localStorage.setItem('theme', t);
    } catch (e) {
      /* ignore */
    }
  }, theme);
}

async function main() {
  await mkdir(OUT_DIR, { recursive: true });
  console.log(`[capture] base=${BASE} version=${VERSION} themes=${THEMES.join(',')}`);
  console.log(`[capture] 输出目录: ${OUT_DIR}`);

  const browser = await chromium.launch();
  const results = [];

  for (const theme of THEMES) {
    const context = await browser.newContext({
      viewport: { width: 1440, height: 900 },
      deviceScaleFactor: 2, // 2x 高清截图
      colorScheme: theme,
      locale: 'zh-CN',
    });
    const page = await context.newPage();
    await applyTheme(page, theme);

    for (const route of activeRoutes) {
      const url = `${BASE}${route.path}`;
      const suffix = THEMES.length > 1 ? `.${theme}` : '';
      const file = resolve(OUT_DIR, `${route.name}${suffix}.png`);
      try {
        // 用 domcontentloaded 而非 networkidle：home/login 等页面有持续轮询/SSE，
        // networkidle（500ms 网络空闲）永远达不到会超时。改为 DOM 就绪后固定等待渲染。
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
        // 给图表/懒加载数据一点稳定时间
        await page.waitForTimeout(2500);
        await page.screenshot({ path: file, fullPage: true });
        console.log(`[ok]   ${theme.padEnd(5)} ${route.path.padEnd(20)} -> ${route.name}${suffix}.png`);
        results.push({ theme, route: route.path, file, ok: true });
      } catch (err) {
        console.error(`[fail] ${theme.padEnd(5)} ${route.path.padEnd(20)} : ${err.message}`);
        results.push({ theme, route: route.path, file, ok: false, error: err.message });
      }
    }
    await context.close();
  }

  await browser.close();

  const ok = results.filter((r) => r.ok).length;
  const fail = results.length - ok;
  console.log(`\n[capture] 完成: 成功 ${ok} / 失败 ${fail} （共 ${results.length}）`);
  if (fail > 0) process.exitCode = 1;
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
