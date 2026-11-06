import { defineConfig, mergeConfig } from "vite";
import base from "./vite.config.ts";

// Test-only ports and proxy. Product configuration remains unchanged.
export default mergeConfig(base, defineConfig({
  envDir: false,
  server: {
    host: "127.0.0.1",
    port: 54173,
    strictPort: true,
    proxy: { "/api": { target: "http://127.0.0.1:58000", changeOrigin: false } },
  },
}));
