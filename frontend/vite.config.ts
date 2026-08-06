import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        // Use localhost for local dev; Docker Compose overrides this via env or network
        target: process.env.VITE_API_TARGET || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
    // Security headers for DuckDB WASM SharedArrayBuffer support (story 6.4.3)
    // COEP + COOP are required for SharedArrayBuffer in modern browsers.
    // Without these, DuckDB WASM silently falls back to single-threaded mode.
    headers: {
      'Cross-Origin-Embedder-Policy': 'require-corp',
      'Cross-Origin-Opener-Policy': 'same-origin',
    },
  },
})
