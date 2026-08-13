import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: process.env.DOCKER_ENV === 'true' ? 'http://api:8000' : 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: process.env.DOCKER_ENV === 'true' ? 'ws://api:8000' : 'ws://localhost:8000',
        ws: true,
      },
    },
  },
})
