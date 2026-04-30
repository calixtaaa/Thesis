import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { ViteImageOptimizer } from 'vite-plugin-image-optimizer'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    ViteImageOptimizer({
      png: { quality: 80 },
      jpeg: { quality: 80 },
      jpg: { quality: 80 },
      webp: { quality: 80 },
      avif: { quality: 55 },
    }),
  ],
  build: {
    chunkSizeWarningLimit: 1200,
    // keep warning threshold, but split heavy deps into separate chunks
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id) return
          if (id.includes('node_modules')) {
            if (id.includes('exceljs')) return 'reports-exceljs'
            if (id.includes('/xlsx/') || id.includes('\\xlsx\\')) return 'reports-xlsx'
            if (id.includes('chart.js')) return 'charts'
            if (id.includes('@supabase/supabase-js')) return 'supabase'
            if (id.includes('vue-router')) return 'vue'
            if (id.includes('/vue/')) return 'vue'
            return 'vendor'
          }
        },
      },
    },
  },
})
