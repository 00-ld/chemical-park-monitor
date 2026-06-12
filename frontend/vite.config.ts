// https://vitejs.dev/config/
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
//引入svg需要用到插件
import { createSvgIconsPlugin } from 'vite-plugin-svg-icons'
//mock插件提供方法
import { viteMockServe } from 'vite-plugin-mock'
export default defineConfig(({ command, mode }) => {
  //获取各种环境下的对应的变量
  let env = loadEnv(mode, process.cwd());
  return {
    publicPath: 'https://gitee.com/jch1011/guiguzhenxuan',
    plugins: [vue(),
    createSvgIconsPlugin({
      iconDirs: [path.resolve(process.cwd(), 'src/assets/icons')],
      symbolId: 'icon-[dir]-[name]',
    }),
      // viteMockServe({
      //   localEnabled: command === 'serve',//保证开发阶段可以使用mock接口
      // })
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
        [env.VITE_APP_BASE_API]: {
          //Java后端服务器地址
          target: env.VITE_SERVE,
          changeOrigin: true,
        },
        [env.VITE_ALGORITHM_BASE_API || '/algorithm-api']: {
          //Python算法服务器地址
          target: env.VITE_ALGORITHM_SERVE,
          changeOrigin: true,
          rewrite: (path: string) => path.replace(/^\/algorithm-api/, ''),
        },
      }
    }
  }
})
