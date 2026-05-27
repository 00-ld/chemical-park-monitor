<template>
  <div class="scene-3d-placeholder">
    <div class="placeholder-content">
      <i class="fas fa-cube"></i>
      <p>3D 场景加载中...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  selectedFacilityId?: string
}>()

defineEmits<{
  (e: 'facility-click', id: string): void
}>()
</script>

<style scoped>
.scene-3d-placeholder {
  width: 100%;
  height: 100%;
  position: absolute;
  top: 0;
  left: 0;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}
.placeholder-content {
  text-align: center;
  color: #666;
}
.placeholder-content i {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}
.placeholder-content p {
  font-size: 14px;
}
</style>
