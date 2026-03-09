import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://127.0.0.1:9000',
      '/timelapse_output': 'http://127.0.0.1:9000',
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    // Optimize for mobile
    target: 'es2020',
    minify: 'esbuild', // Use esbuild (built-in) instead of terser
    rollupOptions: {
      output: {
        // Chunk splitting for better caching
        manualChunks: {
          'vendor-leaflet': ['leaflet', 'react-leaflet'],
          'vendor-query': ['@tanstack/react-query'],
        },
      },
    },
    // Compress output
    cssMinify: true,
    reportCompressedSize: false,
    chunkSizeWarningLimit: 500,
  },
})
