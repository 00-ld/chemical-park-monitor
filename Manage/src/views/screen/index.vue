<template>
  <section class="iportal-screen">
    <div v-if="loading" class="screen-state loading-state">
      <div class="state-ring"></div>
      <div>
        <p class="state-title">正在加载数字园区</p>
        <p class="state-desc">SuperMap iPortal 数字大屏连接中</p>
      </div>
    </div>

    <div v-if="loadFailed" class="screen-state error-state">
      <p class="state-title">数字园区暂时无法加载</p>
      <p class="state-desc">
        请检查 iPortal 服务地址或网关代理配置，当前页面不会暴露服务器调试信息。
      </p>
      <el-button class="retry-btn" :icon="Refresh" @click="reloadDashboard">
        重新加载
      </el-button>
    </div>

    <iframe
      :key="frameKey"
      :src="dashboardUrl"
      title="SuperMap iPortal 数字园区大屏"
      class="iportal-frame"
      frameborder="0"
      allowfullscreen
      @load="handleLoaded"
      @error="handleFailed"
    ></iframe>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Refresh } from '@element-plus/icons-vue'

defineOptions({
  name: 'IportalScreen',
})

const DEFAULT_IPORTAL_URL =
  '/iportal/apps/mapdashboard/v2/index.html?id=1329945243&action=view&mode=pc'

const frameKey = ref(0)
const loading = ref(true)
const loadFailed = ref(false)

const dashboardUrl = computed(() => {
  return import.meta.env.VITE_IPORTAL_DASHBOARD_URL || DEFAULT_IPORTAL_URL
})

const handleLoaded = () => {
  loading.value = false
  loadFailed.value = false
}

const handleFailed = () => {
  loading.value = false
  loadFailed.value = true
}

const reloadDashboard = () => {
  loading.value = true
  loadFailed.value = false
  frameKey.value += 1
}
</script>

<style scoped lang="scss">
.iportal-screen {
  position: relative;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background:
    radial-gradient(circle at 18% 18%, rgba(64, 224, 208, 0.16), transparent 30%),
    linear-gradient(135deg, #071526 0%, #0a192f 48%, #112240 100%);
}

.iportal-frame {
  width: 100%;
  height: 100%;
  border: 0;
  background: #071526;
}

.screen-state {
  position: absolute;
  left: 28px;
  bottom: 28px;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 14px;
  max-width: min(520px, calc(100% - 56px));
  padding: 18px 20px;
  box-sizing: border-box;
  border: 1px solid rgba(64, 224, 208, 0.35);
  background: rgba(10, 25, 47, 0.82);
  color: #e6f7ff;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.28);
  backdrop-filter: blur(10px);
}

.loading-state {
  pointer-events: none;
}

.error-state {
  align-items: flex-start;
  flex-direction: column;
}

.state-ring {
  width: 26px;
  height: 26px;
  border: 3px solid rgba(64, 224, 208, 0.24);
  border-top-color: #40e0d0;
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
  flex: 0 0 auto;
}

.state-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #fff;
}

.state-desc {
  margin: 6px 0 0;
  font-size: 13px;
  line-height: 1.6;
  color: rgba(230, 247, 255, 0.78);
}

.retry-btn {
  height: 36px;
  margin-top: 4px;
  border-color: #40e0d0;
  background: rgba(64, 224, 208, 0.1);
  color: #e6f7ff;
}

.retry-btn:hover,
.retry-btn:focus {
  border-color: #69fff0;
  background: rgba(64, 224, 208, 0.18);
  color: #fff;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 640px) {
  .screen-state {
    left: 16px;
    right: 16px;
    bottom: 16px;
    max-width: none;
    padding: 16px;
  }
}
</style>
