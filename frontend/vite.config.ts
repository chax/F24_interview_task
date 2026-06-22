import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Defaults to the backend reachable from the host (plain `npm run dev`, or a
// backend container with its port published to the host). When the frontend
// itself runs in a container alongside the backend, override this with the
// backend container's name on their shared network, e.g.
// `BACKEND_URL=http://f24-backend:8000`.
const backendUrl = process.env.BACKEND_URL ?? 'http://127.0.0.1:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: backendUrl,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
  // vite preview falls back to server.proxy automatically when this isn't set,
  // so the same /api proxy works for the production build too.
})
