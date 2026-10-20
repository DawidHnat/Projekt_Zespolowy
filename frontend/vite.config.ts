import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";

function releaseVersion(): Plugin {
  const supplied = process.env.FLEET_FLOW_BUILD_SHA;
  if (supplied && !/^(?:[a-f0-9]{7}|[a-f0-9]{40})$/.test(supplied)) {
    throw new Error("FLEET_FLOW_BUILD_SHA must contain 7 or 40 lowercase hexadecimal characters");
  }
  const revision = supplied ? supplied.slice(0, 7) : "lokalnie";
  const publicUrl = new URL(process.env.FLEET_FLOW_PUBLIC_URL || "https://fleet-flow.pl");
  if (publicUrl.protocol !== "https:" || publicUrl.username || publicUrl.password || publicUrl.pathname !== "/" || publicUrl.search || publicUrl.hash) {
    throw new Error("FLEET_FLOW_PUBLIC_URL must be an HTTPS origin");
  }
  return {
    name: "fleet-flow-release-version",
    transformIndexHtml: (html) => html.replaceAll("__FLEET_FLOW_BUILD_SHA__", revision),
    generateBundle() {
      this.emitFile({
        type: "asset",
        fileName: "status.html",
        source: `<!doctype html><html lang="pl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fleet-Flow</title><style>body{font:1rem system-ui,sans-serif;background:#f3f7fb;color:#192a42;margin:0;display:grid;place-items:center;min-height:100vh}main{max-width:36rem;padding:2rem}a{color:#1479e8}footer{margin-top:2rem;color:#63758a}</style><main><h1>Fleet-Flow</h1><p>Wspólna przestrzeń zespołu do zarządzania flotą.</p><p><a href="${publicUrl.origin}/">Otwórz aplikację przez HTTPS</a></p><footer>Wersja <code data-build-sha="${revision}">${revision}</code></footer></main></html>`,
      });
    },
  };
}

export default defineConfig({
  plugins: [react(), releaseVersion()],
  envDir: "..",
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    proxy: { "/api": { target: "http://127.0.0.1:8000", changeOrigin: false } },
  },
  preview: { host: "127.0.0.1", port: 4173, strictPort: true },
});
