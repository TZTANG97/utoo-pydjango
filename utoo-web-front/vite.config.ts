import { fileURLToPath, URL } from 'node:url'
import path from 'node:path'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { createSvgIconsPlugin } from 'vite-plugin-svg-icons'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const proxyTarget = env.VITE_API_TARGET || 'http://127.0.0.1:18083'
  const isLocalGateway =
    proxyTarget.includes('18083') || env.VITE_API_MODE === 'django'

  return {
    plugins: [
      vue(),
      createSvgIconsPlugin({
        iconDirs: [path.resolve(__dirname, 'src/client/icons/svg')],
        symbolId: 'icon-[name]',
      }),
    ],
    resolve: {
      alias: {
        '@client': fileURLToPath(new URL('./src/client', import.meta.url)),
        '@admin': fileURLToPath(new URL('./src/admin', import.meta.url)),
        '@shared': fileURLToPath(new URL('./src/shared', import.meta.url)),
        // 兼容少数未替换完的 @/ 引用：默认指向 client（迁移脚本会尽量改成 @client/@admin）
        '@': fileURLToPath(new URL('./src/client', import.meta.url)),
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
          rewrite: isLocalGateway
            ? (p) => p
            : (p) => p.replace(/^\/api/, ''),
        },
      },
    },
  }
})
