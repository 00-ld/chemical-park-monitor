import axios from 'axios'
import { ElMessage } from 'element-plus'
import useUserStore from '@/store/modules/user'
import { GET_TOKEN, REMOVE_TOKEN } from '@/utils/token'
import router from '@/router'

const request = axios.create({
  baseURL: import.meta.env.VITE_APP_BASE_API || '/api',
  timeout: 5000,
})

request.interceptors.request.use((config) => {
  const userStore = useUserStore()
  const token = userStore.token || GET_TOKEN()
  if (token) {
    config.headers.token = token
  }
  return config
})

request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    let message = ''
    const status = error.response?.status
    const url: string = error.config?.url || ''
    const isAuthEntry = /\/(login|register)\b/.test(url)

    switch (status) {
      case 401:
        if (isAuthEntry) {
          message = error.response?.data?.message || '用户名或密码错误'
        } else {
          message = '登录已过期，请重新登录'
          REMOVE_TOKEN()
          try {
            useUserStore().logout()
          } catch {
            // Pinia 尚未初始化时忽略清理错误。
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
        message = error.response?.data?.message || '服务器错误'
        break
      default:
        message = error.response?.data?.message || '网络连接异常，请检查后端服务是否已启动'
        break
    }

    ElMessage({
      type: 'error',
      message,
    })
    return Promise.reject(error)
  },
)

export default request
