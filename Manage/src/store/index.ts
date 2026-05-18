import { createPinia } from 'pinia'
import type { App } from 'vue'
//创建大仓库
const pinia = createPinia()
//封装函数:让组件引入仓库仓库实例对象
export const setupStore = (app: App<Element>) => {
  app.use(pinia)
}
export default pinia