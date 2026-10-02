import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // 5180, not the 5173 default: QuantPa's vite preview also grabs 5173.
    port: 5180,
    strictPort: true,
    proxy: {
      // Fastwork's API sends no CORS headers, so proxy it in dev.
      '/api': {
        target: 'https://jobboard-api.fastwork.co',
        changeOrigin: true,
      },
    },
  },
})
