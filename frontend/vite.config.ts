import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 3090,
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://172.168.1.95:8109',
        changeOrigin: true,
      },
      '/ws': {
        target: process.env.VITE_WS_URL || 'ws://172.168.1.95:8109',
        ws: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          query: ['@tanstack/react-query'],
          ui: ['@headlessui/react', '@heroicons/react', 'framer-motion'],
        },
      },
    },
  },
});
