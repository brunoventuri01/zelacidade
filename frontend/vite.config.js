import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Em desenvolvimento, `npm run dev` repassa /api para o FastAPI em localhost:8000.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
  test: {
    environment: 'node',
  },
});
