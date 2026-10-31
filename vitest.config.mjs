import {fileURLToPath} from 'node:url';
import {defineConfig} from 'vitest/config';

const webSource = fileURLToPath(new URL('./apps/web/src/', import.meta.url));

export default defineConfig({
  resolve: {alias: {'@web': webSource}},
  test: {include: ['test/web/**/*.test.{ts,tsx}']},
});
