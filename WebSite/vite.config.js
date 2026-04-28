import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  build: {
    // keep warning threshold, but split heavy deps into separate chunks
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id) return
          if (id.includes('node_modules')) {
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
