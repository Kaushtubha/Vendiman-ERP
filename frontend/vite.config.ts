import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// =============================================================================
// vite.config.ts — Vite Build Configuration
// =============================================================================
//
// WHY Vite (not Create React App, Webpack):
//   - Native ES modules during development: no bundling, instant HMR.
//     React component changes reflect in < 50ms vs 2-5 seconds with Webpack.
//   - Rollup for production: generates highly optimized, tree-shaken bundles.
//   - TypeScript support out-of-the-box (esbuild transpilation, not tsc).
//
// WHY path aliases (@/ prefix):
//   - `import { Button } from '@/components/ui/button'` is stable.
//   - `import { Button } from '../../components/ui/button'` breaks when files move.
//   - Configured in both vite.config.ts (build) and tsconfig.json (type checking).
//
// PROXY CONFIGURATION:
//   During development, Vite proxies `/api` requests to the FastAPI backend.
//   WHY: Avoids CORS issues in development. The browser sees one origin
//   (localhost:5173) for both the SPA and the API.
//   In production, Nginx handles this proxy.
//
// =============================================================================

export default defineConfig({
  plugins: [
    react({
      // WHY babel with react-refresh: Enables Fast Refresh — preserves
      // component state across hot reloads. Without it, every code change
      // resets all component state.
    }),
  ],

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },

  server: {
    port: 5173,
    host: true,             // Allow external connections (needed in Docker)
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // WHY changeOrigin: Backend sees requests as coming from localhost:8000,
        // not localhost:5173. Required for CORS to work correctly in development.
      },
      '/media': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },

  build: {
    outDir: 'dist',
    sourcemap: false,       // Enable for debugging in staging, disable in prod
    target: 'esnext',       // Modern browsers only — no IE11 polyfills needed
    rollupOptions: {
      output: {
        // WHY manual chunks: Prevent all vendor code from being one giant bundle.
        // Splitting React, React Query, charts into separate chunks enables
        // browser to cache them independently. React rarely changes (cache hit).
        // App code changes frequently (no cache).
        manualChunks: {
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          'vendor-query': ['@tanstack/react-query'],
          'vendor-charts': ['recharts'],
          'vendor-ui': [
            '@radix-ui/react-dialog',
            '@radix-ui/react-dropdown-menu',
            '@radix-ui/react-select',
            '@radix-ui/react-tabs',
            'framer-motion',
          ],
          'vendor-forms': ['react-hook-form', '@hookform/resolvers', 'zod'],
        },
      },
    },
    // WHY chunk size warning at 600KB: Bundles > 600KB are slow on mobile.
    // This warning forces us to split large dependencies.
    chunkSizeWarningLimit: 600,
  },

  // WHY esbuild for TypeScript: 100x faster than tsc for transpilation.
  // Type checking is done separately with `tsc --noEmit` in CI.
  esbuild: {
    target: 'esnext',
  },

  preview: {
    port: 4173,
    host: true,
  },
})
