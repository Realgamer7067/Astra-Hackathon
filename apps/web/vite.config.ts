import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const api = "http://127.0.0.1:8000";
const proxy = { "/health": api, "/api": api };

export default defineConfig({
  root: fileURLToPath(new URL(".", import.meta.url)),
  plugins: [react()],
  define: { CESIUM_BASE_URL: JSON.stringify("/cesium/") },
  server: { host: "127.0.0.1", proxy },
  preview: { host: "127.0.0.1", proxy },
});
