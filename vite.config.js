import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      // @layui/layer-vue 的 exports 未声明 ./lib/index.css，直接子路径导入在 Vite 下会解析失败
      '@layui/layer-vue/lib/index.css': fileURLToPath(
        new URL('./node_modules/@layui/layer-vue/lib/index.css', import.meta.url)
      ),
    },
  },
  publicDir: 'public',
  server: {
    port: 3000,
    open: true,
    host: true,
    proxy: {
      // 仅开发环境使用：把 /api 转发给本地 Flask，浏览器侧始终同源，因此不涉及跨域。
      // 前端代码里的 baseURL 固定为相对路径 /api，生产环境由部署平台转发（见 public/_redirects）。
      '/api': {
        // 用 127.0.0.1 而非 localhost：Windows 下 localhost 可能优先解析到 IPv6 的 ::1，
        // 而 Flask 监听的是 IPv4，会导致代理连接被拒。
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
        // 无需 rewrite：/api 前缀是后端接口本身的一部分，原样转发即可
      },
    },
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    // Vite 8 已改用 oxc 做压缩，内置 esbuild 压缩入口需要额外安装 esbuild
    minify: 'oxc',
    cssCodeSplit: true,
    rollupOptions: {
      output: {
        // Vite 8 (rolldown) 要求 manualChunks 为函数形式，旧的对象写法会报错
        manualChunks: (id) => {
          if (id.includes('node_modules/vue') || id.includes('node_modules/vue-router')) {
            return 'vue-vendor'
          }
        },
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name.split('.')
          const ext = info[info.length - 1]
          if (/\.(png|jpe?g|gif|svg|webp|ico)$/.test(assetInfo.name)) {
            return `assets/images/[name]-[hash].${ext}`
          }
          if (/\.(woff2?|eot|ttf|otf)$/.test(assetInfo.name)) {
            return `assets/fonts/[name]-[hash].${ext}`
          }
          if (/\.css$/.test(assetInfo.name)) {
            return `assets/css/[name]-[hash].${ext}`
          }
          return `assets/[name]-[hash].${ext}`
        },
      },
    },
  },
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: `@use "@/styles/variables.scss" as *;`,
      },
    },
  },
})