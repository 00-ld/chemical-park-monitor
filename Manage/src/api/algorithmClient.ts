import axios from 'axios'
import type { AlgorithmResponse } from './algorithm'

const algorithmClient = axios.create({
  baseURL: import.meta.env.VITE_ALGORITHM_BASE_API || '/algorithm-api',
  timeout: 30000,
})

algorithmClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.status === 0
      ? '算法服务连接失败'
      : error.response?.data?.error || '算法服务请求异常'
    return { success: false, data: null, error: message, code: error.response?.status || 500 } as AlgorithmResponse
  },
)

export default algorithmClient
