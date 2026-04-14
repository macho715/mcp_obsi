import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (
            id.includes('react-cytoscapejs') ||
            id.includes(`${String.raw`node_modules/cytoscape`}`) ||
            id.includes(`${String.raw`node_modules\\cytoscape`}`)
          ) {
            return 'graph-vendor'
          }
        },
      },
    },
  },
})
