import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '..', '')
  const target = process.env.API_PROXY_TARGET ?? env.API_PROXY_TARGET ?? 'http://127.0.0.1:8000'
  return {
    plugins: [react()],
    envDir: '..',
    server: {
      host: '127.0.0.1',
      port: 5173,
      strictPort: true,
      proxy: { '/api': { target }, '/health': { target } },
    },
    preview: { port: 4173, strictPort: true },
    build: { sourcemap: false },
  }
})
