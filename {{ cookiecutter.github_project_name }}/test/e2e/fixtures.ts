import { test as base, chromium, type BrowserContext } from '@playwright/test';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const dirname = path.dirname(fileURLToPath(import.meta.url));
// Built by `pnpm build` (wxt's default Chromium/MV3 output directory).
const EXTENSION_PATH = path.resolve(dirname, '../../.output/chrome-mv3');

export const test = base.extend<{
  context: BrowserContext;
  extensionId: string;
}>({
  // Playwright's test.extend() requires a literal object-destructuring
  // pattern here, even unused — the directive below must sit on the line
  // immediately above the code it covers, or it silently disables nothing.
  // eslint-disable-next-line no-empty-pattern
  context: async ({}, use) => {
    const context = await chromium.launchPersistentContext('', {
      headless: true,
      args: [
        `--disable-extensions-except=${EXTENSION_PATH}`,
        `--load-extension=${EXTENSION_PATH}`,
      ],
    });
    await use(context);
    await context.close();
  },
  extensionId: async ({ context }, use) => {
    let [worker] = context.serviceWorkers();
    if (!worker) {
      worker = await context.waitForEvent('serviceworker');
    }
    // Not `.split('/')[2]` — `.wxt/tsconfig.json` sets
    // noUncheckedIndexedAccess, which types that as `string | undefined`.
    const extensionId = new URL(worker.url()).hostname;
    await use(extensionId);
  },
});

export const expect = test.expect;
