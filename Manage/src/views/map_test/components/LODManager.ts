import * as THREE from 'three'

export class LODManager {
  private camera: THREE.PerspectiveCamera
  private entries: Map<string, THREE.Group> = new Map()

  constructor(camera: THREE.PerspectiveCamera) {
    this.camera = camera
  }

  register(id: string, group: THREE.Group) {
    this.entries.set(id, group)
  }

  update() {
    // Placeholder - no LOD updates needed for now
  }
}
