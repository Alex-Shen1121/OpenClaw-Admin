import { readFileSync } from 'fs'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import { defineConfig, loadEnv } from 'vite'

const packageJson = JSON.parse(
  readFileSync(new URL('./package.json', import.meta.url), 'utf-8'),
) as { version?: string }

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const appVersion = packageJson.version || ''
  
  const backendPort = env.PORT || '3000'
  const frontendPort = env.DEV_PORT || '3001'
  const isDev = mode === 'development'
  
  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src'),
      },
    },
    server: {
      host: '0.0.0.0',
      port: parseInt(String(frontendPort)),
      allowedHosts: true,
      proxy: {
        '/api': {
          target: `http://localhost:${backendPort}`,
          changeOrigin: true,
        },
      },
    },
    build: {
      target: 'esnext',
      outDir: 'dist',
      sourcemap: !isDev,
      rollupOptions: {
        output: {
          manualChunks: {
            'vue-vendor': ['vue', 'vue-router', 'pinia'],
            'ui-vendor': ['naive-ui', '@vicons/ionicons5'],
            'utils-vendor': ['vue-i18n', 'markdown-it', 'highlight.js', 'katex'],
          },
        },
      },
      chunkSizeWarningLimit: 1000,
    },
    esbuild: {
      drop: isDev ? [] : ['console', 'debugger'],
      pure: isDev ? [] : ['console.log', 'console.info', 'console.warn', 'console.debug'],
    },
    define: {
      'import.meta.env.VITE_APP_TITLE': JSON.stringify(env.VITE_APP_TITLE || 'OpenClaw Web'),
      'import.meta.env.VITE_APP_VERSION': JSON.stringify(appVersion),
      __VUE_OPTIONS_API__: false,
      __VUE_PROD_DEVTOOLS__: false,
    },
    optimizeDeps: {
      include: ['vue', 'vue-router', 'pinia', 'naive-ui', 'vue-i18n'],
    },
  }
})
