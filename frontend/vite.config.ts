import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Le front appelle /api en relatif : le navigateur reste sur une
    // seule origine, ce qui evite les questions de CORS et de cookies
    // pendant le developpement.
    proxy: {
      '/api': {
        // Port du serveur Django. Configurable, parce que 8000 est
        // souvent deja pris par un autre projet sur le poste.
        target: process.env.VITE_API_URL ?? 'http://127.0.0.1:8140',
        changeOrigin: true,
      },
    },
  },
})
