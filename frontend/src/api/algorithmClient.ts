import axios from 'axios'
import type { AlgorithmResponse } from './algorithm'

const algorithmClient = axios.create({
  baseURL: import.meta.env.VITE_ALGORITHM_BASE_API || '/algorithm-api',
  timeout: 30000,
})

algorithmClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const responseBody = error.response?.data
    const message = error.response?.status === 0
      ? '算法服务连接失败'
      : responseBody?.message || responseBody?.error || '算法服务请求异常'

    return {
      code: error.response?.status || 500,
      message,
      data: null,
      ok: false,
      timestamp: Date.now(),
      requestId: responseBody?.requestId,
      success: false,
      error: message,
    } as AlgorithmResponse
  },
)

export default algorithmClient
