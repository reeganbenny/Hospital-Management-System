import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import path from 'path';

export default defineConfig({
  server: {
    host: '::',
    port: 8080,
    hmr: { overlay: false },
    proxy: {
      '/api': {
        target: 'http://localhost:5001',  // your Flask backend (main.py uses port 5001)
        changeOrigin: true,
      },
      '/static': {
        target: 'http://localhost:5001',
        changeOrigin: true,
      },
    },
  },
  plugins: [vue()],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
});
