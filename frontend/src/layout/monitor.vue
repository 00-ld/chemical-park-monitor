<template>
  <div class="monitor-page">
    <div class="bg-grid"></div>

    <!-- 顶部 -->
    <div class="header">
      <el-button type="primary" @click="goBack" class="back-btn">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>

      <div class="title">
        <span class="top">化工园区重点监测区域 - {{ id }}</span>
      </div>

      <div class="info">
        <span class="tag-live">实时监测</span>
        <span :class="hasAlarm ? 'tag-danger' : 'tag-safe'">
          {{ hasAlarm ? '存在泄漏风险！' : '无泄漏风险' }}
        </span>
        <span class="tag-online">在线</span>
      </div>
    </div>

    <!-- 中间主体 -->
    <div class="main-body">

      <!-- 左侧面板 -->
      <div class="left-panel">
        <div class="card">
          <div class="card-title">实时气体浓度</div>
          <div class="card-data">
            CH₄ 甲烷：
            <span :class="isGasAlarm('methane') ? 'text-red' : 'text-green'">
              {{ gasData.methane }}%LEL
            </span>
          </div>
          <div class="card-data">
            H₂S 硫化氢：
            <span :class="isGasAlarm('h2s') ? 'text-red' : 'text-green'">
              {{ gasData.h2s }}ppm
            </span>
          </div>
          <div class="card-data">
            CO 一氧化碳：
            <span :class="isGasAlarm('co') ? 'text-red' : 'text-green'">
              {{ gasData.co }}ppm
            </span>
          </div>
          <div class="card-data">
            VOC 挥发物：
            <span :class="isGasAlarm('voc') ? 'text-red' : 'text-green'">
              {{ gasData.voc }}ppm
            </span>
          </div>
          <div class="card-data">
            O₂ 氧气：
            <span :class="isOxygenAlarm ? 'text-red' : 'text-green'">
              {{ gasData.oxygen }}%
            </span>
          </div>
        </div>

        <div class="card">
          <div class="card-title">环境监测</div>
          <div class="card-data">风速：{{ envData.wind }}m/s</div>
          <div class="card-data">温度：{{ envData.temp }}℃</div>
          <div class="card-data">湿度：{{ envData.humidity }}%</div>
          <div class="card-data">气压：{{ envData.pressure }}kPa</div>
          <div class="card-data">噪声：{{ envData.noise }}dB</div>
        </div>

        <!-- 动态环形图 -->
        <div class="card chart-card">
          <div class="card-title">气体浓度占比</div>
          <div class="chart_round_text">安全指数</div>
          <div class="pie-chart">
            <div class="pie" :style="{ background: `conic-gradient(#00d1ff ${safeValue}%, transparent ${safeValue}%)` }"></div>
            <div :class="safeValue < 80 ? 'pie-text text-red' : 'pie-text'">
              <div>{{ safeValue }}%</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 中间视频 -->
      <div class="video-container">
        <div class="tech-border">
          <div class="corner lt"></div>
          <div class="corner rt"></div>
          <div class="corner lb"></div>
          <div class="corner rb"></div>

          <video
            class="video-player"
            :src="camera.url"
            autoplay
            muted
            loop
            playsinline
          ></video>

          <div class="status">LIVE</div>
          <div class="video-overlay">
            <div class="label">监测ID：MONITOR-A{{ id }}</div>
            <div class="label">定位：{{ camera.name }}</div>
            <div class="label">
              实时状态：
              <span :class="hasAlarm ? 'status-alarm' : 'status-ok'">
                {{ hasAlarm ? '异常' : '正常' }}
              </span>
            </div>
            <div class="label">更新时间：{{ nowTime }}</div>
          </div>
        </div>
      </div>

      <!-- 右侧面板 -->
      <div class="right-panel">
        <div class="card">
          <div class="card-title">设备状态</div>
          <div class="card-data">摄像头：<span class="status-ok">正常在线</span></div>
          <div class="card-data">
            气体传感器：
            <span :class="hasGasAlarm ? 'status-alarm' : 'status-ok'">
              {{ hasGasAlarm ? '数据异常' : '正常' }}
            </span>
          </div>
          <div class="card-data">环境传感器：<span class="status-ok">正常</span></div>
          <div class="card-data">
            报警状态：
            <span :class="hasAlarm ? 'status-alarm' : 'status-ok'">
              {{ hasAlarm ? '报警中' : '无异常' }}
            </span>
          </div>
          <div class="card-data">网络状态：<span class="status-ok">稳定</span></div>
        </div>

        <div class="card">
          <div class="card-title">安全监测</div>
          <div class="card-data">火焰检测：<span class="status-none">无</span></div>
          <div class="card-data">烟雾检测：<span class="status-none">无</span></div>
          <div class="card-data">人员入侵：<span class="status-none">无</span></div>
          <div class="card-data">阀门状态：关闭</div>
          <div class="card-data">应急状态：<span class="status-ok">正常</span></div>
        </div>

        <!-- 折线图 -->
        <div class="card chart-card">
          <div class="card-title">24小时浓度趋势(ppm)</div>
          <div class="line-chart" @mousemove="showTooltip" @mouseleave="hideTooltip">
            <div class="y-axis">
              <div class="y-tick">0.20</div>
              <div class="y-tick">0.15</div>
              <div class="y-tick">0.10</div>
              <div class="y-tick">0.05</div>
              <div class="y-tick">0</div>
            </div>
            <div class="x-axis">
              <div class="x-tick">0时</div>
              <div class="x-tick">6时</div>
              <div class="x-tick">12时</div>
              <div class="x-tick">18时</div>
              <div class="x-tick">24时</div>
            </div>
            <div class="grid"></div>
            <div class="line-area" :style="lineStyle"></div>
            <div class="dots">
              <div class="dot" v-for="(dot, index) in lineDots" :key="index" :style="{left: dot.left+ '%',bottom: dot.bottom + '%'}"></div>
            </div>
            <div
              v-if="tooltip.show"
              class="tooltip"
              :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }"
            >
              <div>时间：{{ tooltip.time }}</div>
              <div>浓度：{{ tooltip.value }} ppm</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'

// 发射异常状态给父组件
const emit = defineEmits(['monitor-status'])

const route = useRoute()
const router = useRouter()
const id = ref('')
const nowTime = ref('')
let timeTimer: ReturnType<typeof setInterval> | null = null
let dataTimer: ReturnType<typeof setInterval> | null = null

const camera = ref({ name: '', url: '' })

// 气体数据
const gasData = ref({
  methane: '0.21',
  h2s: '0.03',
  co: '0.05',
  voc: '0.12',
  oxygen: '20.9'
})

const envData = ref({
  wind: '2.3',
  temp: '24',
  humidity: '48',
  pressure: '101.32',
  noise: '42'
})

const safeValue = ref(97)
const tooltip = ref({ show: false, x: 0, y: 0, time: '', value: '' })

// —————— 异常阈值 ——————
const gasThreshold = {
  methane: 0.5,
  h2s: 0.05,
  co: 0.1,
  voc: 0.2
}

const isOxygenAlarm = computed(() => {
  const v = parseFloat(gasData.value.oxygen)
  return v < 19.5 || v > 23.5
})

const isGasAlarm = (type) => {
  const v = parseFloat(gasData.value[type])
  return v > gasThreshold[type]
}

const hasGasAlarm = computed(() => {
  return isGasAlarm('methane') || isGasAlarm('h2s') || isGasAlarm('co') || isGasAlarm('voc') || isOxygenAlarm.value
})

const hasAlarm = computed(() => hasGasAlarm.value)

// 安全指数
const updateSafeValue = () => {
  let s = 100
  if (isGasAlarm('methane')) s -= 5
  if (isGasAlarm('h2s')) s -= 10
  if (isGasAlarm('co')) s -= 8
  if (isGasAlarm('voc')) s -= 6
  if (isOxygenAlarm.value) s -= 12
  safeValue.value = Math.max(s, 0)
}

// 发送状态给父组件
watch(hasAlarm, (val) => {
  emit('monitor-status', {
    id: id.value,
    alarm: val
  })
}, { immediate: true })

// —————— 图表 ——————
const lineDots = ref([
  { left: 0, bottom: 10 },
  { left: 20, bottom: 60 },
  { left: 40, bottom: 80 },
  { left: 60, bottom: 65 },
  { left: 80, bottom: 70 },
])

const lineStyle = computed(() => {
  const points = lineDots.value.map(dot => `${dot.left}% ${100 - dot.bottom}%`).join(', ')
  return {
    clipPath: `polygon(${points}, 100% 100%, 0 100%)`,
    background: 'linear-gradient(to bottom, transparent, rgba(0, 209, 255, 0.2))'
  }
})

const showTooltip = (e) => {
  const rect = e.currentTarget.getBoundingClientRect()
  const mx = e.clientX - rect.left
  const w = rect.width
  const ratios = [0,20,40,60,80]
  const xp = (mx/w)*100
  let i=0, min=Math.abs(xp-ratios[0])
  for(let j=1;j<ratios.length;j++){
    const d=Math.abs(xp-ratios[j])
    if(d<min){ min=d; i=j }
  }
  const dot=lineDots.value[i]
  const times=['0时','6时','12时','18时','24时']
  tooltip.value = {
    show:true, x:mx+15, y:(100-dot.bottom)*1.6-25,
    time:times[i], value:((dot.bottom/100)*0.2).toFixed(2)
  }
}
const hideTooltip = () => tooltip.value.show = false

// —————— 时间 & 自动刷新 ——————
const getTime = () => {
  const d = new Date()
  nowTime.value = d.toLocaleString()
}

const startAutoUpdate = () => {
  dataTimer = setInterval(() => {
    gasData.value = {
      methane: (0.18 + Math.random()*0.12).toFixed(2),
      h2s: (0.02 + Math.random()*0.08).toFixed(2),
      co: (0.03 + Math.random()*0.12).toFixed(2),
      voc: (0.1 + Math.random()*0.15).toFixed(2),
      oxygen: (19 + Math.random()*5).toFixed(1)
    }
    envData.value = {
      wind: (1.8+Math.random()*1.2).toFixed(1),
      temp: (23+Math.random()*3).toFixed(0),
      humidity: (45+Math.random()*8).toFixed(0),
      pressure: (100.9+Math.random()*1).toFixed(2),
      noise: (40+Math.random()*8).toFixed(0)
    }
    updateSafeValue()
    lineDots.value = [
      { left:0, bottom:10 },
      { left:20, bottom:50+Math.random()*25 },
      { left:40, bottom:60+Math.random()*25 },
      { left:60, bottom:55+Math.random()*25 },
      { left:80, bottom:65+Math.random()*25 }
    ]
  }, 1500)
}

const goBack = () => router.back()

onMounted(() => {
  id.value = route.params.id
  getTime()
  timeTimer = setInterval(getTime, 1000)
  startAutoUpdate()
  updateSafeValue()

  const cams = [
    {id:1,name:'北区储罐区',url:'/gas_video/气体1.mp4'},
    {id:2,name:'中区生产区',url:'/gas_video/气体2.mp4'},
    {id:3,name:'西区装卸区',url:'/gas_video/气体3.mp4'},
    {id:4,name:'东区危废库',url:'/gas_video/气体4.mp4'}
  ]
  const cur = cams.find(c=>c.id==id.value)
  if(cur) camera.value = cur
})

onUnmounted(() => {
  clearInterval(timeTimer)
  clearInterval(dataTimer)
})
</script>

<style scoped>
.monitor-page {
  width: 100vw;
  height: 100vh;
  background: #050d25;
  position: relative;
  overflow: hidden;
  color: #fff;
  font-family: "Microsoft YaHei", sans-serif;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.back-btn {
  --el-button-text-color: #00d1ff;
  --el-button-bg-color: transparent;
  --el-button-border-color: rgba(0, 160, 255, 0.5);
  --el-button-hover-border-color: #00d1ff;
  --el-button-hover-text-color: #00d1ff;
  font-size: 16px;
  padding: 8px 16px;
}

.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(0, 209, 255, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 209, 255, 0.05) 1px, transparent 1px);
  background-size: 40px 40px;
  z-index: 0;
  pointer-events: none;
}

.header {
  position: relative;
  z-index: 10;
  padding: 0 40px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 80px;
  border-bottom: 1px solid rgba(0, 180, 255, 0.3);
}
.title .top {
  font-size: 26px;
  font-weight: bold;
  color: #00d1ff;
  text-shadow: 0 0 10px #00d1ff;
  margin-left: 125px;
}
.info {
  display: flex;
  gap: 20px;
  font-size: 14px;
}

.main-body {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  gap: 24px;
  padding: 30px 40px;
  height: calc(100vh - 80px);
}

.left-panel,
.right-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 290px;
  flex-shrink: 0;
  margin-top: 60px;
}

.card {
  background: rgba(0, 30, 80, 0.4);
  border: 1px solid rgba(0, 170, 255, 0.3);
  padding: 18px 20px;
  border-radius: 10px;
  transition: all 0.3s;
}
.card-title {
  font-size: 16px;
  color: #00d1ff;
  font-weight: bold;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(0, 170, 255, 0.2);
  text-shadow: 0 0 6px #00d1ff;
}
.card-data {
  font-size: 14px;
  color: #cceeff;
  line-height: 1.9;
  text-shadow: 0 0 4px rgba(255,255,255,0.3);
  transition: all 0.3s;
}

.text-green {
  color: #00ff88;
  font-weight: bold;
}
.text-red {
  color: #ff3333 !important;
  font-weight: bold;
  animation: flash 1s infinite alternate;
}

.chart-card {
  min-height: 220px;
  display: flex;
  flex-direction: column;
  position: relative;
}
.pie-chart {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  height: 140px;
}
.pie {
  width: 110px;
  height: 110px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 1s ease;
}
.pie::after {
  content: "";
  width: 80px;
  height: 80px;
  background: #050d25;
  border-radius: 50%;
  position: absolute;
}
.chart_round_text {
  position: absolute;
  color: #00d1ff;
  font-weight: bold;
  font-size: 16px;
  text-shadow: 0 0 8px #00d1ff;
  left: 110px;
  top: 50px;
}
.pie-text {
  position: absolute;
  color: #00d1ff;
  font-weight: bold;
  font-size: 16px;
  text-shadow: 0 0 8px #00d1ff;
}

.line-chart {
  width: 100%;
  height: 160px;
  position: relative;
  border-left: 1px solid rgba(0, 209, 255, 0.6);
  border-bottom: 1px solid rgba(0, 209, 255, 0.6);
  margin: 0px 0 0 16px;
}
.y-axis {
  position: absolute;
  left: -40px;
  top: 16px;
  height: 100%;
  width: 40px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  color: #99ccff;
  font-size: 14px;
  text-align: right;
  padding-right: 8px;
  text-shadow: 0 0 4px #99ccff;
}
.x-axis {
  position: absolute;
  left: 0;
  bottom: -20px;
  width: 100%;
  display: flex;
  justify-content: space-between;
  color: #99ccff;
  font-size: 14px;
  text-shadow: 0 0 4px #99ccff;
}
.grid {
  position: absolute;
  inset: 0;
  background-image: 
    linear-gradient(rgba(0, 209, 255, 0.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 209, 255, 0.1) 1px, transparent 1px);
  background-size: 20% 20%;
  pointer-events: none;
}
.line-area {
  position: absolute;
  left: 0;
  bottom: 0;
  width: 100%;
  height: 100%;
  transition: all 1s ease;
}
.dots {
  position: absolute;
  left: 0;
  bottom: 0;
  width: 100%;
  height: 100%;
  z-index: 2;
}
.dot {
  position: absolute;
  width: 8px;
  height: 8px;
  background: #00d1ff;
  border-radius: 50%;
  transform: translate(-50%, 50%);
  box-shadow: 0 0 8px #00d1ff, 0 0 16px #00d1ff;
  z-index: 3;
}

.video-container {
  flex: 1;
  margin-top: 100px;
  max-width: 1000px;
  display: flex;
  justify-content: center;
}
.tech-border {
  position: relative;
  width: 100%;
  aspect-ratio: 16/10;
  border: 2px solid rgba(0, 160, 255, 0.6);
  background: #000;
  overflow: hidden;
  border-radius: 8px;
}
.video-player {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.corner {
  position: absolute;
  width: 32px;
  height: 32px;
  border: 3px solid #00d1ff;
  z-index: 6;
}
.corner.lt { top: 12px; left: 12px; border-right: none; border-bottom: none; }
.corner.rt { top: 12px; right: 12px; border-left: none; border-bottom: none; }
.corner.lb { bottom: 12px; left: 12px; border-right: none; border-top: none; }
.corner.rb { bottom: 12px; right: 12px; border-left: none; border-top: none; }

.video-overlay {
  position: absolute;
  top: 44px;
  left: 20px;
  color: #ffffff;
  font-size: 14px;
  font-weight: bolder;
  flex-direction: column;
  gap: 6px;
  z-index: 7;
  text-shadow: 0 0 6px rgba(0,0,0,0.8);
}
.status {
  position: absolute;
  top: 20px;
  left: 20px;
  color: #ff0000;
  font-weight: 700;
  font-size: 20px;
  animation: flash 1s infinite alternate;
  z-index: 7;
  text-shadow: 0 0 8px #807f7f;
}

.tooltip {
  position: absolute;
  background: #0a2a4a;
  color: #fff;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 12px;
  border: 1px solid #00d1ff;
  pointer-events: none;
  z-index: 9999;
  white-space: nowrap;
}

.info span {
  padding: 4px 10px;
  border-radius: 4px;
  font-weight: bold;
}
.tag-live {
  color: #00eaff;
  background: rgba(0, 234, 255, 0.1);
  text-shadow: 0 0 6px #00eaff;
}
.tag-safe {
  color: #409eff;
  background: rgba(64, 158, 255, 0.1);
  text-shadow: 0 0 6px #409eff;
}
.tag-danger {
  color: #fff;
  background: #ff3333;
  animation: flash 1s infinite alternate;
}
.tag-online {
  color: #00ff7f;
  background: rgba(0, 255, 127, 0.15);
  text-shadow: 0 0 8px #00ff7f;
}

.status-ok {
  color: #00ff7f !important;
  font-weight: bold;
  text-shadow: 0 0 6px #00ff7f;
}
.status-alarm {
  color: #ff3333 !important;
  font-weight: bold;
  animation: flash 1s infinite alternate;
}
.status-none {
  color: #a0cfff !important;
  font-weight: 500;
}

.video-overlay .label {
  margin-bottom: 6px;
  text-shadow: 0 0 8px #000;
}

@keyframes flash {
  from { opacity: 1; }
  to { opacity: 0.6; }
}
</style>