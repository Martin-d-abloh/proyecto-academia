import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  css: {
    postcss: './postcss.config.js'
  },
  server: {
    proxy: {
      '/api': 'http://localhost:5001',
      '/descargar_documento': 'http://localhost:5001'
    }
  }
})
