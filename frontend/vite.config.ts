import path from "path";
import { fileURLToPath } from "url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function normalizeBasePath(value: string | undefined): string {
  if (!value) {
    return "";
  }
  return value.trim().replace(/\/+$/, "");
}

const basePath = normalizeBasePath(process.env.VITE_BASE_PATH);
const previewApiTarget =
  process.env.VITE_PREVIEW_API_TARGET ?? "http://localhost:8000";

const apiProxy = basePath
  ? {
      [`${basePath}/api`]: {
        target: previewApiTarget,
        changeOrigin: true,
        rewrite: (path: string) =>
          path.replace(new RegExp(`^${basePath}/api`), "/api"),
      },
    }
  : {
      "/api": {
        target: previewApiTarget,
        changeOrigin: true,
      },
    };

export default defineConfig({
  base: basePath ? `${basePath}/` : "/",
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
    allowedHosts: ['foundry.inapp.com']
  },
  preview: {
    port: 4501,
    host: "0.0.0.0",
    allowedHosts: ["foundry.inapp.com"],
    proxy: apiProxy,
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test/setup.ts",
  },
});
