import algorithmClient from './algorithmClient'

export interface AlgorithmResponse<T = unknown> {
  code: number
  message: string
  data: T | null
  ok: boolean
  timestamp?: number
  requestId?: string
  success: boolean
  error: string | null
}

export interface AlgorithmHealth {
  status: string
  version: string
  service: string
}

export function runDiffusionSimulation(payload: Record<string, unknown>) {
  return algorithmClient.post<any, AlgorithmResponse>('/api/diffusion/simulate', payload)
}

export function runPinnCoarseSearch(payload: Record<string, unknown>) {
  return algorithmClient.post<any, AlgorithmResponse>('/api/inversion/coarse-search', payload)
}

export function runPinnInversion(payload: Record<string, unknown>) {
  return algorithmClient.post<any, AlgorithmResponse>('/api/inversion/solve', payload)
}

export function runEvacuationPlanning(payload: Record<string, unknown>) {
  return algorithmClient.post<any, AlgorithmResponse>('/api/planning/evacuation', payload)
}

export function runEngineTask(taskType: string, payload: Record<string, unknown>) {
  return algorithmClient.post<any, AlgorithmResponse>('/api/engine/run', { task_type: taskType, payload })
}

export function getGasTypes() {
  return algorithmClient.get<any, AlgorithmResponse>('/api/gas-types')
}

export function checkAlgorithmHealth() {
  return algorithmClient.get<any, AlgorithmResponse<AlgorithmHealth>>('/api/health')
}
