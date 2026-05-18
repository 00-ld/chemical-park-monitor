<template>
  <div class="car-detail">
    <!-- 顶部导航栏 -->
    <div class="top-nav">
      <button @click="$router.back()" class="back-btn">
        ← 返回
      </button>
      <h2 class="page-title">小车 {{ route.params.id }} 详情</h2>
    </div>

    <div class="detail-content">
      <!-- 左侧：视频区域 -->
      <div class="left-section">
        <div class="video-card">
          <h3 class="section-title">小车 {{ route.params.id }} 成像视频</h3>
          <div class="video-wrapper">
            <video
              autoplay
              muted
              loop
              :src="videoUrl"
              class="detail-video"
              playsinline
            >
              您的浏览器不支持视频播放
            </video>
          </div>
        </div>
        
        <!-- 小车基本信息卡片 -->
        <div class="info-card">
          <h3 class="section-title">小车基本信息</h3>
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">小车编号</span>
              <span class="info-value">{{ route.params.id }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">监测气体</span>
              <span class="info-value">{{ config.type }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">安全阈值</span>
              <span class="info-value">{{ config.type === '氧气' ? `${config.min}-${config.max} ${config.unit}` : `≤${config.warning} ${config.unit}` }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">当前状态</span>
              <span :class="globalStatus === 'normal' ? 'status-normal' : 'status-warning'">
                {{ globalStatus === 'normal' ? '正常' : '异常' }}
              </span>
            </div>
            <div class="info-item">
              <span class="info-label">最近检测</span>
              <span class="info-value">{{ detailList[detailList.length - 1]?.time || '无数据' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">最近浓度</span>
              <span class="info-value">{{ detailList[detailList.length - 1]?.gas || '0' }} {{ gasUnit }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：数据表格 + 警报 -->
      <div class="right-section">
        <div class="data-card">
          <h3 class="section-title">循环运行细节</h3>
          <div class="table-wrapper">
            <table>
              <thead>
              <tr>
                <th>检测时间</th>
                <th>{{ gasTypeLabel }}</th>
                <th>位置(X/Y)</th>
                <th>状态</th>
              </tr>
              </thead>
              <tbody>
              <tr
                v-for="item in detailList"
                :key="item.time"
                :class="item.status === '一级预警' || globalStatus === 'warning' ? 'warning-row' : ''"
              >
                <td>{{ item.time }}</td>
                <td>{{ item.gas }} {{ gasUnit }}</td>
                <td>{{ item.x }}/{{ item.y }}</td>
                <td :class="(item.status === '正常' && globalStatus === 'normal') ? 'status-normal' : 'status-warning'">
                  {{ globalStatus === 'warning' ? '一级预警（手动标记）' : item.status }}
                </td>
              </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- 气体浓度趋势图表 -->
        <div class="chart-card">
          <h3 class="section-title">浓度趋势分析</h3>
          <div class="chart-wrapper">
            <div class="chart-placeholder">
              <div class="chart-title">{{ gasTypeLabel }}变化趋势</div>
              <div class="chart-bars">
                <div v-for="(item, index) in detailList" :key="index" class="chart-bar-container">
                  <div class="chart-bar" :style="{ height: `${(item.gas / (config.type === '氧气' ? 25 : config.warning * 1.5)) * 100}%` }"></div>
                  <div class="chart-label">{{ item.time.split(' ')[1] }}</div>
                  <div class="chart-value">{{ item.gas }} {{ gasUnit }}</div>
                </div>
              </div>
              <div class="chart-threshold" v-if="config.type !== '氧气'">
                <div class="threshold-line" :style="{ bottom: `${(config.warning / (config.warning * 1.5)) * 100}%` }"></div>
                <div class="threshold-label">安全阈值: {{ config.warning }} {{ gasUnit }}</div>
              </div>
              <div class="chart-threshold" v-else>
                <div class="threshold-line min" :style="{ bottom: `${(config.min / 25) * 100}%` }"></div>
                <div class="threshold-line max" :style="{ bottom: `${(config.max / 25) * 100}%` }"></div>
                <div class="threshold-label">安全范围: {{ config.min }}-{{ config.max }} {{ gasUnit }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 异常警报 -->
        <div v-if="hasWarning" class="alert-card">
          <div class="alert-header">
            <span class="alert-icon">⚠️</span>
            <h4>异常警报处理</h4>
          </div>
          <p class="alert-desc">
            {{ globalStatus === 'warning'
            ? '该小车已被手动标记为异常！'
            : `检测到 ${gasTypeLabel} 超出安全阈值，请立即处理！`
            }}
          </p>
          <button @click="handleWarning" class="alert-btn">
            确认已处理
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCarStore } from '@/store/carStore'

import carVideo1 from '/video/小车1视频.mp4'
import carVideo2 from '/video/小车2视频.mp4'
import carVideo3 from '/video/小车3视频.mp4'
import carVideo4 from '/video/小车4视频.mp4'
import { ElMessage } from 'element-plus'
import axios from 'axios'

interface DetailItem {
  time: string
  gas: number
  x: number
  y: number
  status?: string
}

interface GasConfig {
  type: string
  unit: string
  label: string
  warning?: number
  min?: number
  max?: number
}

const route = useRoute()
const router = useRouter()
const carStore = useCarStore()
const videoUrl = ref('')
const detailList = ref<DetailItem[]>([])

const gasConfig: Record<number, GasConfig> = {
  1: { type: '可燃气体', unit: '%LEL', label: '可燃气体浓度', warning: 25 },
  2: { type: 'H₂S', unit: 'ppm', label: 'H₂S浓度', warning: 10 },
  3: { type: 'CO', unit: 'ppm', label: 'CO浓度', warning: 20 },
  4: { type: '氧气', unit: '%VOL', label: '氧气浓度', min: 19.5, max: 23.5 }
}

function getStatus(gasValue: number, config: GasConfig): string {
  if (config.type === '氧气') {
    return (config.min !== undefined && config.max !== undefined && (gasValue < config.min || gasValue > config.max)) ? '一级预警' : '正常'
  } else {
    return (config.warning !== undefined && gasValue >= config.warning) ? '一级预警' : '正常'
  }
}

const carRawData: Record<number, { video: string; list: Omit<DetailItem, 'status'>[] }> = {
  1: { video: carVideo1, list: [
      { time: '2026-03-14 08:00', gas: 20, x: 200, y: 150 },
      { time: '2026-03-14 08:10', gas: 22, x: 210, y: 155 },
      { time: '2026-03-14 08:20', gas: 21, x: 220, y: 160 },
      { time: '2026-03-14 08:30', gas: 23, x: 230, y: 165 }
    ]},
  2: { video: carVideo2, list: [
      { time: '2026-03-14 08:00', gas: 8, x: 300, y: 250 },
      { time: '2026-03-14 08:10', gas: 9, x: 310, y: 255 },
      { time: '2026-03-14 08:20', gas: 9, x: 320, y: 260 },
      { time: '2026-03-14 08:30', gas: 8, x: 330, y: 265 }
    ]},
  3: { video: carVideo3, list: [
      { time: '2026-03-14 08:00', gas: 19, x: 400, y: 180 },
      { time: '2026-03-14 08:10', gas: 25, x: 410, y: 185 },
      { time: '2026-03-14 08:20', gas: 28, x: 420, y: 190 },
      { time: '2026-03-14 08:30', gas: 22, x: 430, y: 195 }
    ]},
  4: { video: carVideo4, list: [
      { time: '2026-03-14 08:00', gas: 20.9, x: 250, y: 300 },
      { time: '2026-03-14 08:10', gas: 21.0, x: 260, y: 305 },
      { time: '2026-03-14 08:20', gas: 20.8, x: 270, y: 310 },
      { time: '2026-03-14 08:30', gas: 20.9, x: 280, y: 315 }
    ]}
}

const carId = computed(() => route.params.id)
const config = computed(() => gasConfig[carId.value])
const gasTypeLabel = computed(() => config.value?.label || '气体浓度')
const gasUnit = computed(() => config.value?.unit || 'ppm')

const globalStatus = computed(() => carStore.getCarStatus(Number(carId.value)))

const hasWarning = computed(() =>
  detailList.value.some(item => item.status === '一级预警') || globalStatus.value === 'warning'
)

function getCarDetail() {
  const id = Number(carId.value)
  if (!id || !carRawData[id]) {
    ElMessage.warning('小车数据不存在')
    router.push('/car/home')
    return
  }
  const raw = carRawData[id]
  videoUrl.value = raw.video
  detailList.value = raw.list.map(item => ({
    ...item,
    status: getStatus(item.gas, config.value)
  }))
}

// 修复：预警处理函数（正确使用axios）
const handleWarning = async () => {
  try {
    // 1. 保存预警历史到数据库
    await axios.post('http://localhost:8081/api/history/add', {
      carId: Number(carId.value),
      gasType: config.value.type,
      gasValue: detailList.value[0]?.gas || 0 // 取当前浓度
    })

    // 2. 重置小车状态（原有逻辑）
    if (globalStatus.value === 'warning') {
      carStore.resetCarStatus(Number(carId.value))
    }
    ElMessage.success('已确认处理，系统已记录！')
  } catch (error) {
    console.error('处理失败：', error)
    ElMessage.error('处理异常，请重试')
  }
}

// 修复：监听路由参数变化，即时加载数据
watch(
  () => route.params.id,
  (newId) => {
    if (newId) {
      getCarDetail()
    }
  },
  { immediate: true }
)

watch(globalStatus, () => {
  console.log(`小车${carId.value}全局状态更新为：${globalStatus.value}`)
}, { immediate: true })

onMounted(async () => {
  await carStore.fetchCarDataFromDB()
  getCarDetail()
})
</script>

<style scoped>
/* 全局重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.car-detail {
  min-height: 100vh;
  background-color: transparent;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
  color: #e0e6ed;
  position: relative;
}

.car-detail::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: url('https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=modern%20industrial%20factory%20interior%20with%20high-tech%20equipment%2C%20blurred%20background%2C%20clean%20lines%2C%20blue%20accents&image_size=landscape_16_9') center/cover no-repeat;
  filter: blur(8px) brightness(0.4);
  z-index: -1;
  opacity: 0.8;
  pointer-events: none;
}

/* 顶部导航栏 */
.top-nav {
  display: flex;
  align-items: center;
  padding: 12px 24px;
  background: rgba(10, 25, 50, 0.8);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(64, 224, 208, 0.2);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
  position: relative;
  z-index: 1;
}
.back-btn {
  padding: 8px 16px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #e0e6ed;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}
.back-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 224, 208, 0.3);
  border-color: #40e0d0;
  color: #40e0d0;
}
.page-title {
  margin-left: 20px;
  font-size: 20px;
  font-weight: 600;
  color: #40e0d0;
  text-shadow: 0 0 10px rgba(64, 224, 208, 0.3);
}

/* 内容区域（左右分栏） */
.detail-content {
  display: flex;
  gap: 24px;
  padding: 24px;
  max-width: 1600px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
}

/* 左侧视频区域 */
.left-section {
  flex: 1;
  min-width: 600px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.video-card, .info-card, .data-card, .chart-card {
  background: rgba(10, 25, 50, 0.6);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(64, 224, 208, 0.2);
}
.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}
.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.info-label {
  font-size: 14px;
  color: #b8e8e4;
  font-weight: 500;
}
.info-value {
  font-size: 16px;
  color: #e0e6ed;
  font-weight: 600;
}
.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #40e0d0;
  margin-bottom: 16px;
}
.video-wrapper {
  position: relative;
  width: 100%;
  padding-top: 56.25%; /* 16:9 比例，视频不会变形 */
  border-radius: 8px;
  overflow: hidden;
  background: #000;
}
.detail-video {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  pointer-events: none;
}

/* 右侧数据区域 */
.right-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.table-wrapper {
  overflow-x: auto;
  border-radius: 8px;
  background: transparent;
}
table {
  width: 100%;
  border-collapse: collapse;
  color: #e0e6ed;
}
thead tr {
  background: rgba(0, 0, 0, 0.3);
  color: #40e0d0;
  border-bottom: 1px solid rgba(64, 224, 208, 0.3);
}
th, td {
  padding: 12px 16px;
  text-align: center;
  font-size: 14px;
}
th {
  font-weight: 600;
}
tbody tr {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  transition: background-color 0.2s;
}
tbody tr:hover {
  background-color: rgba(64, 224, 208, 0.1);
}
.warning-row {
  background-color: rgba(229, 62, 62, 0.1) !important;
}
.status-normal {
  color: #40e0d0;
  font-weight: 600;
}
.status-warning {
  color: #ff4d4f;
  font-weight: 600;
}

/* 气体浓度趋势图表 */
.chart-wrapper {
  width: 100%;
  height: 300px;
}
.chart-placeholder {
  width: 100%;
  height: 100%;
  position: relative;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 20px;
}
.chart-title {
  font-size: 14px;
  font-weight: 600;
  color: #40e0d0;
  margin-bottom: 20px;
  text-align: center;
}
.chart-bars {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 200px;
  position: relative;
}
.chart-bar-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  flex: 1;
  max-width: 60px;
}
.chart-bar {
  width: 100%;
  background: linear-gradient(to top, #40e0d0, #0a5cad);
  border-radius: 4px 4px 0 0;
  transition: height 0.5s ease;
  position: relative;
  overflow: hidden;
}
.chart-bar::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(to top, rgba(255, 255, 255, 0), rgba(255, 255, 255, 0.3));
}
.chart-label {
  font-size: 12px;
  color: #b8e8e4;
  text-align: center;
}
.chart-value {
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  text-align: center;
}
.chart-threshold {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 40px;
  pointer-events: none;
}
.threshold-line {
  position: absolute;
  left: 0;
  right: 0;
  height: 2px;
  background: #ff4d4f;
  z-index: 1;
}
.threshold-line.min {
  background: #40e0d0;
}
.threshold-line.max {
  background: #ff4d4f;
}
.threshold-label {
  position: absolute;
  right: 10px;
  font-size: 12px;
  color: #fff;
  background: rgba(229, 62, 62, 0.8);
  padding: 2px 8px;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
  z-index: 2;
}

/* 警报卡片 */
.alert-card {
  background: rgba(229, 62, 62, 0.2);
  border: 1px solid rgba(229, 62, 62, 0.5);
  border-radius: 12px;
  padding: 20px;
}
.alert-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}
.alert-icon {
  font-size: 20px;
}
.alert-header h4 {
  font-size: 16px;
  font-weight: 600;
  color: #ff6b6b;
}
.alert-desc {
  font-size: 14px;
  color: #e0e6ed;
  margin-bottom: 16px;
}
.alert-btn {
  padding: 10px 20px;
  background: linear-gradient(90deg, #ff4d4f, #ff7875);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(255, 77, 79, 0.4);
}
.alert-btn:hover {
  background: linear-gradient(90deg, #ff7875, #ff4d4f);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 77, 79, 0.6);
}

/* 响应式适配（小屏幕自动堆叠） */
@media (max-width: 1200px) {
  .detail-content {
    flex-direction: column;
  }
  .left-section {
    min-width: 100%;
  }
}
</style>