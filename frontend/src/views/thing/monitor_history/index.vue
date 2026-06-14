<template>
  <div class="container">
    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 实时监测视频区 -->
      <el-card class="card video-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="card-title">
              <el-icon><VideoPlay /></el-icon>
              实时泄漏监测
            </span>
            <!-- 搜索 + 新增按钮 -->
            <div class="header-toolbar">
              <el-input
                  v-model="searchKey"
                  placeholder="搜索监测区域"
                  style="width: 200px"
                  size="small"
                  clearable
              >
                <template #prefix><el-icon><Search /></el-icon></template>
              </el-input>
              <el-button
                  type="primary"
                  size="small"
                  icon="Plus"
                  @click="openAddDialog"
              >
                新增监测点
              </el-button>
            </div>
          </div>
        </template>

        <!-- 监测点列表（带搜索筛选） -->
        <div class="video-container">
          <div
              v-for="item in filteredMonitorList"
              :key="item.id"
              class="monitor-item"
          >
            <!-- 删除按钮 -->
            <div class="delete-monitor" @click.stop="handleDeleteMonitor(item.id)">
              <el-icon><Close /></el-icon>
            </div>

            <div class="monitor-label" @click="goMonitor(item.id)">
              {{ item.name }}
            </div>
            <div class="video-item">
              <div class="video-placeholder">
                <video
                    class="video_style"
                    autoplay
                    loop
                    muted
                    preload="auto"
                    :src="`/gas_video/气体${item.id}.mp4`"
                    @error="$event.target.style.display='none';$event.target.nextElementSibling.style.display='block'"
                    playsinline
                >
                </video>
                <img
                    src="../../../../public/gas_video/novideo.png"
                    :style="{
                    width: '100%',
                    height: '100%',
                    position: 'absolute',
                    top: '0',
                    left: '0',
                    objectFit: 'contain',
                    display: 'none'
                  }"
                />
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 新增弹窗：添加监测点 -->
      <el-dialog
          v-model="addDialogVisible"
          title="新增监测点"
          width="500px"
          @close="resetAddForm"
      >
        <el-form
            ref="addFormRef"
            :model="addForm"
            label-width="100px"
            size="default"
        >
          <el-form-item
              label="区域监测名"
              prop="name"
              :rules="[{ required: true, message: '请输入监测区域名称', trigger: 'blur' }]"
          >
            <el-input v-model="addForm.name" placeholder="仅需输入区域编号即可，如：3" />
          </el-form-item>
        </el-form>
        <template #footer>
          <div class="dialog-footer">
            <el-button @click="addDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="handleAddMonitor">确认添加</el-button>
          </div>
        </template>
      </el-dialog>

      <!-- 优化后的预警历史记录区域 -->
      <el-card class="card history-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="card-title">
              <el-icon><Clock /></el-icon>
              预警历史记录
            </span>
          </div>
        </template>

        <div class="table-container">
          <el-table
              :data="historyList"
              border
              stripe
              :header-cell-style="{background: '#f5f7fa', color: '#303133', fontWeight: '600'}"
              :row-class-name="({row}) => `level-${getLevelTagType(getRiskLevel(row))}`"
              class="history-table"
          >
            <el-table-column prop="carId" label="小车编号" align="center" width="120" />
            <el-table-column prop="areaName" label="所属区域" align="center" width="120" />
            <el-table-column prop="x" label="坐标X" align="center" width="120" />
            <el-table-column prop="y" label="坐标Y" align="center" width="120" />
            <el-table-column prop="gasType" label="气体类型" align="center" width="100">
              <template #default="scope">
                <el-tag size="small" type="info" class="gas-tag">
                  {{ formatGasType(scope.row.gasType) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="gasValue" label="浓度值" align="center" width="170">
              <template #default="scope">
                <span class="concentration-text">
                  {{ scope.row.gasValue }}
                  {{ normalizeGasType(scope.row.gasType) === 'O2' ? '%VOL' : 'ppm' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="危险等级" align="center" width="130">
              <template #default="scope">
                <div
                    class="level-tag"
                    :class="getLevelTagType(getRiskLevel(scope.row))"
                >
                  {{ getRiskLevelText(getRiskLevel(scope.row)) }}
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="warningTime" label="预警时间" align="center" width="220">
              <template #default="scope">
                {{ formatTime(scope.row.warningTime) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" align="center" width="130">
              <template #default="scope">
                <el-button
                    type="danger"
                    size="small"
                    icon="Delete"
                    @click="handleDelete(scope.row.id)"
                    class="delete-btn"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 泄漏统计图表（只保留一个，美观居中） -->
        <el-card class="card chart-card" shadow="hover">
          <div class="chart-item">
            <div class="chart-title">
              <el-icon><Histogram /></el-icon>
              各区域泄漏次数统计
            </div>
            <div ref="areaChartRef" class="chart-box"></div>
          </div>
        </el-card>
      </el-card>
    </div>

    <!-- 气体等级划分区域 -->
    <el-card class="card level-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon><WarnTriangleFilled /></el-icon>
            气体泄漏危险等级划分标准（中国职业卫生/工业安全国标）
          </span>
        </div>
      </template>

      <!-- 气体类型切换 -->
      <div class="gas-tabs">
        <el-radio-group v-model="activeGasType" size="default" class="radio-group">
          <el-radio-button label="all">全部气体</el-radio-button>
          <el-radio-button label="ch4">甲烷(CH₄)</el-radio-button>
          <el-radio-button label="nh3">氨气(NH₃)</el-radio-button>
          <el-radio-button label="co">一氧化碳(CO)</el-radio-button>
          <el-radio-button label="o2">氧气(O₂)</el-radio-button>
        </el-radio-group>
      </div>

      <!-- 表格容器 - 增加滚动适配 -->
      <div class="table-container">
        <!-- 全部气体汇总表 -->
        <el-table
            v-if="activeGasType === 'all'"
            :data="allGasLevelList"
            border
            stripe
            :header-cell-style="{background: '#f5f7fa', color: '#303133', fontWeight: '600'}"
            class="level-table"
        >
          <el-table-column prop="level" label="危险等级" align="center" min-width="120" />
          <el-table-column prop="color" label="预警色" align="center" min-width="120">
            <template #default="scope">
              <div class="color-tag" :class="scope.row.tagType">{{ scope.row.color }}</div>
            </template>
          </el-table-column>
          <el-table-column prop="ch4" label="甲烷(CH₄)" align="center" min-width="200">
            <template #default="scope">
              <div class="cell-content" style="white-space:pre-line">{{ scope.row.ch4 }}</div>
            </template>
          </el-table-column>
          <el-table-column prop="nh3" label="氨气(NH₃)" align="center" min-width="220">
            <template #default="scope">
              <div class="cell-content" style="white-space:pre-line">{{ scope.row.nh3 }}</div>
            </template>
          </el-table-column>
          <el-table-column prop="co" label="一氧化碳(CO)" align="center" min-width="220">
            <template #default="scope">
              <div class="cell-content" style="white-space:pre-line">{{ scope.row.co }}</div>
            </template>
          </el-table-column>
          <el-table-column prop="o2" label="氧气(O₂)" align="center" min-width="200">
            <template #default="scope">
              <div class="cell-content" style="white-space:pre-line">{{ scope.row.o2 }}</div>
            </template>
          </el-table-column>
          <el-table-column prop="risk" label="风险描述" align="center" min-width="200" />
          <el-table-column prop="response" label="应急响应" align="center" min-width="180" />
        </el-table>

        <!-- 甲烷单独表格 -->
        <el-table
            v-else-if="activeGasType === 'ch4'"
            :data="ch4LevelList"
            border
            stripe
            :header-cell-style="{background: '#f5f7fa', color: '#303133', fontWeight: '600'}"
            class="level-table"
        >
          <el-table-column prop="level" label="危险等级" align="center" min-width="120" />
          <el-table-column prop="color" label="预警色" align="center" min-width="120">
            <template #default="scope">
              <div class="color-tag" :class="scope.row.tagType">{{ scope.row.color }}</div>
            </template>
          </el-table-column>
          <el-table-column prop="concentration" label="浓度范围（占LEL%）" align="center" min-width="180" />
          <el-table-column prop="ppm" label="对应浓度(ppm)" align="center" min-width="180" />
          <el-table-column prop="risk" label="爆炸风险描述" align="center" min-width="250" />
          <el-table-column prop="response" label="应急响应措施" align="center" min-width="200" />
        </el-table>

        <!-- 氨气单独表格 -->
        <el-table
            v-else-if="activeGasType === 'nh3'"
            :data="nh3LevelList"
            border
            stripe
            :header-cell-style="{background: '#f5f7fa', color: '#303133', fontWeight: '600'}"
            class="level-table"
        >
          <el-table-column prop="level" label="危险等级" align="center" min-width="120" />
          <el-table-column prop="color" label="预警色" align="center" min-width="120">
            <template #default="scope">
              <div class="color-tag" :class="scope.row.tagType">{{ scope.row.color }}</div>
            </template>
          </el-table-column>
          <el-table-column prop="mg" label="浓度(mg/m³)" align="center" min-width="150" />
          <el-table-column prop="ppm" label="浓度(ppm)" align="center" min-width="150" />
          <el-table-column prop="risk" label="健康风险描述" align="center" min-width="280" />
          <el-table-column prop="response" label="应急响应措施" align="center" min-width="200" />
        </el-table>

        <!-- 一氧化碳单独表格 -->
        <el-table
            v-else-if="activeGasType === 'co'"
            :data="coLevelList"
            border
            stripe
            :header-cell-style="{background: '#f5f7fa', color: '#303133', fontWeight: '600'}"
            class="level-table"
        >
          <el-table-column prop="level" label="危险等级" align="center" min-width="120" />
          <el-table-column prop="color" label="预警色" align="center" min-width="120">
            <template #default="scope">
              <div class="color-tag" :class="scope.row.tagType">{{ scope.row.color }}</div>
            </template>
          </el-table-column>
          <el-table-column prop="mg" label="浓度(mg/m³)" align="center" min-width="150" />
          <el-table-column prop="ppm" label="浓度(ppm)" align="center" min-width="150" />
          <el-table-column prop="risk" label="健康风险描述" align="center" min-width="280" />
          <el-table-column prop="response" label="应急响应措施" align="center" min-width="200" />
        </el-table>

        <!-- 氧气单独表格 -->
        <el-table
            v-else-if="activeGasType === 'o2'"
            :data="o2LevelList"
            border
            stripe
            :header-cell-style="{background: '#f5f7fa', color: '#303133', fontWeight: '600'}"
            class="level-table"
        >
          <el-table-column prop="level" label="危险等级" align="center" min-width="120" />
          <el-table-column prop="color" label="预警色" align="center" min-width="120">
            <template #default="scope">
              <div class="color-tag" :class="scope.row.tagType">{{ scope.row.color }}</div>
            </template>
          </el-table-column>
          <el-table-column prop="concentration" label="浓度(%VOL)" align="center" min-width="180" />
          <el-table-column prop="risk" label="风险描述" align="center" min-width="300" />
          <el-table-column prop="response" label="应急响应措施" align="center" min-width="200" />
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import {
  VideoPlay, WarnTriangleFilled, Clock, Delete, Plus, Close, Search, Histogram
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, FormInstance } from 'element-plus'
import { useRouter } from 'vue-router'
import request from '@/utils/request'

const router = useRouter()

// 搜索关键词
const searchKey = ref('')

// 监测点列表（本地存储）
interface MonitorItem {
  id: number
  name: string
}
const monitorList = ref<MonitorItem[]>([])

// 新增弹窗
const addDialogVisible = ref(false)
const addFormRef = ref<FormInstance>()
const addForm = ref({
  name: ''
})

// 打开新增弹窗
const openAddDialog = () => {
  addDialogVisible.value = true
}

// 重置表单
const resetAddForm = () => {
  addForm.value.name = ''
  addFormRef.value?.clearValidate()
}

// 从本地加载监测点
const loadMonitorList = () => {
  const local = localStorage.getItem('monitorList')
  if (local) {
    monitorList.value = JSON.parse(local)
  } else {
    // 默认初始化4个
    monitorList.value = Array.from({ length: 4 }, (_, i) => ({
      id: i + 1,
      name: "重点监测区域" + `${i + 1}`
    }))
    saveMonitorList()
  }
}

// 保存到本地
const saveMonitorList = () => {
  localStorage.setItem('monitorList', JSON.stringify(monitorList.value))
}

// 搜索筛选
const filteredMonitorList = computed(() => {
  if (!searchKey.value) return monitorList.value
  return monitorList.value.filter(item =>
      item.name.includes(searchKey.value.trim())
  )
})

// 新增监测点
const handleAddMonitor = async () => {
  if (!addFormRef.value) return
  await addFormRef.value.validate()
  const maxId = monitorList.value.length > 0
      ? Math.max(...monitorList.value.map(i => i.id))
      : 0
  monitorList.value.push({
    id: maxId + 1,
    name: "重点监测区域" + addForm.value.name
  })
  saveMonitorList()
  addDialogVisible.value = false
  resetAddForm()
  ElMessage.success('添加成功！')
}

// 删除监测点
const handleDeleteMonitor = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定删除该监测点？删除后无法恢复', '删除确认', {
      type: 'warning'
    })
    monitorList.value = monitorList.value.filter(item => item.id !== id)
    saveMonitorList()
    ElMessage.success('删除成功')
  } catch (e) {
    ElMessage.info('已取消')
  }
}

//点击跳转监测页面
const goMonitor = (id: number) => {
  router.push(`/monitor/${id}`)
}

// 气体类型切换
const activeGasType = ref('all')

// 图表DOM引用
const areaChartRef = ref<HTMLElement | null>(null)
let areaChart: echarts.ECharts | null = null

// ==================== ECharts 绘图（已按你的要求修改） ====================
const renderCharts = () => {
  if (!areaChart) return
  // 统计区域
  const areaCount: Record<string, number> = {}
  historyList.value.forEach(({ areaName }) => {
    areaCount[areaName] = (areaCount[areaName] || 0) + 1
  })
  const areaNames = Object.keys(areaCount)
  const areaValues = areaNames.map(k => areaCount[k])

  // 区域图表配置
  areaChart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(0, 20, 40, 0.8)',
      borderColor: '#40e0d0',
      textStyle: { color: '#fff', fontSize: 14 }
    },
    grid: {
      left: '10%',
      right: '10%',
      bottom: '15%',
      top: '15%'
    },
    xAxis: {
      type: 'category',
      data: areaNames,
      axisLabel: {
        fontSize: 16, // 放大X轴字体
        color: '#e0e6ed' // 适配深色背景
      },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.2)' } },
      axisTick: { lineStyle: { color: 'rgba(255,255,255,0.2)' } }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        fontSize: 16, // 放大Y轴字体
        color: '#e0e6ed'
      },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.2)' } },
      axisTick: { lineStyle: { color: 'rgba(255,255,255,0.2)' } },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } }
    },
    series: [{
      type: 'bar',
      data: areaValues,
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#409eff' },
          { offset: 1, color: '#40e0d0' }
        ]),
        borderRadius: [4, 4, 0, 0]
      },
      emphasis: {
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#66b1ff' },
            { offset: 1, color: '#66f0e0' }
          ])
        }
      },
      barWidth: 45, // 缩小柱状体粗度
      barMaxWidth: 40,
      barMinWidth: 20,
      barGap: '5%',
      barCategoryGap: '15%'
    }]
  })
}

// 初始化图表
onMounted(() => {
  loadMonitorList()
  if (areaChartRef.value) {
    areaChart = echarts.init(areaChartRef.value)
  }
  fetchHistory()
  window.addEventListener('resize', () => { areaChart?.resize() })
})

onUnmounted(() => {
  areaChart?.dispose()
})

// ========== 核心：按国标定义的四种气体等级划分 ==========
const allGasLevelList = reactive([
  {
    level: '极高危险',
    color: '红色',
    tagType: 'danger',
    ch4: '≥ 50% LEL\n(≈25000ppm)',
    nh3: '≥ 52mg/m³\n(≥ 75ppm)',
    co: '≥ 300mg/m³\n(≥ 262ppm)',
    o2: '< 16%VOL 或 >23.5%VOL',
    risk: '致命风险/爆炸极高风险',
    response: '立即疏散/专业应急'
  },
  {
    level: '危险',
    color: '橙色',
    tagType: 'warning',
    ch4: '25% ~ 50% LEL\n(12500-25000ppm)',
    nh3: '35 ~ 52mg/m³\n(50 ~ 75ppm)',
    co: '100 ~ 300mg/m³\n(87 ~ 262ppm)',
    o2: '16% ~ 19.5%VOL',
    risk: '中毒重伤/爆炸高风险',
    response: '禁止动火/人员撤离'
  },
  {
    level: '预警',
    color: '黄色',
    tagType: 'primary',
    ch4: '10% ~ 25% LEL\n(5000-12500ppm)',
    nh3: '17 ~ 35mg/m³\n(25 ~ 50ppm)',
    co: '50 ~ 100mg/m³\n(43 ~ 87ppm)',
    o2: '19.5% ~ 20.9%VOL',
    risk: '刺激不适/爆炸预警',
    response: '启动报警/加强通风'
  },
  {
    level: '安全',
    color: '灰色',
    tagType: 'info',
    ch4: '< 10% LEL\n(< 5000ppm)',
    nh3: '≤ 17mg/m³\n(≤ 25ppm)',
    co: '≤ 20mg/m³\n(≤ 17ppm)',
    o2: '20.9% ~ 23.5%VOL',
    risk: '无急性风险/可正常作业',
    response: '常规监测/定期巡检'
  }
])

// 甲烷(CH₄) - 按爆炸下限LEL划分
const ch4LevelList = reactive([
  {
    level: '极高危险',
    color: '红色',
    tagType: 'danger',
    concentration: '≥ 50% LEL',
    ppm: '≈25000ppm',
    risk: '接近爆炸极限，随时可能爆炸，立即疏散',
    response: '紧急撤离/切断气源/防爆通风'
  },
  {
    level: '危险',
    color: '橙色',
    tagType: 'warning',
    concentration: '25% ~ 50% LEL',
    ppm: '12500-25000ppm',
    risk: '禁止动火，人员撤离，紧急处置',
    response: '区域隔离/专业防爆处置'
  },
  {
    level: '预警',
    color: '黄色',
    tagType: 'primary',
    concentration: '10% ~ 25% LEL',
    ppm: '5000-12500ppm',
    risk: '需启动报警，加强通风，排查泄漏源',
    response: '启动报警/加强通风/排查泄漏'
  },
  {
    level: '安全',
    color: '灰色',
    tagType: 'info',
    concentration: '< 10% LEL',
    ppm: '< 5000ppm',
    risk: '无爆炸风险，可正常作业',
    response: '常规监测/定期巡检'
  }
])

// 氨气(NH₃) - 刺激性有毒气体
const nh3LevelList = reactive([
  {
    level: '极高危险',
    color: '红色',
    tagType: 'danger',
    mg: '≥ 52mg/m³',
    ppm: '≥ 75ppm',
    risk: '强烈刺激呼吸道和眼部，存在急性中毒风险',
    response: '佩戴正压呼吸器/紧急撤离/专业处置'
  },
  {
    level: '危险',
    color: '橙色',
    tagType: 'warning',
    mg: '35 ~ 52mg/m³',
    ppm: '50 ~ 75ppm',
    risk: '刺激明显，可能引起咳嗽、胸闷等症状',
    response: '立即通风/人员撤离/医学观察'
  },
  {
    level: '预警',
    color: '黄色',
    tagType: 'primary',
    mg: '17 ~ 35mg/m³',
    ppm: '25 ~ 50ppm',
    risk: '刺激眼睛和呼吸道，需报警',
    response: '启动报警/加强通风/佩戴防护装备'
  },
  {
    level: '安全',
    color: '灰色',
    tagType: 'info',
    mg: '≤ 17mg/m³',
    ppm: '≤ 25ppm',
    risk: '低于预警阈值，可维持常规监测',
    response: '常规监测/定期巡检'
  }
])

// 一氧化碳(CO) - 血液窒息性气体
const coLevelList = reactive([
  {
    level: '极高危险',
    color: '红色',
    tagType: 'danger',
    mg: '≥ 300mg/m³',
    ppm: '≥ 262ppm',
    risk: '昏迷、呼吸衰竭，数小时内死亡',
    response: '紧急送医/高压氧治疗/环境通风'
  },
  {
    level: '危险',
    color: '橙色',
    tagType: 'warning',
    mg: '100 ~ 300mg/m³',
    ppm: '87 ~ 262ppm',
    risk: '恶心、呕吐，意识模糊',
    response: '立即撤离/新鲜空气/医学观察'
  },
  {
    level: '预警',
    color: '黄色',
    tagType: 'primary',
    mg: '50 ~ 100mg/m³',
    ppm: '43 ~ 87ppm',
    risk: '头痛、头晕，需报警',
    response: '启动报警/加强通风/人员防护'
  },
  {
    level: '安全',
    color: '灰色',
    tagType: 'info',
    mg: '≤ 20mg/m³',
    ppm: '≤ 17ppm',
    risk: '8小时加权平均容许浓度（PC-TWA）',
    response: '常规监测/定期巡检'
  }
])

// 氧气(O₂) - 浓度异常风险
const o2LevelList = reactive([
  {
    level: '极高危险',
    color: '红色',
    tagType: 'danger',
    concentration: '< 16%VOL 或 >23.5%VOL',
    risk: '严重缺氧致死亡 / 富氧环境火灾爆炸风险剧增',
    response: '缺氧：供氧撤离 / 富氧：严禁明火/通风稀释'
  },
  {
    level: '危险',
    color: '橙色',
    tagType: 'warning',
    concentration: '16% ~ 19.5%VOL',
    risk: '呼吸急促、心跳加快，判断力下降',
    response: '补充氧气/人员撤离/通风换气'
  },
  {
    level: '预警',
    color: '黄色',
    tagType: 'primary',
    concentration: '19.5% ~ 20.9%VOL',
    risk: '开始出现缺氧症状，需关注',
    response: '加强监测/通风换气/人员观察'
  },
  {
    level: '安全',
    color: '灰色',
    tagType: 'info',
    concentration: '20.9% ~ 23.5%VOL',
    risk: '大气正常浓度，安全',
    response: '常规监测/定期巡检'
  }
])

// ========== 预警历史记录相关逻辑 ==========
interface HistoryItem {
  id: number
  carId: string
  areaName: string
  x: number
  y: number
  gasType: string
  gasValue: number
  warningTime: string
}
const historyList = ref<HistoryItem[]>([])

// 格式化气体类型显示
const normalizeGasType = (gasType: string | null | undefined) => {
  const raw = String(gasType || '').trim().toUpperCase()
  if (!raw) return ''
  if (raw.includes('CO') || raw.includes('一氧化碳')) return 'CO'
  if (raw.includes('O2') || raw.includes('O₂') || raw.includes('氧气')) return 'O2'
  if (raw.includes('NH3') || raw.includes('NH₃') || raw.includes('氨')) return 'NH3'
  if (raw.includes('CH4') || raw.includes('CH₄') || raw.includes('甲烷') || raw.includes('可燃')) return 'CH4'
  if (raw.includes('H2S') || raw.includes('H₂S') || raw.includes('硫化氢')) return 'NH3'
  return raw
}

const formatGasType = (gasType: string) => {
  const gasMap: Record<string, string> = {
    CH4: '甲烷(CH₄)',
    NH3: '氨气(NH₃)',
    CO: '一氧化碳(CO)',
    O2: '氧气(O₂)'
  }
  const normalized = normalizeGasType(gasType)
  return gasMap[normalized] || gasType
}

// 格式化时间
const formatTime = (timeStr: string) => {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}`
}

// 核心：根据气体类型和浓度计算危险等级
const getRiskLevel = (item: HistoryItem | null | undefined) => {
  if (!item || !item.gasType || !item.gasValue) return 4

  const gasType = normalizeGasType(item.gasType)
  const value = parseFloat(item.gasValue as unknown as string)

  if (isNaN(value)) return 4

  switch (gasType) {
    case 'CH4':
      return value >= 50 ? 1 : value >= 20 ? 2 : value >= 10 ? 3 : 4
    case 'NH3':
      return value >= 75 ? 1 : value >= 50 ? 2 : value >= 25 ? 3 : 4
    case 'CO':
      return value >= 262 ? 1 : value >= 87 ? 2 : value >= 19 ? 3 : 4
    case 'O2':
      return value >= 20.9 ? 1 : value >= 19.9 ? 2 : value >= 19.5 ? 3 : 4
    default:
      return 4
  }
}

// 获取危险等级文本
const getRiskLevelText = (level: number) => {
  const levelMap: Record<number, string> = {
    1: '极高危险',
    2: '危险',
    3: '预警',
    4: '安全'
  }
  return levelMap[level] || '未知'
}

// 获取危险等级标签样式类型
const getLevelTagType = (level: number) => {
  const typeMap: Record<number, string> = {
    1: 'danger',
    2: 'warning',
    3: 'primary',
    4: 'info'
  }
  return typeMap[level] || 'info'
}

// 获取历史数据
const fetchHistory = async () => {
  try {
    const res = await request.get('/history/list')
    if (res.code === 200) {
      historyList.value = res.data.sort((a: HistoryItem, b: HistoryItem) =>
          new Date(b.warningTime).getTime() - new Date(a.warningTime).getTime()
      )
      renderCharts()
    }
  } catch (error) {
    console.error('获取历史数据失败：', error)
    ElMessage.error('网络异常，无法加载历史数据')
  }
}

// 删除单条记录
const handleDelete = async (id: number) => {
  try {
    await ElMessageBox.confirm(
        '确定要删除这条预警记录吗？',
        '删除确认',
        {
          confirmButtonText: '确认删除',
          cancelButtonText: '取消',
          type: 'warning'
        }
    )

    const res = await request.post('/history/delete', { id })
    if (res.code === 200) {
      ElMessage.success('删除成功')
      fetchHistory()
    } else {
      ElMessage.error(res.data.msg)
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败：', error)
      ElMessage.error('删除异常，请稍后重试')
    }
  }
}
</script>

<style scoped>
/* 全局样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

/* 主容器样式 */
.container {
  max-width: 1920px;
  margin: 0 auto;
  padding: 20px;
  background: transparent;
  min-height: 100vh;
}

/* 主要内容区域 */
.main-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 通用卡片样式 - 玻璃拟态科技风 */
.card {
  border-radius: 12px;
  background: rgba(10, 25, 50, 0.75) !important;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(64, 224, 208, 0.2) !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) !important;
  transition: all 0.3s ease;
  overflow: hidden;
}

.card:hover {
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.6) !important;
  border-color: rgba(64, 224, 208, 0.4) !important;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: rgba(0, 0, 0, 0.2);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.card-title {
  font-size: 20px;
  font-weight: 600;
  color: #40e0d0;
  display: flex;
  align-items: center;
  gap: 8px;
  text-shadow: 0 0 10px rgba(64, 224, 208, 0.3);
}

/* 视频区域样式 */
.video-card {
  padding: 0;
}

.video-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  padding: 20px;
}

.monitor-display {
  display: inline-block;
  margin-bottom: 10px;
  vertical-align: top;
}

.monitor-label:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  border-color: #409eff;
}

.monitor-label {
  text-align: center;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 5px;
  background-color: #f8fafc;
  transition: all 0.3s ease;
  display: flex;
  justify-content: center;
  align-items: center;
  font-family: "Microsoft YaHei", "PingFang SC", "Helvetica Neue", Arial, sans-serif;
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  letter-spacing: 0.5px;
  line-height: 1.0;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

/* 视频容器：开启横向滚动，禁止换行 */
.video-container {
  display: flex;
  flex-wrap: nowrap;
  gap: 16px;
  padding: 20px;
  width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
  box-sizing: border-box;
}
.video-container::-webkit-scrollbar {
  height: 8px;
}
.video-container::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 4px;
}
.video-container::-webkit-scrollbar-track {
  background: #f1f5f9;
}

/* 子元素：固定宽度 */
.monitor-item {
  flex: 0 0 24%;
  min-width: 280px;
  max-width: 320px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.monitor-label {
  width: 100%;
  text-align: center;
  border: 1px solid rgba(64, 224, 208, 0.3);
  border-radius: 8px;
  padding: 8px;
  background-color: rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;
  font-size: 16px;
  font-weight: 600;
  color: #e0e6ed;
  cursor: pointer;
}

.monitor-label:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(64, 224, 208, 0.2);
  border-color: #40e0d0;
  color: #40e0d0;
}

.video-item {
  width: 100%;
  border: 1px solid rgba(64, 224, 208, 0.2);
  border-radius: 8px;
  padding: 12px;
  background-color: rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;
}

.video-placeholder {
  width: 100%;
  aspect-ratio: 16/9;
  overflow: hidden;
  border-radius: 8px;
  background-color: #000;
  position: relative;
}

.video_style {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 气体等级划分区域 */
.level-card {
  padding: 0;
}

.gas-tabs {
  padding: 20px 20px 0;
}

.radio-group {
  display: flex;
  gap: 4px;
  background-color: #f8fafc;
  padding: 8px;
  border-radius: 8px;
}

:deep(.radio-group .el-radio-button__inner) {
  border-radius: 6px !important;
  padding: 8px 20px;
}

.table-container {
  padding: 20px;
  overflow-x: auto;
}

.level-table {
  --el-table-row-hover-bg-color: #f1f5f9;
  font-size: 14px;
  border-radius: 8px;
  overflow: hidden;
}

:deep(.level-table .el-table__header) {
  background-color: #f8fafc;
}

:deep(.level-table .el-table__cell) {
  padding: 14px 12px;
  border-bottom: 1px solid #e2e8f0;
}

.cell-content {
  line-height: 1.6;
}

/* 预警色标签样式 */
.color-tag {
  width: 80px;
  height: 32px;
  line-height: 32px;
  text-align: center;
  border-radius: 6px;
  font-weight: 600;
  color: white;
}

.color-tag.danger {
  background-color: #e53e3e;
  box-shadow: 0 2px 4px rgba(229, 62, 62, 0.3);
}

.color-tag.warning {
  background-color: #ed8936;
  box-shadow: 0 2px 4px rgba(237, 137, 54, 0.3);
}

.color-tag.primary {
  background-color: #ecc94b;
  color: #2d3748;
  box-shadow: 0 2px 4px rgba(236, 201, 75, 0.3);
}

.color-tag.info {
  background-color: #718096;
  box-shadow: 0 2px 4px rgba(113, 128, 150, 0.3);
}

/* ========== 优化后的预警历史记录样式 ========== */
.history-card {
  padding: 0;
}

.history-table {
  --el-table-bg-color: transparent !important;
  --el-table-tr-bg-color: transparent !important;
  --el-table-row-hover-bg-color: rgba(64, 224, 208, 0.1) !important;
  --el-table-border-color: rgba(66, 58, 58, 0.1) !important;
  font-size: 14px;
  border-radius: 8px;
  overflow: hidden;
  color: #ffffff;
}

:deep(.el-table) {
  background-color: transparent !important;
}

:deep(.el-table th.el-table__cell) {
  background-color: rgba(171, 42, 42, 0.3) !important;
  color: #40e0d0 !important;
  border-bottom: 1px solid rgba(135, 117, 126, 0.3) !important;
}

:deep(.el-table td.el-table__cell) {
  border-bottom: 1px solid rgba(142, 163, 137, 0.1) !important;
}


:deep(.el-table__row:nth-child(even)) {
  background: rgba(255,255,255,0.9) !important;
  color: #000 !important;
}
:deep(.el-table__row:nth-child(odd)) {
  background: rgba(0,0,0,0.15) !important;
  color: #fff !important;
}

:deep(.level-danger) {
  background-color: rgba(229, 62, 62, 0.1) !important;
}
:deep(.level-warning) {
  background-color: rgba(237, 137, 54, 0.1) !important;
}
:deep(.level-primary) {
  background-color: rgba(236, 201, 75, 0.1) !important;
}
:deep(.level-info) {
  background-color: rgba(113, 128, 150, 0.1) !important;
}

.gas-tag {
  border-radius: 4px;
  font-weight: 500;
  color: #000000 !important;
}

.concentration-text {
  font-weight: 600;
  color: #bda9a9;
  font-size: 14px;
}

.level-tag {
  width: 100px;
  height: 32px;
  line-height: 32px;
  text-align: center;
  border-radius: 6px;
  font-weight: 600;
  color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.level-tag.danger {
  background: linear-gradient(135deg, #e53e3e 0%, #c53030 100%);
}

.level-tag.warning {
  background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%);
}

.level-tag.primary {
  background: linear-gradient(135deg, #ecc94b 0%, #d69e2e 100%);
  color: #2d3748;
}

.level-tag.info {
  background: linear-gradient(135deg, #718096 0%, #4a5568 100%);
}

.delete-btn {
  border-radius: 6px;
  padding: 6px 16px;
  font-weight: 500;
  transition: all 0.2s ease;
  background: linear-gradient(90deg, #ff4d4f, #ff7875);
  border: none;
  color: #fff;
  box-shadow: 0 2px 8px rgba(255, 77, 79, 0.4);
}

:deep(.delete-btn:hover) {
  transform: translateY(-2px);
  background: linear-gradient(90deg, #ff7875, #ff4d4f);
  box-shadow: 0 4px 12px rgba(255, 77, 79, 0.6);
  color: #fff;
}

/* 图表样式 */
.chart-card {
  margin: 0 20px 20px;
  padding: 15px;
}
.chart-item {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.chart-title {
  font-size: 20px;
  font-weight: 600;
  color: #333;
}
.chart-box {
  width: 100%;
  height: 360px;
  margin: 0 auto;
}

/* 响应式适配 */
@media (max-width: 1400px) {
  .video-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .history-table {
    font-size: 13px;
  }
  .level-tag {
    width: 80px;
    height: 28px;
    line-height: 28px;
    font-size: 12px;
  }
}

@media (max-width: 768px) {
  .video-grid {
    grid-template-columns: 1fr;
  }
  .card-title {
    font-size: 16px;
  }
  :deep(.radio-group) {
    flex-wrap: wrap;
  }
  .color-tag {
    height: 28px;
    line-height: 28px;
    font-size: 12px;
  }
  .delete-btn {
    padding: 4px 12px;
    font-size: 12px;
  }
}

/* 视频区头部工具栏：搜索 + 新增 */
.header-toolbar {
  display: flex;
  gap: 10px;
  align-items: center;
}

/* 监测点删除按钮 */
.monitor-item {
  position: relative;
}
.delete-monitor {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10;
  color: #f56c6c;
  transition: 0.2s;
}
.delete-monitor:hover {
  background: #f56c6c;
  color: #fff;
}

.dialog-footer {
  text-align: right;
}
</style>
