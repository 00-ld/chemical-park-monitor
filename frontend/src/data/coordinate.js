export const MAP_METERS_PER_UNIT = 0.5

export const GEO_REFERENCE = {
  originLongitude: 118.78,
  originLatitude: 32.04,
  baseAltitude: 18,
}

export function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max)
}

export function worldToGeo(wx, wy) {
  const metersX = wx * MAP_METERS_PER_UNIT
  const metersY = wy * MAP_METERS_PER_UNIT
  const latitude = GEO_REFERENCE.originLatitude - metersY / 111320
  const longitude = GEO_REFERENCE.originLongitude
    + metersX / (111320 * Math.cos(GEO_REFERENCE.originLatitude * Math.PI / 180))
  const normalizedY = clamp(wy, 0, 650)
  const altitude = GEO_REFERENCE.baseAltitude
    + (650 - normalizedY) * 0.02
    + Math.sin(wx / 90) * 1.8
    + Math.cos(wy / 70) * 1.2

  return {
    longitude,
    latitude,
    altitude,
  }
}

export function geoToWorld(longitude, latitude) {
  const metersX = (longitude - GEO_REFERENCE.originLongitude)
    * (111320 * Math.cos(GEO_REFERENCE.originLatitude * Math.PI / 180))
  const metersY = (GEO_REFERENCE.originLatitude - latitude) * 111320
  return {
    x: metersX / MAP_METERS_PER_UNIT,
    y: metersY / MAP_METERS_PER_UNIT,
  }
}

export function formatGeoCoord(wx, wy) {
  const geo = worldToGeo(wx, wy)
  return {
    longitude: `${geo.longitude.toFixed(3)}°E`,
    latitude: `${geo.latitude.toFixed(3)}°N`,
    altitude: `${geo.altitude.toFixed(1)}m`,
  }
}
