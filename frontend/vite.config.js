import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    hmr: {
      // Fix WebSocket connection issues
      host: 'localhost',
      port: 5173,
      protocol: 'ws'
    },
    proxy: {
      '/auth': 'http://localhost:8000',
      '/users': 'http://localhost:8000',
      '/v1': 'http://localhost:8000'
    }
  },
  // Ensure proper module resolution
  resolve: {
    extensions: ['.js', '.jsx', '.ts', '.tsx']
  },
  // Force dependency optimization
  optimizeDeps: {
    include: ['react', 'react-dom']
  }
})
