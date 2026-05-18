export interface Point {
  x: number
  y: number
}

export interface Obstacle {
  x: number
  y: number
  width: number
  height: number
  name?: string
}

export interface Road {
  id: number
  x1: number
  y1: number
  x2: number
  y2: number
  width: number
  type: 'main' | 'secondary' | 'path'
  name?: string
}

export interface RoadSegment {
  id: string
  startPoint: Point
  endPoint: Point
  length: number
  roadId: number
  type: 'main' | 'secondary' | 'path'
}

export interface Intersection {
  id: string
  point: Point
  connectedSegments: string[]
  type: 'cross' | 't-junction' | 'corner'
}

export interface RoadNetwork {
  segments: RoadSegment[]
  intersections: Intersection[]
  nodes: Map<string, NetworkNode>
  totalLength: number
  boundingBox: { minX: number; minY: number; maxX: number; maxY: number }
}

export interface PathPlanningOptions {
  startPoint: Point
  endPoint: Point
  obstacles: Obstacle[]
  roads: Road[]
  windDirection: number
  windSpeed: number
  gridSize: number
}

export interface PathResult {
  path: Point[]
  distance: number
  estimatedTime: number
  riskLevel: 'low' | 'medium' | 'high'
  buildingName?: string
  roadSegments: RoadSegment[]
  pathDetails: PathDetail[]
}

export interface PathDetail {
  segmentIndex: number
  startPoint: Point
  endPoint: Point
  distance: number
  roadType: 'main' | 'secondary' | 'path'
  roadName?: string
}

export interface NetworkNode {
  id: string
  point: Point
  neighbors: Map<string, { distance: number; segmentId: string }>
  segmentIds: string[]
}

interface GraphNode {
  id: string
  x: number
  y: number
  edges: GraphEdge[]
}

interface GraphEdge {
  toNodeId: string
  distance: number
  segmentId: string
  roadType: 'main' | 'secondary' | 'path'
  roadName?: string
}

export class RoadNetworkAnalyzer {
  analyze(roads: Road[]): RoadNetwork {
    const segments = this.buildSegments(roads)
    const nodes = this.buildNodes(segments)
    const intersections = this.findIntersections(nodes)
    const boundingBox = this.calculateBoundingBox(segments)
    const totalLength = segments.reduce((sum, s) => sum + s.length, 0)

    return {
      segments,
      intersections,
      nodes,
      totalLength,
      boundingBox
    }
  }

  private buildSegments(roads: Road[]): RoadSegment[] {
    const segments: RoadSegment[] = []
    let segId = 0

    for (const road of roads) {
      segments.push({
        id: `seg_${segId++}`,
        startPoint: { x: road.x1, y: road.y1 },
        endPoint: { x: road.x2, y: road.y2 },
        length: Math.sqrt(Math.pow(road.x2 - road.x1, 2) + Math.pow(road.y2 - road.y1, 2)),
        roadId: road.id,
        type: road.type || 'main'
      })
    }

    return segments
  }

  private buildNodes(segments: RoadSegment[]): Map<string, NetworkNode> {
    const nodes = new Map<string, NetworkNode>()

    for (const seg of segments) {
      const startKey = this.nodeKey(seg.startPoint)
      const endKey = this.nodeKey(seg.endPoint)

      if (!nodes.has(startKey)) {
        nodes.set(startKey, {
          id: startKey,
          point: seg.startPoint,
          neighbors: new Map(),
          segmentIds: [seg.id]
        })
      } else {
        nodes.get(startKey)!.segmentIds.push(seg.id)
      }

      if (!nodes.has(endKey)) {
        nodes.set(endKey, {
          id: endKey,
          point: seg.endPoint,
          neighbors: new Map(),
          segmentIds: [seg.id]
        })
      } else {
        nodes.get(endKey)!.segmentIds.push(seg.id)
      }

      nodes.get(startKey)!.neighbors.set(endKey, { distance: seg.length, segmentId: seg.id })
      nodes.get(endKey)!.neighbors.set(startKey, { distance: seg.length, segmentId: seg.id })
    }

    return nodes
  }

  private findIntersections(nodes: Map<string, NetworkNode>): Intersection[] {
    const intersections: Intersection[] = []
    let intId = 0

    for (const node of nodes.values()) {
      if (node.segmentIds.length >= 2) {
        let type: 'cross' | 't-junction' | 'corner' = 'corner'
        if (node.segmentIds.length >= 4) type = 'cross'
        else if (node.segmentIds.length === 3) type = 't-junction'

        intersections.push({
          id: `int_${intId++}`,
          point: node.point,
          connectedSegments: node.segmentIds,
          type
        })
      }
    }

    return intersections
  }

  private calculateBoundingBox(segments: RoadSegment[]) {
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
    for (const seg of segments) {
      minX = Math.min(minX, seg.startPoint.x, seg.endPoint.x)
      minY = Math.min(minY, seg.startPoint.y, seg.endPoint.y)
      maxX = Math.max(maxX, seg.startPoint.x, seg.endPoint.x)
      maxY = Math.max(maxY, seg.startPoint.y, seg.endPoint.y)
    }
    return { minX, minY, maxX, maxY }
  }

  private nodeKey(p: Point): string {
    return `${Math.round(p.x)},${Math.round(p.y)}`
  }
}

export class PathPlanner {
  private obstacles: Obstacle[] = []
  private roads: Road[] = []
  private windDirection: number = 90
  private windSpeed: number = 5
  private graphNodes: Map<string, GraphNode> = new Map()
  private segments: RoadSegment[] = []
  private network: RoadNetwork | null = null
  private networkAnalyzer: RoadNetworkAnalyzer

  constructor(options: Partial<PathPlanningOptions> = {}) {
    this.networkAnalyzer = new RoadNetworkAnalyzer()
    if (options.roads && options.roads.length > 0) {
      this.roads = options.roads
      this.buildGraph()
    }
    if (options.obstacles) this.obstacles = options.obstacles
    if (options.windDirection !== undefined) this.windDirection = options.windDirection
    if (options.windSpeed !== undefined) this.windSpeed = options.windSpeed
  }

  private buildGraph(): void {
    this.graphNodes.clear()
    this.segments = []

    const allPoints: Map<string, Point> = new Map()
    const roadSegments: { road: Road; points: Point[] }[] = []

    for (const road of this.roads) {
      const startKey = this.pointKey(road.x1, road.y1)
      const endKey = this.pointKey(road.x2, road.y2)
      allPoints.set(startKey, { x: road.x1, y: road.y1 })
      allPoints.set(endKey, { x: road.x2, y: road.y2 })
      roadSegments.push({
        road,
        points: [{ x: road.x1, y: road.y1 }, { x: road.x2, y: road.y2 }]
      })
    }

    for (let i = 0; i < this.roads.length; i++) {
      const road1 = this.roads[i]
      for (let j = i + 1; j < this.roads.length; j++) {
        const road2 = this.roads[j]
        const intersection = this.lineIntersection(
          road1.x1, road1.y1, road1.x2, road1.y2,
          road2.x1, road2.y1, road2.x2, road2.y2
        )
        if (intersection) {
          const key = this.pointKey(intersection.x, intersection.y)
          allPoints.set(key, intersection)
          roadSegments[i].points.push(intersection)
          roadSegments[j].points.push(intersection)
        }
      }
    }

    for (const point of allPoints.values()) {
      const key = this.pointKey(point.x, point.y)
      if (!this.graphNodes.has(key)) {
        this.graphNodes.set(key, {
          id: key,
          x: point.x,
          y: point.y,
          edges: []
        })
      }
    }

    let segId = 0
    for (const { road, points } of roadSegments) {
      points.sort((a, b) => {
        const tA = this.paramOnLine(a, road.x1, road.y1, road.x2, road.y2)
        const tB = this.paramOnLine(b, road.x1, road.y1, road.x2, road.y2)
        return tA - tB
      })

      for (let i = 0; i < points.length - 1; i++) {
        const p1 = points[i]
        const p2 = points[i + 1]
        const dist = this.distance(p1.x, p1.y, p2.x, p2.y)

        if (dist < 1) continue

        const key1 = this.pointKey(p1.x, p1.y)
        const key2 = this.pointKey(p2.x, p2.y)
        const segIdStr = `seg_${segId++}`

        const segment: RoadSegment = {
          id: segIdStr,
          startPoint: p1,
          endPoint: p2,
          length: dist,
          roadId: road.id,
          type: road.type || 'main'
        }
        this.segments.push(segment)

        const node1 = this.graphNodes.get(key1)
        const node2 = this.graphNodes.get(key2)

        if (node1 && node2) {
          node1.edges.push({
            toNodeId: key2,
            distance: dist,
            segmentId: segIdStr,
            roadType: road.type || 'main',
            roadName: road.name
          })
          node2.edges.push({
            toNodeId: key1,
            distance: dist,
            segmentId: segIdStr,
            roadType: road.type || 'main',
            roadName: road.name
          })
        }
      }
    }

    this.network = this.networkAnalyzer.analyze(this.roads)
    console.log(`图构建完成: ${this.graphNodes.size}个节点, ${this.segments.length}条边`)
  }

  private lineIntersection(x1: number, y1: number, x2: number, y2: number,
    x3: number, y3: number, x4: number, y4: number): Point | null {
    const denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if (Math.abs(denom) < 0.001) return null

    const t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    const u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

    if (t >= 0 && t <= 1 && u >= 0 && u <= 1) {
      return { x: x1 + t * (x2 - x1), y: y1 + t * (y2 - y1) }
    }
    return null
  }

  private paramOnLine(p: Point, x1: number, y1: number, x2: number, y2: number): number {
    const dx = x2 - x1
    const dy = y2 - y1
    const lenSq = dx * dx + dy * dy
    if (lenSq < 0.001) return 0
    return ((p.x - x1) * dx + (p.y - y1) * dy) / lenSq
  }

  private pointKey(x: number, y: number): string {
    return `${Math.round(x)},${Math.round(y)}`
  }

  private distance(x1: number, y1: number, x2: number, y2: number): number {
    return Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2))
  }

  updateOptions(options: Partial<PathPlanningOptions>): void {
    if (options.obstacles !== undefined) this.obstacles = options.obstacles
    if (options.windDirection !== undefined) this.windDirection = options.windDirection
    if (options.windSpeed !== undefined) this.windSpeed = options.windSpeed

    if (options.roads !== undefined && options.roads.length > 0) {
      this.roads = options.roads
      this.buildGraph()
    }
  }

  getRoadNetwork(): RoadNetwork | null {
    return this.network
  }

  findPath(options: PathPlanningOptions): PathResult {
    this.updateOptions(options)

    if (this.graphNodes.size === 0) {
      console.warn('道路图为空')
      return this.createDirectPath(options.startPoint, options.endPoint)
    }

    const startKey = this.findNearestNodeKey(options.startPoint)
    const endKey = this.findNearestNodeKey(options.endPoint)

    console.log(`路径搜索: ${startKey} -> ${endKey}`)

    const result = this.dijkstra(startKey, endKey, options.startPoint, options.endPoint)

    if (result.roadSegments.length === 0) {
      console.warn('Dijkstra搜索失败')
      return this.createDirectPath(options.startPoint, options.endPoint)
    }

    console.log(`路径找到: ${result.path.length}个点, ${result.roadSegments.length}个路段, 距离${result.distance.toFixed(1)}m`)
    return result
  }

  private findNearestNodeKey(point: Point): string {
    let nearestKey = ''
    let minDist = Infinity

    for (const [key, node] of this.graphNodes) {
      const dist = this.distance(point.x, point.y, node.x, node.y)
      if (dist < minDist) {
        minDist = dist
        nearestKey = key
      }
    }

    return nearestKey
  }

  private dijkstra(startKey: string, endKey: string, originalStart: Point, originalEnd: Point): PathResult {
    const distances = new Map<string, number>()
    const previous = new Map<string, { nodeId: string; edge: GraphEdge }>()
    const visited = new Set<string>()
    const pq: { nodeId: string; dist: number }[] = []

    for (const key of this.graphNodes.keys()) {
      distances.set(key, Infinity)
    }
    distances.set(startKey, 0)
    pq.push({ nodeId: startKey, dist: 0 })

    let iterations = 0
    const maxIterations = 10000

    while (pq.length > 0 && iterations < maxIterations) {
      iterations++
      pq.sort((a, b) => a.dist - b.dist)
      const current = pq.shift()!

      if (visited.has(current.nodeId)) continue
      visited.add(current.nodeId)

      if (current.nodeId === endKey) {
        console.log(`Dijkstra完成，迭代${iterations}次`)
        break
      }

      const node = this.graphNodes.get(current.nodeId)
      if (!node) continue

      for (const edge of node.edges) {
        if (visited.has(edge.toNodeId)) continue

        const newDist = distances.get(current.nodeId)! + edge.distance
        if (newDist < distances.get(edge.toNodeId)!) {
          distances.set(edge.toNodeId, newDist)
          previous.set(edge.toNodeId, { nodeId: current.nodeId, edge })
          pq.push({ nodeId: edge.toNodeId, dist: newDist })
        }
      }
    }

    if (!previous.has(endKey) && startKey !== endKey) {
      console.warn(`无法找到从 ${startKey} 到 ${endKey} 的路径`)
      return this.createDirectPath(originalStart, originalEnd)
    }

    return this.buildResult(startKey, endKey, originalStart, originalEnd, previous)
  }

  private buildResult(
    startKey: string,
    endKey: string,
    originalStart: Point,
    originalEnd: Point,
    previous: Map<string, { nodeId: string; edge: GraphEdge }>
  ): PathResult {
    const nodePath: string[] = [endKey]
    const edges: GraphEdge[] = []
    let current = endKey

    while (current !== startKey) {
      const prev = previous.get(current)
      if (!prev) break
      nodePath.unshift(prev.nodeId)
      edges.unshift(prev.edge)
      current = prev.nodeId
    }

    const path: Point[] = [originalStart]
    const roadSegments: RoadSegment[] = []
    const pathDetails: PathDetail[] = []

    for (let i = 0; i < nodePath.length; i++) {
      const node = this.graphNodes.get(nodePath[i])
      if (node) {
        path.push({ x: node.x, y: node.y })

        if (i < edges.length) {
          const edge = edges[i]
          const segment = this.segments.find(s => s.id === edge.segmentId)
          if (segment) {
            roadSegments.push(segment)
            pathDetails.push({
              segmentIndex: pathDetails.length,
              startPoint: path[path.length - 2],
              endPoint: { x: node.x, y: node.y },
              distance: edge.distance,
              roadType: edge.roadType,
              roadName: edge.roadName
            })
          }
        }
      }
    }

    path.push(originalEnd)

    const totalDistance = this.calculateTotalDistance(path)
    const estimatedTime = totalDistance / 1.5 / 60
    const riskLevel = this.calculateRiskLevel(path, originalStart)

    return {
      path,
      distance: totalDistance,
      estimatedTime,
      riskLevel,
      roadSegments,
      pathDetails
    }
  }

  private calculateTotalDistance(path: Point[]): number {
    let dist = 0
    for (let i = 1; i < path.length; i++) {
      dist += this.distance(path[i - 1].x, path[i - 1].y, path[i].x, path[i].y)
    }
    return dist
  }

  private calculateRiskLevel(path: Point[], leakPoint: Point): 'low' | 'medium' | 'high' {
    let totalRisk = 0
    for (const p of path) {
      const d = this.distance(p.x, p.y, leakPoint.x, leakPoint.y)
      totalRisk += Math.max(0, 1 - d / 500)
    }
    const avgRisk = totalRisk / path.length
    if (avgRisk < 0.3) return 'low'
    if (avgRisk < 0.6) return 'medium'
    return 'high'
  }

  private createDirectPath(start: Point, end: Point): PathResult {
    const dist = this.distance(start.x, start.y, end.x, end.y)
    return {
      path: [start, end],
      distance: dist,
      estimatedTime: dist / 1.5 / 60,
      riskLevel: 'high',
      roadSegments: [],
      pathDetails: []
    }
  }

  calculateRisk(point: Point, leakPoint: Point): number {
    const d = this.distance(point.x, point.y, leakPoint.x, leakPoint.y)
    return Math.max(0, 1 - d / 500)
  }

  isObstacle(point: Point): boolean {
    return this.obstacles.some(obs =>
      point.x >= obs.x && point.x <= obs.x + obs.width &&
      point.y >= obs.y && point.y <= obs.y + obs.height
    )
  }

  findMultipleEscapeRoutes(
    leakPoint: Point,
    exitPoints: Point[],
    options: Partial<PathPlanningOptions> = {}
  ): PathResult[] {
    const results: PathResult[] = []
    for (const exit of exitPoints) {
      const result = this.findPath({
        startPoint: leakPoint,
        endPoint: exit,
        ...options
      })
      results.push(result)
    }
    results.sort((a, b) => {
      const riskOrder = { low: 0, medium: 1, high: 2 }
      if (riskOrder[a.riskLevel] !== riskOrder[b.riskLevel]) {
        return riskOrder[a.riskLevel] - riskOrder[b.riskLevel]
      }
      return a.distance - b.distance
    })
    return results
  }

  findAllBuildingEscapeRoutes(
    buildingEntrances: Point[],
    exitPoints: Point[],
    options: Partial<PathPlanningOptions> = {}
  ): Map<string, PathResult> {
    const routes = new Map<string, PathResult>()
    for (let i = 0; i < buildingEntrances.length; i++) {
      const entrance = buildingEntrances[i]
      let bestRoute: PathResult | null = null
      let minDist = Infinity

      for (const exit of exitPoints) {
        const result = this.findPath({
          startPoint: entrance,
          endPoint: exit,
          ...options
        })
        if (result.distance < minDist) {
          minDist = result.distance
          bestRoute = result
        }
      }

      if (bestRoute) {
        routes.set(`building_${i}`, bestRoute)
      }
    }
    return routes
  }

  generateOptimalEvacuationPlan(
    leakPoint: Point,
    personnelCount: number,
    exitPoints: Point[],
    options: Partial<PathPlanningOptions> = {}
  ): {
    routes: PathResult[]
    totalCapacity: number
    recommendedRoute: PathResult
    estimatedTotalTime: number
  } {
    const routes = this.findMultipleEscapeRoutes(leakPoint, exitPoints, options)
    const totalCapacity = exitPoints.length * 200
    const recommendedRoute = routes[0]
    const estimatedTotalTime = Math.ceil(personnelCount / 200) * recommendedRoute.estimatedTime

    return {
      routes,
      totalCapacity,
      recommendedRoute,
      estimatedTotalTime
    }
  }

  clearCache(): void { }
}

export const pathPlanner = new PathPlanner()

export const defaultObstacles: Obstacle[] = [
  { x: 300, y: 200, width: 100, height: 80, name: '车间1' },
  { x: 700, y: 200, width: 100, height: 80, name: '车间2' },
  { x: 550, y: 150, width: 100, height: 80, name: '办公楼' },
  { x: 300, y: 400, width: 100, height: 80, name: '仓库' },
  { x: 700, y: 400, width: 100, height: 80, name: '设备房' },
  { x: 150, y: 250, width: 120, height: 100, name: '行政楼' }
]

export const defaultRoads: Road[] = [
  { id: 1, x1: 100, y1: 300, x2: 1100, y2: 300, width: 8, type: 'main', name: '东西主干道' },
  { id: 2, x1: 600, y1: 100, x2: 600, y2: 500, width: 8, type: 'main', name: '南北主干道' },
  { id: 3, x1: 100, y1: 200, x2: 400, y2: 200, width: 8, type: 'main', name: '北侧西段道路' },
  { id: 4, x1: 800, y1: 200, x2: 1100, y2: 200, width: 8, type: 'main', name: '北侧东段道路' },
  { id: 5, x1: 100, y1: 400, x2: 400, y2: 400, width: 8, type: 'main', name: '南侧西段道路' },
  { id: 6, x1: 800, y1: 400, x2: 1100, y2: 400, width: 8, type: 'main', name: '南侧东段道路' },
  { id: 7, x1: 300, y1: 200, x2: 900, y2: 200, width: 4, type: 'secondary', name: '北侧横向通道' },
  { id: 8, x1: 300, y1: 400, x2: 900, y2: 400, width: 4, type: 'secondary', name: '南侧横向通道' },
  { id: 9, x1: 400, y1: 100, x2: 400, y2: 500, width: 4, type: 'secondary', name: '西侧纵向通道' },
  { id: 10, x1: 800, y1: 100, x2: 800, y2: 500, width: 4, type: 'secondary', name: '东侧纵向通道' },
  { id: 11, x1: 500, y1: 150, x2: 700, y2: 150, width: 4, type: 'secondary', name: '办公区北侧通道' },
  { id: 12, x1: 500, y1: 250, x2: 700, y2: 250, width: 4, type: 'secondary', name: '办公区南侧通道' },
  { id: 13, x1: 500, y1: 350, x2: 700, y2: 350, width: 4, type: 'secondary', name: '中心区北侧通道' },
  { id: 14, x1: 500, y1: 450, x2: 700, y2: 450, width: 4, type: 'secondary', name: '中心区南侧通道' }
]

export const defaultExitPoints: Point[] = [
  { x: 100, y: 300 },
  { x: 1100, y: 300 },
  { x: 600, y: 100 }
]

export const defaultBuildingEntrances: Point[] = [
  { x: 300, y: 200 },
  { x: 700, y: 200 },
  { x: 600, y: 250 },
  { x: 300, y: 400 },
  { x: 700, y: 400 },
  { x: 270, y: 300 }
]

export const buildingNames: string[] = [
  '车间1',
  '车间2',
  '办公楼',
  '仓库',
  '设备房',
  '行政楼'
]
