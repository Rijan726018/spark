import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [react()],

  server: {
    port: 3000,
    open: false,   // Electron opens the window, not the browser
    strictPort: true,
    host: 'localhost',
  },

  // When building for Electron production, use relative paths
  // so the loaded index.html can find assets regardless of cwd
  base: mode === 'production' ? './' : '/',

  build: {
    outDir:       'dist',
    emptyOutDir:  true,
    sourcemap:    false,
    // Chunk size warning threshold
    chunkSizeWarningLimit: 2000,
    rollupOptions: {
      output: {
        // Split vendor chunks for faster reload in dev
        manualChunks: {
          'lightweight-charts': ['lightweight-charts'],
          'react-vendor':       ['react', 'react-dom'],
        },
      },
    },
  },

  // Make sure HMR works when loaded inside Electron
  define: {
    __APP_VERSION__: JSON.stringify('3.0.0'),
  },
}));
