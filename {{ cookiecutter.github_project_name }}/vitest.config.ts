import { defineConfig } from 'vitest/config';
import { WxtVitest } from 'wxt/testing/vitest-plugin';

export default defineConfig({
  plugins: [WxtVitest()],
  test: {
    // happy-dom rather than jsdom for speed. It implements less of the DOM,
    // so test real-browser behaviour with Playwright (test/e2e/). If a unit
    // test needs a DOM feature happy-dom lacks, run `pnpm add -D jsdom` and
    // put `// @vitest-environment jsdom` at the top of that test file, or
    // change this line to switch the whole suite.
    environment: 'happy-dom',
    include: ['test/unit/**/*.test.ts'],
  },
});
