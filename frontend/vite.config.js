'use strict';

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'build',
    sourcemap: false,
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
      },
    },
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          animations: ['framer-motion'],
          http: ['axios', 'socket.io-client'],
          icons: ['@heroicons/react']
        },
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: 'assets/[ext]/[name]-[hash].[ext]'
      }
    },
    chunkSizeWarningLimit: 1000
  },
  server: {
    port: 3000,
    host: '0.0.0.0',
    allowedHosts: [
      'webfix-mission.preview.emergentagent.com', 
      '.emergent.host',
      'agent-dashboard-25.preview.emergentagent.com',
      '.emergentagent.com',
      'Devskyy.app',
      '.Devskyy.app',
      'devskyy.app',
      '.devskyy.app'
    ],
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        secure: false
      }
    }
  },
  define: {
    'process.env.VITE_API_URL': JSON.stringify(process.env.VITE_API_URL || '/api'),
    'process.env.REACT_APP_BACKEND_URL': JSON.stringify(process.env.REACT_APP_BACKEND_URL || '/api')
  },
  optimizeDeps: {
    include: ['react', 'react-dom', 'framer-motion', 'axios']
  },
  esbuild: {
    drop: ['console', 'debugger']
  }
})