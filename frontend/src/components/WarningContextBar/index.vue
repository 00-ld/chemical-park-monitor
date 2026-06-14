<template>
  <div v-if="context" class="warning-context-bar">
    <div class="context-main">
      <div class="context-kicker">当前联动事件</div>
      <div class="context-title">
        小车 {{ context.carId || '--' }}
        <span v-if="context.areaName"> · {{ context.areaName }}</span>
        <span v-if="context.gasType"> · {{ context.gasType }}</span>
      </div>
      <div class="context-meta">
        <span v-if="context.warningId">预警编号 {{ context.warningId }}</span>
        <span v-if="context.x || context.y">坐标 X {{ context.x || '--' }} / Y {{ context.y || '--' }}</span>
        <span v-if="context.gasValue">浓度 {{ context.gasValue }}</span>
      </div>
    </div>

    <div class="context-actions">
      <el-button size="small" type="primary" :icon="Location" @click="goSmartMap">地图定位</el-button>
      <el-button size="small" type="success" :icon="Van" @click="goCar">智巡跟进</el-button>
      <el-button size="small" type="warning" :icon="VideoCamera" @click="goMonitor">视频核验</el-button>
      <el-button size="small" type="info" :icon="Monitor" @click="goYolo">AI复核</el-button>
      <el-button size="small" text :icon="Close" @click="clearContext">解除联动</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Close, Location, Monitor, Van, VideoCamera } from '@element-plus/icons-vue'
import {
  clearWarningContext,
  getCurrentWarningContext,
  getWarningContextFromQuery,
  saveWarningContext,
  withWarningQuery,
  type WarningContext,
} from '@/utils/warningContext'

defineOptions({
  name: 'WarningContextBar',
})

const route = useRoute()
const router = useRouter()
const context = ref<WarningContext | null>(null)

watch(
  () => route.fullPath,
  () => {
    const queryContext = getWarningContextFromQuery(route.query)
    context.value = queryContext ? saveWarningContext(queryContext) : getCurrentWarningContext(route.query)
  },
  { immediate: true },
)

const currentContext = () => context.value || getCurrentWarningContext(route.query)

const goSmartMap = () => {
  router.push({
    path: '/smart-map',
    query: withWarningQuery({ autoConfig: 'true' }, currentContext(), 'link-bar'),
  })
}

const goCar = () => {
  router.push({
    path: '/car/home',
    query: withWarningQuery({}, currentContext(), 'link-bar'),
  })
}

const goMonitor = () => {
  const target = currentContext()
  const monitorId = target?.monitorId || target?.carId || '1'
  router.push({
    path: `/monitor/${monitorId}`,
    query: withWarningQuery({ monitorId }, target, 'link-bar'),
  })
}

const goYolo = () => {
  router.push({
    path: '/yolo',
    query: withWarningQuery({}, currentContext(), 'link-bar'),
  })
}

const clearContext = () => {
  clearWarningContext()
  context.value = null
}
</script>

<style scoped>
.warning-context-bar {
  width: 100%;
  margin: 0 0 16px;
  padding: 12px 14px;
  border: 1px solid rgba(64, 224, 208, 0.28);
  border-radius: 8px;
  background: rgba(10, 25, 50, 0.9);
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.22);
  color: #e8fbff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  box-sizing: border-box;
}

.context-main {
  min-width: 0;
}

.context-kicker {
  color: #40e0d0;
  font-size: 12px;
  margin-bottom: 4px;
}

.context-title {
  font-size: 16px;
  font-weight: 700;
  line-height: 1.4;
}

.context-meta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 4px;
  color: #a0cfff;
  font-size: 12px;
}

.context-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
  flex: 0 0 auto;
}

@media (max-width: 960px) {
  .warning-context-bar {
    align-items: flex-start;
    flex-direction: column;
  }

  .context-actions {
    justify-content: flex-start;
  }
}
</style>
