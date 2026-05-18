import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: 'tests',
  use: {
    // Configure the testing framework here
    testFramework: 'jest',
  },
});