import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  use: {
    baseURL: 'http://127.0.0.1:5173',
    screenshot: 'only-on-failure',
  },
  webServer: [
    {
      command: 'npm run dev -- --host 127.0.0.1',
      cwd: '.',
      url: 'http://127.0.0.1:5173',
      reuseExistingServer: true,
    },
    {
      command: 'python -m uvicorn nei.main:app --host 127.0.0.1 --port 8000',
      cwd: '../..',
      url: 'http://127.0.0.1:8000/api/v1/health',
      reuseExistingServer: true,
    },
  ],
  reporter: 'list',
});
