import algorithmClient from './algorithmClient'

/** 统一算法 API 响应格式 */
export interface AlgorithmResponse<T = unknown> {
  success: boolean
  data: T | null
  error: string | null
  code: number
}

/**
 * 运行扩散模拟
 * POST /api/diffusion/simulate
 */
export function runDiffusionSimulation(payload: Record<string, unknown>) {
  return algorithmClient.post<any, AlgorithmResponse>('/api/diffusion/simulate', payload)
}

/**
 * PINN 粗搜索
 * POST /api/inversion/coarse-search
 */
export function runPinnCoarseSearch(payload: Record<string, unknown>) {
  return algorithmClient.post<any, AlgorithmResponse>('/api/inversion/coarse-search', payload)
}

/**
 * PINN 反演求解
 * POST /api/inversion/solve
 */
export function runPinnInversion(payload: Record<string, unknown>) {
  return algorithmClient.post<any, AlgorithmResponse>('/api/inversion/solve', payload)
}

/**
 * 疏散路径规划
 * POST /api/planning/evacuation
 */
export function runEvacuationPlanning(payload: Record<string, unknown>) {
  return algorithmClient.post<any, AlgorithmResponse>('/api/planning/evacuation', payload)
}

/**
 * 算法引擎统一入口
 * POST /api/engine/run
 */
export function runEngineTask(taskType: string, payload: Record<string, unknown>) {
  return algorithmClient.post<any, AlgorithmResponse>('/api/engine/run', { task_type: taskType, payload })
}

/**
 * 获取气体类型信息
 * GET /api/gas-types
 */
export function getGasTypes() {
  return algorithmClient.get<any, AlgorithmResponse>('/api/gas-types')
}

/**
 * 检测算法服务健康状态
 * GET /api/health
 */
export function checkAlgorithmHealth() {
  return algorithmClient.get<any, { status: string; version: string; service: string }>('/api/health')
}
