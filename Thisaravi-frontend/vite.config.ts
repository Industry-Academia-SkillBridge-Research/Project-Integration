import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      // Thisaravi Backend API (port 8185)
      '/api': {
        target: 'http://localhost:8185',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      // LinkedIn Job Scraper (port 8000)
      '/scraper': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/scraper/, ''),
        configure: (proxy) => { proxy.on('error', () => {}); },
      },
      // Agent-Runtime / Candidate profiles (port 8002)
      '/agent-runtime': {
        target: 'http://localhost:8002',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/agent-runtime/, ''),
        configure: (proxy) => { proxy.on('error', () => {}); },
      },
      // Role-Skill-API (port 8181)
      '/role-skills': {
        target: 'http://localhost:8181',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/role-skills/, ''),
        configure: (proxy) => {
          proxy.on('error', (_err, _req, res) => {
            res.writeHead(503, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: 'Role-Skill-API unavailable' }));
          });
        },
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
