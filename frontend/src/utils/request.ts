//进行axios二次封装:使用请求与响应拦截器
import axios from 'axios'
import { ElMessage } from 'element-plus'
// 引入用户仓库
import useUserStore from '@/store/modules/user'
// 引入 token 工具作为兜底数据源（与 store 同一 key 'TOKEN'）
import { GET_TOKEN, REMOVE_TOKEN } from '@/utils/token'
import router from '@/router'

//第一步:利用axios对象的create方法,去创建axios实例(其他的配置:基础路径、超时的时间)
const request = axios.create({
  // 开发环境使用代理，生产环境直接连接后端
  baseURL: import.meta.env.VITE_APP_BASE_API || '/api',
  timeout: 5000,
})
//第二步:request实例添加请求与响应拦截器
request.interceptors.request.use((config) => {
  // 获取用户仓库实例
  const userStore = useUserStore()
  // 优先取 store 内存中的 token，刷新后 store 已为空时回退到本地存储
  const token = userStore.token || GET_TOKEN()
  if (token) {
    config.headers.token = token
  }
  // 返回配置对象
  return config
})

//第三步:响应拦截器
request.interceptors.response.use(
  (response) => {
    //成功回调
    //简化数据
    return response.data
  },
  (error) => {
    //失败回调:处理http网络错误的
    //定义一个变量:存储网络错误信息
    let message = ''
    //http状态码（error.response 可能不存在，如超时/断网）
    const status = error.response?.status
    // 请求地址：登录/注册等鉴权入口返回 401 表示「凭证错误」，而非 token 过期
    const url: string = error.config?.url || ''
    const isAuthEntry = /\/(login|register)\b/.test(url)
    switch (status) {
      case 401:
        if (isAuthEntry) {
          // 登录/注册失败：直接透传后端的真实提示，不清登录态、不跳转
          message = error.response?.data?.message || '用户名或密码错误'
        } else {
          message = 'TOKEN过期，请重新登录'
          // 清除失效登录态并跳转登录页
          REMOVE_TOKEN()
          try {
            useUserStore().logout()
          } catch (e) {
            // store 未初始化时忽略
          }
          if (router.currentRoute.value.path !== '/login') {
            router.push({
              path: '/login',
              query: { redirect: router.currentRoute.value.fullPath },
            })
          }
        }
        break
      case 403:
        message = '无权访问'
        break
      case 404:
        message = '请求地址错误'
        break
      case 500:
        message = '服务器出现问题'
        break
      default:
        message = '网络出现问题'
        break
    }
    //提示错误信息
    ElMessage({
      type: 'error',
      message,
    })
    return Promise.reject(error)
  },
)
//对外暴露
export default request