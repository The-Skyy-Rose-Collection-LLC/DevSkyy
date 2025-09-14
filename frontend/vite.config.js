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
      mangle: {
        safari10: true,
      },
    },
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          // Vendor chunks
          if (id.includes('node_modules')) {
            if (id.includes('react') || id.includes('react-dom')) {
              return 'vendor-react';
            }
            if (id.includes('framer-motion')) {
              return 'vendor-animations';
            }
            if (id.includes('axios') || id.includes('socket.io-client')) {
              return 'vendor-http';
            }
            if (id.includes('@heroicons')) {
              return 'vendor-icons';
            }
            if (id.includes('tailwindcss')) {
              return 'vendor-styles';
            }
            return 'vendor-other';
          }
          
          // Component chunks based on routes/features
          if (id.includes('components/Agent')) {
            return 'feature-agents';
          }
          if (id.includes('components/Dashboard')) {
            return 'feature-dashboard';
          }
          if (id.includes('components/WordPress')) {
            return 'feature-wordpress';
          }
          if (id.includes('components/Performance')) {
            return 'feature-performance';
          }
        },
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: 'assets/[ext]/[name]-[hash].[ext]'
      }
    },
    chunkSizeWarningLimit: 500,
    // Enable tree shaking
    treeshake: {
      moduleSideEffects: false,
      propertyReadSideEffects: false,
      unknownGlobalSideEffects: false
    }
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
    include: ['react', 'react-dom', 'framer-motion', 'axios'],
    exclude: ['@heroicons/react'] // Icons will be loaded on demand
  },
  esbuild: {
    drop: ['console', 'debugger'],
    treeShaking: true
  },
  // Performance optimizations
  experimental: {
    renderBuiltUrl(filename, { hostId, hostType, type }) {
      // Implement CDN URL generation if needed
      return filename;
    }
  }
})