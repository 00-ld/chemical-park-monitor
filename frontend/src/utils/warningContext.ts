import type { LocationQuery, LocationQueryRaw } from 'vue-router'

export interface WarningContext {
  warningId?: string
  carId?: string
  areaName?: string
  gasType?: string
  gasValue?: string
  x?: string
  y?: string
  source?: string
  monitorId?: string
}

const STORAGE_KEY = 'park_warning_context'

const queryText = (value: LocationQuery[string] | undefined) => {
  if (Array.isArray(value)) return String(value[0] ?? '')
  return String(value ?? '')
}

const cleanContext = (context: WarningContext): WarningContext | null => {
  const cleaned = Object.fromEntries(
    Object.entries(context).filter(([, value]) => value !== undefined && value !== ''),
  ) as WarningContext
  return cleaned.warningId || cleaned.carId ? cleaned : null
}

export const normalizeGasType = (gasType: string | null | undefined) => {
  const raw = String(gasType || '').trim().toUpperCase()
  if (!raw) return ''
  if (raw.includes('CO') || raw.includes('一氧化碳')) return 'CO'
  if (raw.includes('O2') || raw.includes('O₂') || raw.includes('氧气')) return 'O2'
  if (raw.includes('NH3') || raw.includes('NH₃') || raw.includes('氨')) return 'NH3'
  if (raw.includes('CH4') || raw.includes('CH₄') || raw.includes('甲烷') || raw.includes('可燃')) return 'CH4'
  return raw
}

export const formatGasType = (gasType: string | null | undefined) => {
  const gasMap: Record<string, string> = {
    CH4: '甲烷(CH₄)',
    NH3: '氨气(NH₃)',
    CO: '一氧化碳(CO)',
    O2: '氧气(O₂)',
  }
  const normalized = normalizeGasType(gasType)
  return gasMap[normalized] || String(gasType || '--')
}

export const getWarningContextFromQuery = (query: LocationQuery): WarningContext | null => {
  return cleanContext({
    warningId: queryText(query.warningId),
    carId: queryText(query.carId),
    areaName: queryText(query.areaName),
    gasType: queryText(query.gasType),
    gasValue: queryText(query.gasValue),
    x: queryText(query.x),
    y: queryText(query.y),
    source: queryText(query.source),
    monitorId: queryText(query.monitorId),
  })
}

export const saveWarningContext = (context: WarningContext | null) => {
  const cleaned = context ? cleanContext(context) : null
  if (!cleaned) return null
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(cleaned))
  return cleaned
}

export const loadWarningContext = (): WarningContext | null => {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    return raw ? cleanContext(JSON.parse(raw)) : null
  } catch (error) {
    console.warn('读取预警联动上下文失败:', error)
    return null
  }
}

export const clearWarningContext = () => {
  sessionStorage.removeItem(STORAGE_KEY)
}

export const getCurrentWarningContext = (query: LocationQuery) => {
  const fromQuery = getWarningContextFromQuery(query)
  return fromQuery ? saveWarningContext(fromQuery) : loadWarningContext()
}

export const buildWarningQuery = (
  item: {
    id?: number | string
    carId?: number | string
    areaName?: string
    gasType?: string
    gasValue?: number | string
    x?: number | string
    y?: number | string
  },
  source: string,
  extra: WarningContext = {},
): LocationQueryRaw => {
  const context = saveWarningContext({
    warningId: String(item.id ?? ''),
    carId: String(item.carId ?? ''),
    areaName: String(item.areaName ?? ''),
    gasType: formatGasType(item.gasType),
    gasValue: String(item.gasValue ?? ''),
    x: String(item.x ?? ''),
    y: String(item.y ?? ''),
    source,
    monitorId: String(item.carId ?? ''),
    ...extra,
  })

  return { ...(context || {}) }
}

export const withWarningQuery = (
  query: LocationQueryRaw = {},
  context: WarningContext | null,
  source?: string,
): LocationQueryRaw => {
  if (!context) return query
  const saved = saveWarningContext({
    ...context,
    source: source || context.source,
  })
  return {
    ...(saved || {}),
    ...query,
  }
}
