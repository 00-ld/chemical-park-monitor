// https://vitejs.dev/config/
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
//引入svg需要用到插件
import { createSvgIconsPlugin } from 'vite-plugin-svg-icons'
export default defineConfig(({ mode }) => {
  //获取各种环境下的对应的变量
  const env = loadEnv(mode, process.cwd())
  const appBaseApi = env.VITE_APP_BASE_API || '/api'
  const appServer = env.VITE_SERVE || 'http://localhost:8081'
  const algorithmBaseApi = env.VITE_ALGORITHM_BASE_API || '/algorithm-api'
  const algorithmServer = env.VITE_ALGORITHM_SERVE || 'http://localhost:8000'

  return {
    plugins: [
      vue(),
      createSvgIconsPlugin({
        iconDirs: [path.resolve(process.cwd(), 'src/assets/icons')],
        symbolId: 'icon-[dir]-[name]',
      }),
    ],
    resolve: {
      alias: {
        "@": path.resolve("./src") // 相对路径别名配置，使用 @ 代替 src
      }
    },
    //scss全局变量一个配置
    css: {
      preprocessorOptions: {
        scss: {
          javascriptEnabled: true,
          additionalData: '@import "./src/styles/variable.scss";',
        },
      },
    },
    //代理跨域
    server: {
      proxy: {
        [appBaseApi]: {
          //Java后端服务器地址
          target: appServer,
          changeOrigin: true,
        },
        [algorithmBaseApi]: {
          //Python算法服务器地址
          target: algorithmServer,
          changeOrigin: true,
          rewrite: (path: string) => path.replace(algorithmBaseApi, ''),
        },
      }
    }
  }
})
