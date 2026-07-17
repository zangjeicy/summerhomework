import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const baseCss = readFileSync(resolve(process.cwd(), 'src/index.css'), 'utf8');
const ruyiThemeCss = readFileSync(resolve(process.cwd(), 'src/styles/themes/ruyi.css'), 'utf8');
const ruyiArtCss = readFileSync(resolve(process.cwd(), 'src/styles/themes/ruyi-art.css'), 'utf8');

const DEFINED_SURFACE_TOKENS = [
  '--surface-card-radius',
  '--surface-card-border-width',
  '--surface-card-bg-alpha',
  '--surface-card-background',
  '--surface-card-border',
  '--surface-card-backdrop-blur',
  '--surface-card-backdrop-saturate',
  '--surface-card-backdrop',
  '--surface-card-shadow',
  '--surface-inset-radius',
  '--surface-inset-background',
  '--surface-inset-border',
  '--surface-inset-shadow',
  '--surface-floating-radius',
  '--surface-floating-background',
  '--surface-floating-backdrop',
  '--surface-floating-shadow',
] as const;

const CONSUMED_SURFACE_TOKENS = [
  '--surface-card-radius',
  '--surface-card-border-width',
  '--surface-card-border',
  '--surface-card-background',
  '--surface-card-backdrop',
  '--surface-card-shadow',
] as const;

describe('Ruyi card surface theme contract', () => {
  it('defines card geometry and glass behavior as theme tokens', () => {
    for (const token of DEFINED_SURFACE_TOKENS) {
      expect(ruyiThemeCss).toContain(`${token}:`);
    }
  });

  it('routes primary card classes through the shared token-driven surface rule', () => {
    expect(baseCss).toMatch(/@layer components\s*\{\s*:where\(/);

    const sharedRule = baseCss.match(
      /:where\(([^)]*\.surface-card[^)]*)\)\s*\{([^}]*)\}/,
    );

    expect(sharedRule).not.toBeNull();

    const selectorList = sharedRule?.[1] ?? '';
    const declarations = sharedRule?.[2] ?? '';

    for (const className of [
      '.surface-card',
      '.terminal-card',
      '.glass-card',
      '.dashboard-card',
      '.glass-panel',
      '.glass-panel-lg',
    ]) {
      expect(selectorList).toContain(className);
    }

    for (const token of CONSUMED_SURFACE_TOKENS) {
      expect(declarations).toContain(`var(${token})`);
    }
  });

  it('keeps the generated-art layer free of component material overrides', () => {
    for (const selector of [
      '.surface-card',
      '.terminal-card',
      '.glass-card',
      '.dashboard-card',
      '.glass-panel',
      '.home-rail-card',
    ]) {
      expect(ruyiArtCss).not.toContain(selector);
    }
  });
});
