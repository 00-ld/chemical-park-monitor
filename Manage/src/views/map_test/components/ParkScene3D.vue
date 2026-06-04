<template>
  <div class="scene-3d-container">
    <iframe
      :src="viewerUrl"
      class="scene-3d-iframe"
      frameborder="0"
      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope"
      allowfullscreen
    ></iframe>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  selectedFacilityId?: string
}>()

defineEmits<{
  (e: 'facility-click', id: string): void
}>()

const viewerUrl = computed(() => {
  const base = import.meta.env.VITE_APP_BASE_API || '/api'
  // 3D viewer is served as static file at /3d_viewer/
  return '/3d_viewer/'
})
</script>

<style scoped>
.scene-3d-container {
  width: 100%;
  height: 100%;
  position: absolute;
  top: 0;
  left: 0;
  background: #020b1a;
}
.scene-3d-iframe {
  width: 100%;
  height: 100%;
  border: none;
}
</style>
