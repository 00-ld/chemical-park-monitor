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

defineOptions({
  name: 'ParkScene3D',
})

defineEmits<{
  (e: 'facility-click', id: string): void
}>()

const DEFAULT_IPORTAL_URL =
  '/iportal/apps/mapdashboard/v2/index.html?id=1329945243&action=view&mode=pc'

const viewerUrl = computed(() => {
  return import.meta.env.VITE_IPORTAL_DASHBOARD_URL || DEFAULT_IPORTAL_URL
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
