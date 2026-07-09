import { fileURLToPath, URL } from 'node:url'
import path from 'node:path'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { createSvgIconsPlugin } from 'vite-plugin-svg-icons'

export default defineConfig(({ mode }) => {
  // 必须从 loadEnv 读取；process.env.VITE_* 在 vite.config 里默认是空的
  const env = loadEnv(mode, process.cwd(), '')
  const proxyTarget =
    env.VITE_API_TARGET || 'http://127.0.0.1:18083'
  const isLocalGateway =
    proxyTarget.includes('18083') || env.VITE_API_MODE === 'django'

  return {
  plugins: [
    vue(),
    createSvgIconsPlugin({
      iconDirs: [path.resolve(__dirname, 'src/icons/svg')],
      symbolId: 'icon-[name]',
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
    extensions: ['.vue', '.js', '.ts', '.json'],
  },
  css: {
    preprocessorOptions: {
      scss: {
        silenceDeprecations: ['import'],
      },
    },
  },
  server: {
    port: 9530,
    host: '0.0.0.0',
    hmr: true,
    proxy: {
      '/api': {
        target: proxyTarget,
        changeOrigin: true,
        pathRewrite: isLocalGateway ? { '^/api': '/api' } : { '^/api': '' },
      },
    },
  },
  }
})
