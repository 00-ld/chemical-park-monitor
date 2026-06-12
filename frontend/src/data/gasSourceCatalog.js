const MAP_METERS_PER_UNIT = 0.5

export const GAS_SOURCE_CATALOG = [
  {
    gasId: 'co',
    gasName: '一氧化碳',
    validRadiusMeters: 36,
    allowedSourceFacilityIds: ['b23', 'b07'],
    description: '允许位于一氧化碳钢瓶库及相关工艺区附近',
  },
  {
    gasId: 'h2s',
    gasName: '硫化氢',
    validRadiusMeters: 38,
    allowedSourceFacilityIds: ['t08', 'tw05'],
    description: '允许位于硫化氢储罐和脱硫塔相关区域附近',
  },
  {
    gasId: 'ch4',
    gasName: '甲烷',
    validRadiusMeters: 40,
    allowedSourceFacilityIds: ['b20', 'b09'],
    description: '允许位于甲烷储配库及配料区域附近',
  },
  {
    gasId: 'o2',
    gasName: '氧气',
    validRadiusMeters: 30,
    allowedSourceFacilityIds: ['b18'],
    description: '允许位于氧气制备站附近',
  },
]

export function getGasSourceConfig(gasId) {
  return GAS_SOURCE_CATALOG.find(item => item.gasId === gasId) || null
}

export function getAllowedGasSourceFacilityIds(gasId) {
  return getGasSourceConfig(gasId)?.allowedSourceFacilityIds || []
}

export function getAllowedGasSourceFacilities(facilities, gasId) {
  const allowedIds = new Set(getAllowedGasSourceFacilityIds(gasId))
  return facilities.filter(facility => allowedIds.has(facility.id))
}

export function findNearestAllowedGasSourceFacility(facilities, gasId, mapPoint) {
  if (!mapPoint) return null
  const allowedFacilities = getAllowedGasSourceFacilities(facilities, gasId)
  if (!allowedFacilities.length) return null
  return findNearestAllowedFacility(mapPoint, allowedFacilities)
}

export function validateGasLeakSource({
  gasId,
  sourceFacilityId,
  facilities,
  mapPoint,
}) {
  const config = getGasSourceConfig(gasId)
  if (!config) {
    return {
      valid: false,
      reasonCode: 'missing_catalog',
      gasId,
      config: null,
      selectedFacility: null,
      allowedFacilities: [],
      nearestAllowedFacility: null,
      distanceToNearestAllowedMeters: null,
      message: '当前气体尚未配置允许的泄漏源范围',
    }
  }

  const selectedFacility = facilities.find(item => item.id === sourceFacilityId) || null
  const allowedFacilities = getAllowedGasSourceFacilities(facilities, gasId)
  if (!selectedFacility) {
    return {
      valid: false,
      reasonCode: 'missing_source',
      gasId,
      config,
      selectedFacility: null,
      allowedFacilities,
      nearestAllowedFacility: null,
      distanceToNearestAllowedMeters: null,
      message: '请先选择一个泄漏源设施',
    }
  }

  if (!allowedFacilities.length) {
    return {
      valid: false,
      reasonCode: 'missing_allowed_facilities',
      gasId,
      config,
      selectedFacility,
      allowedFacilities: [],
      nearestAllowedFacility: null,
      distanceToNearestAllowedMeters: null,
      message: `${config.gasName} 暂未配置合法泄漏设施`,
    }
  }

  const selectedPoint = mapPoint || getFacilityCenter(selectedFacility)
  const nearest = findNearestAllowedFacility(selectedPoint, allowedFacilities)
  const isDirectlyAllowed = config.allowedSourceFacilityIds.includes(selectedFacility.id)
  const isWithinRadius = nearest && nearest.distanceMeters <= config.validRadiusMeters
  const valid = Boolean(isDirectlyAllowed || isWithinRadius)

  if (valid) {
    return {
      valid: true,
      reasonCode: isDirectlyAllowed ? 'allowed_facility' : 'within_radius',
      gasId,
      config,
      selectedFacility,
      allowedFacilities,
      nearestAllowedFacility: nearest?.facility || null,
      distanceToNearestAllowedMeters: nearest ? round2(nearest.distanceMeters) : 0,
      message: `${config.gasName} 泄漏源校验通过`,
    }
  }

  const nearestLabel = nearest?.facility?.name || '允许区域'
  const distanceLabel = nearest ? `${round2(nearest.distanceMeters)}m` : '--'
  return {
    valid: false,
    reasonCode: 'out_of_range',
    gasId,
    config,
    selectedFacility,
    allowedFacilities,
    nearestAllowedFacility: nearest?.facility || null,
    distanceToNearestAllowedMeters: nearest ? round2(nearest.distanceMeters) : null,
    message: `当前泄漏点不在 ${config.gasName} 允许的生产/存储区域附近，最近允许设施为 ${nearestLabel}（${distanceLabel}）`,
  }
}

function findNearestAllowedFacility(point, facilities) {
  let nearest = null
  for (const facility of facilities) {
    const center = getFacilityCenter(facility)
    const distanceMeters = Math.hypot(point.x - center.x, point.y - center.y) * MAP_METERS_PER_UNIT
    if (!nearest || distanceMeters < nearest.distanceMeters) {
      nearest = {
        facility,
        distanceMeters,
      }
    }
  }
  return nearest
}

function getFacilityCenter(facility) {
  if (facility.type === 'tank' || facility.type === 'tower') {
    return { x: facility.x, y: facility.y }
  }
  return {
    x: facility.x + (facility.w || 0) / 2,
    y: facility.y + (facility.h || 0) / 2,
  }
}

function round2(value) {
  return Number(value.toFixed(2))
}
