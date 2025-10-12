import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load env file based on mode
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [
      react({
        // Enable Fast Refresh for React
        fastRefresh: true,
        // Babel plugins for optimization
        babel: {
          plugins: [
            // Add any Babel plugins here if needed
          ],
        },
      }),
    ],

    // Path resolution
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
        '@components': path.resolve(__dirname, './src/components'),
        '@types': path.resolve(__dirname, './src/types'),
        '@styles': path.resolve(__dirname, './src/styles'),
      },
    },

    // Development server
    server: {
      port: 3000,
      host: true, // Listen on all addresses
      strictPort: false, // Try next port if 3000 is taken
      open: false, // Don't auto-open browser
      cors: true,
      proxy: {
        '/api': {
          target: env.VITE_API_URL || 'http://localhost:8000',
          changeOrigin: true,
          secure: false,
          ws: true, // WebSocket support
        },
      },
      hmr: {
        overlay: true, // Show error overlay
      },
    },

    // Preview server (for production builds)
    preview: {
      port: 4173,
      host: true,
      strictPort: false,
      open: false,
    },

    // Build configuration
    build: {
      outDir: 'dist',
      assetsDir: 'assets',
      sourcemap: mode === 'development', // Source maps only in dev
      minify: 'terser', // Use terser for better minification
      terserOptions: {
        compress: {
          drop_console: mode === 'production', // Remove console.log in production
          drop_debugger: true,
        },
      },
      // Chunk size warning limit
      chunkSizeWarningLimit: 1000,
      // Rollup options for advanced configuration
      rollupOptions: {
        output: {
          // Manual chunk splitting for better caching
          manualChunks: {
            // Vendor chunks
            'react-vendor': ['react', 'react-dom', 'react-router-dom'],
            'ui-vendor': ['framer-motion', 'recharts'],
            'query-vendor': ['@tanstack/react-query', 'axios'],
          },
          // Asset file naming
          assetFileNames: (assetInfo) => {
            const info = assetInfo.name?.split('.') || []
            let extType = info[info.length - 1]
            if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(extType || '')) {
              extType = 'images'
            } else if (/woff2?|ttf|otf|eot/i.test(extType || '')) {
              extType = 'fonts'
            }
            return `assets/${extType}/[name]-[hash][extname]`
          },
          // Chunk file naming
          chunkFileNames: 'assets/js/[name]-[hash].js',
          entryFileNames: 'assets/js/[name]-[hash].js',
        },
      },
      // CSS code splitting
      cssCodeSplit: true,
      // Report compressed size
      reportCompressedSize: true,
      // Optimize dependencies
      commonjsOptions: {
        include: [/node_modules/],
        transformMixedEsModules: true,
      },
    },

    // Dependency optimization
    optimizeDeps: {
      include: [
        'react',
        'react-dom',
        'react-router-dom',
        '@tanstack/react-query',
        'axios',
        'framer-motion',
      ],
      exclude: ['@vitejs/plugin-react'],
    },

    // CSS configuration
    css: {
      modules: {
        localsConvention: 'camelCase',
      },
      preprocessorOptions: {
        // Add preprocessor options if using SASS/SCSS
      },
      devSourcemap: mode === 'development',
    },

    // Environment variables
    envPrefix: 'VITE_',

    // Enable esbuild for faster builds
    esbuild: {
      logOverride: { 'this-is-undefined-in-esm': 'silent' },
      drop: mode === 'production' ? ['console', 'debugger'] : [],
    },

    // JSON handling
    json: {
      namedExports: true,
      stringify: false,
    },

    // Performance options
    worker: {
      format: 'es',
    },
  }
})
