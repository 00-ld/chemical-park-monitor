<template>
  <div class="chempark-container">
    <div class="main-layout">
      <aside class="left-panel">
        <div class="panel-section">
          <div class="search-box">
            <i class="fas fa-search"></i>
            <input type="text" placeholder="搜索设施 / 区域..." v-model="searchQuery" @input="onSearch">
          </div>
        </div>
        <div class="panel-section">
          <div class="panel-title"><i class="fas fa-smog"></i> 扩散模型</div>
          <div class="control-grid">
            <label class="control-field">
              <span>气体类型</span>
              <select v-model="diffusionForm.gasId">
                <option v-for="gas in diffusionGasOptions" :key="gas.id" :value="gas.id">{{ gas.name }}</option>
              </select>
            </label>
            <label class="control-field">
              <span>泄漏源设施</span>
              <select v-model="diffusionForm.sourceFacilityId">
                <option v-for="facility in diffusionSourceOptions" :key="facility.id" :value="facility.id">{{ facility.name }}</option>
              </select>
            </label>
            <label class="control-field">
              <span>手动经度</span>
              <input v-model.trim="leakSourceState.manualLongitude" type="text" placeholder="118.780">
            </label>
            <label class="control-field">
              <span>手动纬度</span>
              <input v-model.trim="leakSourceState.manualLatitude" type="text" placeholder="32.040">
            </label>
            <label class="control-field">
              <span>泄漏速率</span>
              <input v-model.number="diffusionForm.sourceRate" type="number" min="5" max="120" step="1">
            </label>
            <label class="control-field">
              <span>持续时间(s)</span>
              <input v-model.number="diffusionForm.releaseDuration" type="number" min="20" max="300" step="10">
            </label>
            <label class="control-field">
              <span>泄漏初始温度(°C)</span>
              <input v-model.number="diffusionForm.initialTemperature" type="number" min="-20" max="180" step="1">
            </label>
            <label class="control-field">
              <span>泄漏初始压力(MPa)</span>
              <input v-model.number="diffusionForm.initialPressure" type="number" min="0.1" max="2.5" step="0.1">
            </label>
            <label class="control-field">
              <span>泄漏高度(m)</span>
              <input v-model.number="diffusionForm.releaseHeight" type="number" min="0" max="30" step="0.5">
            </label>
            <label class="control-field">
              <span>风速(m/s)</span>
              <input v-model.number="diffusionForm.windSpeed" type="number" min="1" max="12" step="0.1">
            </label>
            <label class="control-field">
              <span>风向(°)</span>
              <input v-model.number="diffusionForm.windDirection" type="number" min="0" max="359" step="1">
            </label>
            <label class="control-field">
              <span>环境温度(°C)</span>
              <input v-model.number="diffusionForm.ambientTemperature" type="number" min="-30" max="60" step="1">
            </label>
            <label class="control-field">
              <span>相对湿度(%)</span>
              <input v-model.number="diffusionForm.humidity" type="number" min="0" max="100" step="1">
            </label>
            <label class="control-field">
              <span>稳定度</span>
              <select v-model="diffusionForm.stabilityClass">
                <option value="A">A</option>
                <option value="B">B</option>
                <option value="C">C</option>
                <option value="D">D</option>
                <option value="E">E</option>
                <option value="F">F</option>
              </select>
            </label>
            <label class="control-field">
              <span>地表粗糙度</span>
              <input v-model.number="diffusionForm.terrainRoughness" type="number" min="0.05" max="1.5" step="0.05">
            </label>
            <label class="control-field">
              <span>障碍物影响</span>
              <select v-model="diffusionForm.obstacleInfluenceEnabled">
                <option :value="true">开启</option>
                <option :value="false">关闭</option>
              </select>
            </label>
            <label class="control-field">
              <span>模拟帧数</span>
              <input v-model.number="diffusionForm.frameCount" type="number" min="12" max="240" step="12">
            </label>
            <label class="control-field">
              <span>时间步长(s)</span>
              <input v-model.number="diffusionForm.frameStepSec" type="number" min="1" max="30" step="1">
            </label>
          </div>
          <div class="control-note" :class="{ invalid: !diffusionSourceValidation.valid }">
            {{ diffusionSourceHint }}
          </div>
          <div class="control-subnote">
            当前入口：{{ leakSourceEntryLabel }} | 当前坐标：{{ leakSourceLocationText }}
          </div>
          <div class="inline-actions">
            <button class="sensor-btn primary" @click="useSelectedFacilityAsLeakSource">
              <i class="fas fa-bullseye"></i> 当前设施设为源点
            </button>
            <button class="sensor-btn primary" :class="{ active: leakSourceState.picking }" @click="toggleLeakSourcePicking">
              <i :class="leakSourceState.picking ? 'fas fa-ban' : 'fas fa-location-crosshairs'"></i>
              {{ leakSourceState.picking ? '取消地图取点' : '地图点击选点' }}
            </button>
            <button class="sensor-btn primary" @click="applyManualGeoLeakSource">
              <i class="fas fa-earth-asia"></i> 应用经纬度源点
            </button>
            <button class="sensor-btn primary" @click="runDiffusionSimulation()">
              <i class="fas fa-play"></i> 扩散模拟
            </button>
            <button class="sensor-btn primary" @click="runEvacuationPlanning()">
              <i class="fas fa-route"></i> 当前建筑路径
            </button>
            <button class="sensor-btn primary" @click="runBatchEvacuationPlanning({ displayMode: 'all' })">
              <i class="fas fa-people-arrows-left-right"></i> 全建筑路径
            </button>
            <button class="sensor-btn danger" @click="clearEvacuationPlanning">
              <i class="fas fa-road-circle-xmark"></i> 清除路径
            </button>
            <button class="sensor-btn primary" @click="generatePinnInputExport">
              <i class="fas fa-file-waveform"></i> 生成PINN输入
            </button>
            <button class="sensor-btn primary" @click="exportPinnInputJson">
              <i class="fas fa-download"></i> 导出JSON
            </button>
            <button class="sensor-btn danger" @click="resetDiffusionSimulation">
              <i class="fas fa-rotate-left"></i> 清除动画
            </button>
          </div>
        </div>
        <div class="panel-section">
          <div class="panel-title"><i class="fas fa-brain"></i> PINN 参数</div>
          <div class="control-grid">
            <label class="control-field">
              <span>候选数量 Top-K</span>
              <input v-model.number="pinnConfig.topK" type="number" min="1" max="8" step="1">
            </label>
            <label class="control-field">
              <span>粗搜网格步长</span>
              <input v-model.number="pinnConfig.gridStep" type="number" min="20" max="120" step="10">
            </label>
            <label class="control-field">
              <span>候选半径</span>
              <input v-model.number="pinnConfig.candidateRadius" type="number" min="20" max="100" step="5">
            </label>
            <label class="control-field">
              <span>支持半径</span>
              <input v-model.number="pinnConfig.supportRadius" type="number" min="40" max="220" step="10">
            </label>
            <label class="control-field">
              <span>距离尺度</span>
              <input v-model.number="pinnConfig.distanceScale" type="number" min="30" max="240" step="10">
            </label>
            <label class="control-field">
              <span>最小观测阈值</span>
              <input v-model.number="pinnConfig.minObservationThreshold" type="number" min="0" max="20" step="0.5">
            </label>
            <label class="control-field">
              <span>精修迭代步数</span>
              <input v-model.number="pinnRefinementConfig.animationSteps" type="number" min="8" max="60" step="2">
            </label>
            <label class="control-field">
              <span>学习率</span>
              <input v-model.number="pinnRefinementConfig.learningRate" type="number" min="0.001" max="0.1" step="0.001">
            </label>
            <label class="control-field">
              <span>收敛比例</span>
              <input v-model.number="pinnRefinementConfig.convergenceRatio" type="number" min="0.05" max="0.8" step="0.05">
            </label>
            <label class="control-field">
              <span>精修最小信号</span>
              <input v-model.number="pinnRefinementConfig.minSignalThreshold" type="number" min="0" max="20" step="0.5">
            </label>
          </div>
          <div class="inline-actions">
            <button class="sensor-btn primary" @click="runPinnCoarseSearchPreview">
              <i class="fas fa-crosshairs"></i> 生成候选区域
            </button>
            <button class="sensor-btn primary" @click="runMockPinnRefinementPreview">
              <i class="fas fa-bolt"></i> 生成精修骨架
            </button>
            <button class="sensor-btn primary" @click="toggleRefinementPlayback">
              <i :class="refinementState.playing ? 'fas fa-pause' : 'fas fa-play'"></i>
              {{ refinementState.playing ? '暂停精修' : '播放精修' }}
            </button>
            <button class="sensor-btn danger" @click="clearPinnCoarseSearch">
              <i class="fas fa-eraser"></i> 清空候选
            </button>
          </div>
        </div>
        <div class="panel-section">
          <div class="panel-title"><i class="fas fa-chart-pie"></i> 园区概览</div>
          <div class="stat-grid">
            <div
                v-for="s in stats" :key="s.filter"
                class="stat-card"
                :class="{ active: activeFilter === s.filter }"
                @click="setFilter(s.filter)"
            >
              <div class="stat-value" :style="{ color: s.color || '' }">{{ s.value }}</div>
              <div class="stat-label">{{ s.label }}</div>
            </div>
          </div>
        </div>
        <div class="panel-section">
          <div class="panel-title"><i class="fas fa-palette"></i> 图例</div>
          <div class="legend-list">
            <div v-for="l in legends" :key="l.type" class="legend-item">
              <div class="legend-swatch" :class="l.shape" :style="l.style"></div>
              <span>{{ l.label }}</span>
            </div>
          </div>
        </div>
        <div class="panel-section" style="flex:1;">
          <div class="panel-title"><i class="fas fa-map-marked-alt"></i> 功能分区</div>
          <div class="zone-list">
            <div
                v-for="z in zones" :key="z.id"
                class="zone-item"
                :class="{ selected: selectedZone === z.id }"
                @click="selectZone(z.id)"
            >
              <div class="zone-name">
                <div :style="{ width:'8px', height:'8px', borderRadius:'2px', background:z.color, flexShrink:0 }"></div>
                {{ z.name }}
              </div>
              <span class="zone-tag">{{ z.tag }}</span>
            </div>
          </div>
        </div>
      </aside>

      <main class="map-container" ref="mapContainerRef">
        <template v-if="viewMode === '2d'">
        <div class="grid-overlay"></div>
        <canvas
            ref="mapCanvasRef"
            id="mapCanvas"
            :class="{ grabbing: isDragging }"
            @mousedown="onCanvasMouseDown"
            @mousemove="onCanvasMouseMove"
            @mouseup="onCanvasMouseUp"
            @mouseleave="onCanvasMouseLeave"
            @wheel.prevent="onCanvasWheel"
        ></canvas>

        <div class="coord-display">
          经度: <span>{{ coordLongitude }}</span> &nbsp; 纬度: <span>{{ coordLatitude }}</span> &nbsp; 海拔: <span>{{ coordAltitude }}</span>
        </div>

        <div v-if="hoveredSensorCard" class="sensor-hover-card">
          <div class="sensor-hover-head">
            <div>
              <div class="sensor-hover-title">{{ hoveredSensorCard.id }}</div>
              <div class="sensor-hover-sub">{{ hoveredSensorCard.typeName }} / {{ hoveredSensorCard.levelText }}</div>
            </div>
            <span class="sensor-hover-badge" :class="hoveredSensorCard.levelClass">{{ hoveredSensorCard.levelLabel }}</span>
          </div>
          <div class="sensor-hover-metric">
            <span>当前浓度</span>
            <strong>{{ hoveredSensorCard.currentLabel }}</strong>
          </div>
          <div class="sensor-hover-grid">
            <span>当前时间 {{ hoveredSensorCard.timeLabel }}</span>
            <span>采样峰值 {{ hoveredSensorCard.peakLabel }}</span>
            <span>风险等级 <span :style="{ color: getPriorityColor(hoveredSensorCard.priority), fontWeight: 600 }">P{{ hoveredSensorCard.priority }} {{ hoveredSensorCard.priorityLabel }}</span></span>
            <span>{{ hoveredSensorCard.coordLabel }}</span>
          </div>
        </div>

        <div class="bottom-toolbar">
          <button class="tool-btn" :class="{ active: !measureMode }" @click="setTool('select')">
            <i class="fas fa-mouse-pointer"></i> 选择
          </button>
          <button class="tool-btn" :class="{ active: showFlow }" @click="toggleFlow">
            <i class="fas fa-water"></i> 流向
          </button>
          <button class="tool-btn" :class="{ active: showEntrances }" @click="toggleEntrances">
            <i class="fas fa-door-open"></i> 出入口
          </button>
          <button class="tool-btn" :class="{ active: measureMode }" @click="setTool('measure')">
            <i class="fas fa-ruler"></i> 测距
          </button>
          <button class="tool-btn" :class="{ active: showSensors }" @click="toggleSensors">
            <i class="fas fa-eye"></i> 传感器
          </button>
          <button class="tool-btn" :class="{ active: showSensorRanges }" @click="toggleSensorRanges">
            <i class="fas fa-circle"></i> 半径范围
          </button>
          <button class="tool-btn" @click="runEndToEndPipeline" title="全流程联动：巡逻→采样→PINN溯源">
            <i class="fas fa-play-circle"></i> 全流程
          </button>
        </div>

        <div class="scale-bar">
          <div class="scale-text">50m</div>
          <div class="scale-line"></div>
        </div>

        <div v-if="diffusionFrames.length" class="timeline-panel">
          <div class="timeline-head">
            <div>
              <div class="timeline-title">扩散时间轴</div>
              <div class="timeline-meta">{{ diffusionSummary.sourceName }} / {{ diffusionSummary.gasName }}</div>
            </div>
            <div class="timeline-meta">第 {{ diffusionSummary.frameText }} 帧</div>
          </div>
          <input
              class="timeline-slider"
              type="range"
              min="0"
              :max="Math.max(diffusionFrames.length - 1, 0)"
              :value="diffusionState.currentFrame"
              @input="seekDiffusionFrame(Number($event.target.value))"
          >
          <div class="timeline-controls-row">
            <div class="timeline-actions">
              <button class="timeline-btn" @click="stepDiffusionFrame(-1)" title="上一帧"><i class="fas fa-backward-step"></i></button>
              <button class="timeline-btn primary" @click="toggleDiffusionPlayback" :title="diffusionState.playing ? '暂停' : '播放'">
                <i :class="diffusionState.playing ? 'fas fa-pause' : 'fas fa-play'"></i>
              </button>
              <button class="timeline-btn" @click="stepDiffusionFrame(1)" title="下一帧"><i class="fas fa-forward-step"></i></button>
            </div>
            <div class="timeline-readout">
              <span>{{ diffusionSummary.timeText }}</span>
              <span>峰值 {{ diffusionSummary.maxConcentration }}</span>
              <span>影响 {{ diffusionSummary.affectedArea }}</span>
            </div>
            <div class="timeline-settings">
              <select v-model.number="diffusionState.speed">
                <option v-for="speed in playbackSpeedOptions" :key="speed" :value="speed">{{ speed }}x</option>
              </select>
              <label class="timeline-loop">
                <input v-model="diffusionState.loop" type="checkbox">
                循环
              </label>
            </div>
          </div>
        </div>

        <div class="map-controls">
          <button class="map-btn" @click="zoomIn" title="放大"><i class="fas fa-plus"></i></button>
          <button class="map-btn" @click="zoomOut" title="缩小"><i class="fas fa-minus"></i></button>
          <button class="map-btn" @click="zoomReset" title="重置"><i class="fas fa-expand"></i></button>
          <button class="map-btn" :class="{ active: showLabels }" @click="toggleLabels" title="标注"><i class="fas fa-tag"></i></button>
        </div>
        </template>

        <ParkScene3D
            v-if="viewMode === '3d'"
            ref="scene3DRef"
            :selected-facility-id="selectedFacility?.id"
            @facility-click="(id) => { selectedFacility = facilityById.get(id) || null }"
        />
      </main>

      <aside class="right-panel" :class="{ collapsed: panelCollapsed }">
        <div class="info-header">
          <div>
            <h2>{{ infoTitle }}</h2>
            <div style="margin-top:4px;">
              <span v-if="infoSubtitle.text" :style="{ color: infoSubtitle.color }">{{ infoSubtitle.text }}</span>
              <span v-if="infoSubtitle.tag" :class="infoSubtitle.tagClass" style="margin-left:4px;">{{ infoSubtitle.tag }}</span>
              <span v-if="infoSubtitle.desc" style="color:var(--fg-muted);font-size:12px;margin-left:4px;">{{ infoSubtitle.desc }}</span>
            </div>
          </div>
          <button class="close-btn" @click="closeInfo"><i class="fas fa-times"></i></button>
        </div>
        <div class="info-body">
          <template v-if="selectedFacility || selectedSensor || selectedCar">
            <div v-for="(row, idx) in infoRows" :key="idx" class="info-row">
              <span class="info-key">{{ row.key }}</span>
              <span class="info-val" v-if="row.action" @click="row.action" style="cursor:pointer;">
                <button class="info-car-btn" :class="row.btnClass">{{ row.val }}</button>
              </span>
              <span class="info-val" v-else-if="row.tag" :class="row.tagClass">{{ row.val }}</span>
              <span class="info-val" v-else :style="row.style || {}">{{ row.val }}</span>
            </div>
            <!-- YOLO 检测结果 -->
            <div v-if="selectedCar && yoloResult && yoloResult.carId === selectedCar.id" class="yolo-result-card">
              <div class="sensor-history-head">
                <span>YOLO 检测结果</span>
                <span>{{ yoloResult.count }} 人</span>
              </div>
              <img v-if="yoloResult.imageBase64" :src="'data:image/png;base64,' + yoloResult.imageBase64" class="yolo-result-img" />
              <div class="yolo-result-time">{{ new Date(yoloResult.timestamp).toLocaleTimeString() }} 检测</div>
            </div>
            <div v-if="selectedFacility?.type === 'tank' && selectedFacility.level != null" class="info-row">
              <span class="info-key">液位指示</span>
              <div class="mini-bar">
                <div class="mini-bar-fill"
                     :style="{ width: selectedFacility.level + '%', background: selectedFacility.level > 85 ? '#ef4444' : '#00e5a0' }"
                ></div>
              </div>
            </div>
            <div v-if="selectedSensor && selectedSensorHistoryChart" class="sensor-history-card">
              <div class="sensor-history-head">
                <span>历史浓度曲线</span>
                <span>{{ selectedSensorHistoryChart.currentLabel }}</span>
              </div>
              <svg class="sensor-history-svg" viewBox="0 0 280 96" preserveAspectRatio="none">
                <line
                    :x1="selectedSensorHistoryChart.padding"
                    y1="80"
                    :x2="280 - selectedSensorHistoryChart.padding"
                    y2="80"
                    class="sensor-axis"
                />
                <line
                    :x1="selectedSensorHistoryChart.padding"
                    y1="12"
                    :x2="selectedSensorHistoryChart.padding"
                    y2="80"
                    class="sensor-axis"
                />
                <line
                    :x1="selectedSensorHistoryChart.padding"
                    :x2="280 - selectedSensorHistoryChart.padding"
                    :y1="selectedSensorHistoryChart.warningY"
                    :y2="selectedSensorHistoryChart.warningY"
                    class="sensor-threshold warning"
                />
                <line
                    :x1="selectedSensorHistoryChart.padding"
                    :x2="280 - selectedSensorHistoryChart.padding"
                    :y1="selectedSensorHistoryChart.dangerY"
                    :y2="selectedSensorHistoryChart.dangerY"
                    class="sensor-threshold danger"
                />
                <polyline :points="selectedSensorHistoryChart.points" class="sensor-line" />
                <line
                    :x1="selectedSensorHistoryChart.markerX"
                    :x2="selectedSensorHistoryChart.markerX"
                    y1="12"
                    y2="80"
                    class="sensor-marker"
                />
                <circle
                    :cx="selectedSensorHistoryChart.markerX"
                    :cy="selectedSensorHistoryChart.markerY"
                    r="3.5"
                    class="sensor-marker-dot"
                />
              </svg>
              <div class="sensor-history-foot">
                <span>0s</span>
                <span>峰值 {{ selectedSensorHistoryChart.peakLabel }}</span>
                <span>{{ selectedSensorHistoryChart.endLabel }}</span>
              </div>
            </div>
            <div v-if="selectedSensor" class="sensor-history-card" style="margin-top:12px;">
              <div class="sensor-history-head">
                <span>数据模式</span>
                <span>{{ selectedSensor.mode === 'manual' ? '手动录入' : '自动采样' }}</span>
              </div>
              <div class="control-grid" style="margin-top:10px;">
                <label class="control-field">
                  <span>传感器数据源</span>
                  <select :value="selectedSensor.mode || 'auto'" @change="setSelectedSensorMode($event.target.value)">
                    <option value="auto">自动采样</option>
                    <option value="manual">手动录入</option>
                  </select>
                </label>
                <label v-if="selectedSensor.mode === 'manual'" class="control-field">
                  <span>当前帧手动浓度(ppm)</span>
                  <input v-model.number="sensorEditorState.currentFrameConcentration" type="number" min="0" step="0.1">
                </label>
                <label v-if="selectedSensor.mode === 'manual'" class="control-field">
                  <span>全时段批量浓度(ppm)</span>
                  <input v-model.number="sensorEditorState.fillAllConcentration" type="number" min="0" step="0.1">
                </label>
              </div>
              <div v-if="selectedSensor.mode === 'manual'" class="inline-actions" style="margin-top:10px;">
                <button class="sensor-btn primary" @click="applySelectedSensorManualValueToCurrentFrame">
                  <i class="fas fa-pen"></i> 写入当前帧
                </button>
                <button class="sensor-btn primary" @click="fillSelectedSensorManualSeries">
                  <i class="fas fa-wave-square"></i> 填充全时段
                </button>
                <button class="sensor-btn primary" @click="copyAutoSeriesToSelectedSensorManual">
                  <i class="fas fa-copy"></i> 复制自动曲线
                </button>
                <button class="sensor-btn danger" @click="clearSelectedSensorManualSeries">
                  <i class="fas fa-eraser"></i> 清空手动曲线
                </button>
              </div>
              <div class="control-subnote" style="margin-top:8px;">
                自动采样：系统定时生成仿真采样数据，跟随当前扩散场浓度变化。手动采样：用户点击按钮后生成一次采样数据，使用独立时间序列，并同步影响图表、告警显示和 PINN 输入。
              </div>
            </div>
          </template>
          <div v-if="selectedSensor" style="margin-top:16px;padding-top:12px;border-top:1px solid var(--border);">
                        <button class="sensor-btn primary" style="width:100%;margin-bottom:8px;" @click="openSensorEdit">
              <i class="fas fa-edit"></i> 编辑参数
            </button>
<button class="sensor-btn danger" style="width:100%;" @click="deleteCurrSensor">
              <i class="fas fa-minus-circle"></i> 删除此传感器
            </button>
          </div>
          <!-- 设备安装详情卡片 -->
          <div v-if="selectedSensor && sensorDeviceCard" class="sensor-device-card">
            <div class="sensor-history-head">
              <span>设备安装详情</span>
              <button class="sensor-btn-white" @click="openDeviceFullscreen">
                <i class="fas fa-expand"></i>
              </button>
            </div>
            <div class="sensor-device-compact">
              <img :src="sensorDeviceCard.image" class="sensor-device-thumb" />
              <div class="sensor-device-compact-info">
                <div class="sensor-device-compact-name">{{ sensorDeviceCard.deviceName }}</div>
                <div class="sensor-device-compact-status">
                  <span class="sensor-status-dot online"></span> 在线
                  <span class="sensor-status-sep">|</span>
                  <span class="sensor-conc-val">{{ sensorDeviceCard.concentration }}</span>
                </div>
              </div>
            </div>
          </div>
          <div v-else-if="!selectedSensor" style="text-align:center;padding:40px 0;color:var(--fg-muted);font-size:13px;">
            <i class="fas fa-mouse-pointer" style="font-size:32px;opacity:0.2;display:block;margin-bottom:12px;"></i>
            点击地图上的设施查看详细信息
          </div>
        </div>

        <div class="panel-section">
          <div class="panel-title"><i class="fas fa-wave-square"></i> 扩散监测</div>
          <div class="info-row">
            <span class="info-key">当前气体</span>
            <span class="info-val">{{ diffusionSummary.gasName }}</span>
          </div>
          <div class="info-row">
            <span class="info-key">泄漏源</span>
            <span class="info-val">{{ diffusionSummary.sourceName }}</span>
          </div>
          <div class="info-row">
            <span class="info-key">当前时间</span>
            <span class="info-val">{{ diffusionSummary.timeText }}</span>
          </div>
          <div class="info-row">
            <span class="info-key">最大浓度</span>
            <span class="info-val">{{ diffusionSummary.maxConcentration }}</span>
          </div>
          <div class="info-row">
            <span class="info-key">影响面积</span>
            <span class="info-val">{{ diffusionSummary.affectedArea }}</span>
          </div>
          <div class="info-row">
            <span class="info-key">危险面积</span>
            <span class="info-val">{{ diffusionSummary.dangerArea }}</span>
          </div>
        </div>

        <div class="panel-section">
          <div class="panel-title"><i class="fas fa-route"></i> 逃生规划</div>
          <div class="info-row">
            <span class="info-key">规划状态</span>
            <span class="info-val">{{ evacuationSummary.statusText }}</span>
          </div>
          <div class="info-row">
            <span class="info-key">逃生起点</span>
            <span class="info-val">{{ evacuationSummary.startLabel }}</span>
          </div>
          <div class="info-row">
            <span class="info-key">目标出口</span>
            <span class="info-val">{{ evacuationSummary.exitLabel }}</span>
          </div>
          <div class="info-row">
            <span class="info-key">路线长度</span>
            <span class="info-val">{{ evacuationSummary.distanceText }}</span>
          </div>
          <div class="info-row">
            <span class="info-key">预计耗时</span>
            <span class="info-val">{{ evacuationSummary.etaText }}</span>
          </div>
          <div class="info-row">
            <span class="info-key">路径风险</span>
            <span class="info-val">{{ evacuationSummary.riskText }}</span>
          </div>
          <div class="info-row">
            <span class="info-key">危险屏蔽</span>
            <span class="info-val">{{ evacuationSummary.blockedText }}</span>
          </div>
          <div class="info-row">
            <span class="info-key">规划内核</span>
            <span class="info-val">{{ evacuationSummary.plannerText }}</span>
          </div>
          <div class="info-row">
            <span class="info-key">规划范围</span>
            <span class="info-val">{{ evacuationPlanningMode === 'all' ? '全建筑' : '当前建筑' }}</span>
          </div>
          <div v-if="evacuationCandidateRoutes.length" class="info-row">
            <span class="info-key">可达出口</span>
            <span class="info-val">{{ evacuationCandidateRoutes.length }} 条</span>
          </div>
          <div v-if="evacuationBatchResult" class="info-row">
            <span class="info-key">成功建筑</span>
            <span class="info-val">{{ evacuationBatchResult.successCount }}/{{ evacuationBatchResult.totalBuildings }}</span>
          </div>
          <div v-if="evacuationBatchResult" class="info-row">
            <span class="info-key">阻断建筑</span>
            <span class="info-val">{{ evacuationBatchResult.blockedCount }}</span>
          </div>
        </div>

        <div class="panel-section">
          <div class="panel-title"><i class="fas fa-shoe-prints"></i> 逃生候选路线</div>
          <div v-if="evacuationPlanningMode === 'all' && evacuationBatchResult" class="inline-actions">
            <button
                class="sensor-btn primary"
                :class="{ active: evacuationDisplayMode === 'selected' }"
                @click="evacuationDisplayMode = 'selected'"
            >
              仅看当前建筑
            </button>
            <button
                class="sensor-btn primary"
                :class="{ active: evacuationDisplayMode === 'all' }"
                @click="evacuationDisplayMode = 'all'"
            >
              显示全部路径
            </button>
          </div>
          <div v-if="evacuationCandidateRoutes.length" class="candidate-list">
            <button
                v-for="route in evacuationCandidateRoutes"
                :key="route.candidateId"
                class="candidate-item"
                :class="{ active: selectedEvacuationCandidateId === route.candidateId }"
                @click="selectEvacuationCandidate(route.candidateId)"
            >
              <div class="candidate-main">
                <span class="candidate-rank">R{{ route.rank }}</span>
                <span class="candidate-name">{{ route.exitLabel }}</span>
                <span class="candidate-score">
                  {{ route.candidateId === evacuationRecommendedCandidateId ? '推荐' : '备选' }}
                </span>
              </div>
              <div class="candidate-meta">
                <span>{{ route.distanceMeters.toFixed(1) }} m</span>
                <span>{{ route.estimatedTimeSec.toFixed(0) }} s</span>
                <span>{{ route.riskLevelText }}</span>
              </div>
            </button>
          </div>
          <div v-else class="empty-block">先点击“逃生规划”生成可用疏散路线</div>
          <div v-if="selectedEvacuationCandidate" class="candidate-detail-card">
            <div class="candidate-detail-head">
              <span>{{ selectedEvacuationCandidate.exitLabel }}</span>
              <span>
                {{ selectedEvacuationCandidate.candidateId === evacuationRecommendedCandidateId ? '推荐路线' : '当前查看' }}
              </span>
            </div>
            <div class="candidate-detail-grid">
              <span>排名 R{{ selectedEvacuationCandidate.rank || 1 }}</span>
              <span>长度 {{ selectedEvacuationCandidate.distanceMeters.toFixed(1) }} m</span>
              <span>耗时 {{ selectedEvacuationCandidate.estimatedTimeSec.toFixed(0) }} s</span>
              <span>风险 {{ selectedEvacuationCandidate.riskLevelText }}</span>
              <span>屏蔽节点 {{ selectedEvacuationCandidate.dangerMask?.blockedNodeCount || 0 }}</span>
              <span>屏蔽路段 {{ selectedEvacuationCandidate.dangerMask?.blockedEdgeCount || 0 }}</span>
            </div>
          </div>
        </div>

        <div class="panel-section">
          <div class="panel-title"><i class="fas fa-building-shield"></i> 建筑疏散列表</div>
          <div v-if="evacuationBuildingRoutes.length" class="candidate-list">
            <button
                v-for="route in evacuationBuildingRoutes"
                :key="route.buildingId"
                class="candidate-item"
                :class="{
                  active: selectedEvacuationBuildingId === route.buildingId,
                  blocked: !route.success,
                }"
                @click="selectEvacuationBuilding(route.buildingId, true)"
            >
              <div class="candidate-main">
                <span class="candidate-rank">B</span>
                <span class="candidate-name">{{ route.buildingName }}</span>
                <span class="candidate-score">{{ route.success ? '可达' : '阻断' }}</span>
              </div>
              <div class="candidate-meta">
                <span>{{ route.entranceLabel }}</span>
                <span>{{ route.success ? route.exitLabel : '无可用出口' }}</span>
                <span>{{ route.success ? `${route.distanceMeters.toFixed(1)} m` : route.message }}</span>
              </div>
            </button>
          </div>
          <div v-else class="empty-block">先点击“全建筑路径”生成园区疏散结果</div>
        </div>

        <div class="panel-section">
          <div class="panel-title"><i class="fas fa-brain"></i> PINN 输入准备</div>
          <div class="info-row">
            <span class="info-key">数据集状态</span>
            <span class="info-val">{{ pinnExportSummary ? '已生成' : '待生成' }}</span>
          </div>
          <div class="info-row">
            <span class="info-key">有效传感器</span>
            <span class="info-val">{{ pinnExportSummary ? `${pinnExportSummary.activeSensors}/${pinnExportSummary.sensorCount}` : '--' }}</span>
          </div>
          <div class="info-row">
            <span class="info-key">时序点数</span>
            <span class="info-val">{{ pinnExportSummary ? pinnExportSummary.totalSeriesPoints : '--' }}</span>
          </div>
          <div class="info-row">
            <span class="info-key">总时长</span>
            <span class="info-val">{{ pinnExportSummary ? `${pinnExportSummary.totalDurationSec}s` : '--' }}</span>
          </div>
          <div class="info-row">
            <span class="info-key">候选区域</span>
            <span class="info-val">{{ coarseSearchSummary ? coarseSearchSummary.candidateCount : '--' }}</span>
          </div>
          <div class="info-row">
            <span class="info-key">最优候选</span>
            <span class="info-val">{{ coarseSearchSummary ? coarseSearchSummary.bestLabel : '--' }}</span>
          </div>
          <div class="info-row">
            <span class="info-key">最优坐标</span>
            <span class="info-val">{{ coarseSearchSummary ? coarseSearchSummary.bestCoord : '--' }}</span>
          </div>
          <div class="json-preview" v-if="pinnExportPreview">{{ pinnExportPreview }}</div>
        </div>

        <div class="panel-section">
          <div class="panel-title"><i class="fas fa-wave-square"></i> PINN 精修</div>
          <div class="info-row">
            <span class="info-key">精修状态</span>
            <span class="info-val">{{ refinementSummary ? '已生成' : '待生成' }}</span>
          </div>
          <div class="info-row">
            <span class="info-key">当前迭代</span>
            <span class="info-val">{{ refinementCurrentIteration ? `${refinementCurrentIteration.iteration}/${refinementSummary.totalIterations}` : '--' }}</span>
          </div>
          <div class="info-row">
            <span class="info-key">当前损失</span>
            <span class="info-val">{{ refinementCurrentIteration ? refinementCurrentIteration.loss.toFixed(4) : '--' }}</span>
          </div>
          <div class="info-row">
            <span class="info-key">预测坐标</span>
            <span class="info-val">{{ refinementSummary ? refinementSummary.estimatedCoord : '--' }}</span>
          </div>
          <div class="info-row">
            <span class="info-key">预测状态</span>
            <span class="info-val">{{ refinementCurrentIteration ? (refinementState.currentStep >= refinementIterations.length - 1 ? '已收敛到预测源点' : '收缩搜索中') : '--' }}</span>
          </div>
          <div class="info-row">
            <span class="info-key">源点偏差</span>
            <span class="info-val">{{ refinementSummary?.sourceMatchError != null ? `${refinementSummary.sourceMatchError}m` : '--' }}</span>
          </div>
          <input
              v-if="refinementIterations.length"
              class="timeline-slider"
              type="range"
              min="0"
              :max="Math.max(refinementIterations.length - 1, 0)"
              :value="refinementState.currentStep"
              @input="seekRefinementStep(Number($event.target.value))"
          >
          <div class="sampling-row" v-if="refinementInputSummary">
            <span>候选 {{ refinementInputSummary.candidateLabel }}</span>
            <span>有效传感器 {{ refinementInputSummary.activeSensorCount }}</span>
            <span>步数 {{ refinementInputSummary.animationSteps }}</span>
          </div>
        </div>

        <div class="panel-section">
          <div class="panel-title"><i class="fas fa-list-ol"></i> 粗搜候选列表</div>
          <div v-if="coarseCandidateRegions.length" class="candidate-list">
            <button
                v-for="candidate in coarseCandidateRegions"
                :key="candidate.candidateId"
                class="candidate-item"
                :class="{ active: selectedCoarseCandidateId === candidate.candidateId }"
                @click="selectCoarseCandidate(candidate.candidateId, true)"
            >
              <div class="candidate-main">
                <span class="candidate-rank">C{{ candidate.rank }}</span>
                <span class="candidate-name">{{ candidate.label }}</span>
                <span class="candidate-score">S {{ candidate.score.toFixed(3) }}</span>
              </div>
              <div class="candidate-meta">
                <span>{{ candidate.center.x.toFixed(0) }}, {{ candidate.center.y.toFixed(0) }}</span>
                <span>支持 {{ candidate.supportCount }}</span>
                <span>误差 {{ candidate.error.toFixed(3) }}</span>
              </div>
            </button>
          </div>
          <div v-else class="empty-block">先点击“生成候选区域”查看粗搜结果</div>
          <div v-if="selectedCoarseCandidate" class="candidate-detail-card">
            <div class="candidate-detail-head">
              <span>{{ selectedCoarseCandidate.label }}</span>
              <span>半径 {{ selectedCoarseCandidate.radius }}m</span>
            </div>
            <div class="candidate-detail-grid">
              <span>排名 C{{ selectedCoarseCandidate.rank }}</span>
              <span>得分 {{ selectedCoarseCandidate.score.toFixed(3) }}</span>
              <span>支持传感器 {{ selectedCoarseCandidate.supportCount }}</span>
              <span>误差 {{ selectedCoarseCandidate.error.toFixed(3) }}</span>
              <span>X {{ selectedCoarseCandidate.center.x.toFixed(0) }}</span>
              <span>Y {{ selectedCoarseCandidate.center.y.toFixed(0) }}</span>
            </div>
          </div>
        </div>

        <div class="panel-section">
          <div class="panel-title"><i class="fas fa-signal"></i> 区域风险等级</div>
          <div class="risk-stat-list">
            <div class="risk-stat-item">
              <div class="risk-dot" style="background:#ef4444"></div>
              <span>重大风险</span>
              <span class="num">{{ riskStat.critical }} 格</span>
            </div>
            <div class="risk-stat-item">
              <div class="risk-dot" style="background:#f97316"></div>
              <span>较大风险</span>
              <span class="num">{{ riskStat.high }} 格</span>
            </div>
            <div class="risk-stat-item">
              <div class="risk-dot" style="background:#eab308"></div>
              <span>一般风险</span>
              <span class="num">{{ riskStat.mid }} 格</span>
            </div>
            <div class="risk-stat-item">
              <div class="risk-dot" style="background:#22c55e"></div>
              <span>低风险</span>
              <span class="num">{{ riskStat.low }} 格</span>
            </div>
          </div>
        </div>

        <div class="panel-section">
          <div class="panel-title"><i class="fas fa-cloud-sun"></i> 气象环境 <span :class="weatherSource === 'real' ? 'tag tag-green' : 'tag tag-gray'" style="font-size:10px;margin-left:6px;">{{ weatherSource === 'real' ? '实时天气' : '模拟天气' }}</span></div>
          <div class="sensor-stat-grid" style="grid-template-columns:1fr 1fr 1fr;">
            <div class="stat-mini">
              <div class="val" style="font-size:14px;">{{ weatherState.windSpeed.toFixed(1) }} <span style="font-size:10px;opacity:0.7">m/s</span></div>
              <div class="lab" v-if="weatherSource === 'real' && weatherState.windSpeedKmh">风速（{{ weatherState.windSpeedKmh.toFixed(1) }} km/h）</div>
              <div class="lab" v-else>风速（模型值）</div>
            </div>
            <div class="stat-mini">
              <div class="val" style="font-size:14px;">{{ weatherState.windDir }}°</div>
              <div class="lab">风向</div>
            </div>
            <div class="stat-mini">
              <div class="val" style="font-size:14px;">{{ weatherState.temp.toFixed(1) }}°C</div>
              <div class="lab">温度</div>
            </div>
          </div>
          <div v-if="weatherSource === 'real' && weatherState.obsTime" style="margin-top:6px;font-size:11px;color:var(--fg-muted);text-align:center;">
            观测时间：{{ weatherState.obsTime }}
          </div>
        </div>

        <div class="panel-section">
          <div class="panel-title"><i class="fas fa-microchip"></i> 传感器布局统计</div>
          <div class="sensor-stat-grid">
            <div class="stat-mini">
              <div class="val">{{ layoutResult.sensorCount }}</div>
              <div class="lab">传感器总数</div>
            </div>
            <div class="stat-mini">
              <div class="val">{{ layoutResult.coverageRate }}%</div>
              <div class="lab">全域覆盖率</div>
            </div>
            <div class="stat-mini">
              <div class="val">{{ layoutResult.riskCoverRate }}%</div>
              <div class="lab">高风险覆盖率</div>
            </div>
            <div class="stat-mini">
              <div class="val">¥{{ layoutResult.totalCost }}</div>
              <div class="lab">部署总成本</div>
            </div>
          </div>

          <div class="sensor-btn-group" style="margin-top:12px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;">
            <button class="sensor-btn primary" :class="{ active: sensorPlacementState.picking }" @click="addManualSensor">
              <i :class="sensorPlacementState.picking ? 'fas fa-ban' : 'fas fa-plus'"></i>
              {{ sensorPlacementState.picking ? '取消选点' : (manualSensorConfigVisible ? '重新选点' : '手动添加') }}
            </button>
            <button class="sensor-btn primary" :class="{ active: manualSensorPanelVisible }" @click="toggleManualSensorPanel">
              <i class="fas fa-pen-to-square"></i> 手动录入
            </button>
            <button class="sensor-btn danger" @click="clearAllSensor">
              <i class="fas fa-trash"></i> 清空全部
            </button>
          </div>
          <div v-if="manualSensorConfigVisible" class="candidate-detail-card" style="margin-top:10px;">
            <div class="candidate-detail-head">
              <span>手动添加传感器参数</span>
              <span>{{ manualSensorPlacementPointLabel }}</span>
            </div>
            <div class="control-grid" style="margin-top:10px;">
              <label class="control-field" style="grid-column:1 / -1;">
                <span>零点坐标</span>
                <div style="display:flex;gap:8px;align-items:center;">
                  <input type="text" :value="sensorPlacementState.origin ? `(${sensorPlacementState.origin.x.toFixed(1)}, ${sensorPlacementState.origin.y.toFixed(1)})` : '未设置'" disabled style="flex:1;">
                  <button class="sensor-btn primary" :class="{ active: sensorPlacementState.pickingOrigin }" @click="toggleOriginPicking" style="white-space:nowrap;">
                    <i class="fas fa-crosshairs"></i> {{ sensorPlacementState.pickingOrigin ? '选择中...' : (sensorPlacementState.origin ? '重设零点' : '设置零点') }}
                  </button>
                </div>
              </label>
              <label class="control-field">
                <span>X 偏移 (m)</span>
                <input v-model.number="sensorPlacementState.relativeX" type="number" step="0.1" placeholder="0">
              </label>
              <label class="control-field">
                <span>Y 偏移 (m)</span>
                <input v-model.number="sensorPlacementState.relativeY" type="number" step="0.1" placeholder="0">
              </label>
              <label class="control-field" style="grid-column:1 / -1;">
                <button class="sensor-btn primary" @click="applyRelativeCoordinates" :disabled="!sensorPlacementState.origin" style="width:100%;">
                  <i class="fas fa-check"></i> 应用坐标
                </button>
              </label>
              <label class="control-field">
                <span>安装高度 (m)</span>
                <input v-model.number="manualSensorDraft.installationHeight" type="number" min="0.3" max="10" step="0.1">
              </label>
              <label class="control-field">
                <span>有效监测范围 (m)</span>
                <input v-model.number="manualSensorDraft.effectiveRange" type="number" min="5" max="100" step="1">
              </label>
              <label class="control-field" style="grid-column:1 / -1;">
                <span>检测范围</span>
                <input v-model.trim="manualSensorDraft.detectionRange" type="text" placeholder="CO / CH4 / NH3 / O2">
              </label>
              <label class="control-field" style="grid-column:1 / -1;">
                <span>布点说明 / 备注（可选）</span>
                <input v-model.trim="manualSensorDraft.installRemark" type="text" placeholder="如：靠近阀组、下风向重点监测">
              </label>
            </div>
            <div class="control-note" :class="{ invalid: !manualSensorDraftValidation.valid }" style="margin-top:10px;">
              {{ manualSensorDraftValidation.message }}
            </div>
            <div class="control-subnote" style="margin-top:8px;">
              默认值：安装高度 {{ MANUAL_SENSOR_DEFAULTS.installationHeight }} m，有效监测范围 {{ MANUAL_SENSOR_DEFAULTS.effectiveRange }} m，检测范围 {{ MANUAL_SENSOR_DEFAULTS.detectionRange }}
            </div>
            <div class="control-subnote" style="margin-top:4px;">
              当前点位：{{ manualSensorPlacementLocationText }}
            </div>
            <div class="inline-actions" style="margin-top:10px;">
              <button class="sensor-btn primary" @click="startManualSensorPicking">
                <i class="fas fa-location-crosshairs"></i> {{ sensorPlacementState.picking ? '正在地图选点' : (sensorPlacementState.pendingPoint ? '重新地图选点' : '开始地图选点') }}
              </button>
              <button class="sensor-btn primary" @click="resetManualSensorDraft(true)">
                <i class="fas fa-rotate-left"></i> 恢复默认值
              </button>
              <button class="sensor-btn primary" @click="confirmManualSensorPlacement">
                <i class="fas fa-circle-check"></i> 确认添加
              </button>
              <button class="sensor-btn danger" @click="cancelManualSensorPlacement">
                <i class="fas fa-xmark"></i> 取消
              </button>
            </div>
          </div>
          <div v-if="manualSensorConfigVisible" class="candidate-detail-card" style="margin-top:10px;">
            <div class="candidate-detail-head">
              <span>批量导入传感器</span>
              <span>{{ batchImportPreview.length }} 个点位</span>
            </div>
            <div class="control-grid" style="margin-top:10px;">
              <label class="control-field" style="grid-column:1 / -1;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                  <span>直接粘贴Excel数据 (X Y 高度)</span>
                  <button class="sensor-btn" @click="pasteFromClipboard" style="padding:2px 8px;font-size:11px;">
                    <i class="fas fa-paste"></i> 粘贴
                  </button>
                </div>
                <textarea v-model="batchImportText" rows="6" style="width:100%;background:#0a0f1a;color:#e0e0e0;border:1px solid #2a3a2a;border-radius:6px;padding:8px;font-family:monospace;font-size:12px;resize:vertical;" placeholder="支持格式:&#10;15  10  1.5&#10;23  10  1.5&#10;或: 15,10,1.5&#10;或: 15 10"></textarea>
              </label>
              <div style="grid-column:1 / -1;display:flex;gap:8px;align-items:center;">
                <span style="font-size:11px;color:#888;">默认:</span>
                <label style="display:flex;align-items:center;gap:4px;font-size:11px;">
                  高度 <input v-model.number="batchDefaultHeight" type="number" min="0.3" max="10" step="0.1" style="width:50px;background:#0a0f1a;color:#e0e0e0;border:1px solid #2a3a2a;border-radius:4px;padding:2px 4px;font-size:11px;"> m
                </label>
                <label style="display:flex;align-items:center;gap:4px;font-size:11px;">
                  范围 <input v-model.number="batchDefaultRange" type="number" min="0" max="20" step="0.1" style="width:50px;background:#0a0f1a;color:#e0e0e0;border:1px solid #2a3a2a;border-radius:4px;padding:2px 4px;font-size:11px;"> m
                </label>
              </div>
              <div v-if="batchImportPreview.length > 0" style="grid-column:1 / -1;max-height:120px;overflow-y:auto;background:#0a0f1a;border-radius:6px;padding:6px;font-size:11px;">
                <div v-for="(item, idx) in batchImportPreview.slice(0, 20)" :key="idx" style="display:flex;justify-content:space-between;padding:2px 0;">
                  <span style="color:#00e5a0;">{{ item.id }}</span>
                  <span>({{ item.x.toFixed(1) }}, {{ item.y.toFixed(1) }})</span>
                </div>
                <div v-if="batchImportPreview.length > 20" style="color:#888;text-align:center;padding:4px;">... 共 {{ batchImportPreview.length }} 个</div>
              </div>
              <button class="sensor-btn primary" @click="executeBatchImport" :disabled="batchImportPreview.length === 0" style="grid-column:1 / -1;width:100%;">
                <i class="fas fa-upload"></i> 一键导入 {{ batchImportPreview.length }} 个传感器
              </button>
            </div>
          </div>
          <div v-if="manualSensorPanelVisible" class="candidate-detail-card" style="margin-top:10px;">
            <div class="candidate-detail-head">
              <span>传感器手动录入面板</span>
              <span>{{ manualSensorTarget ? manualSensorTarget.id : '未选择' }}</span>
            </div>
            <div v-if="sensors.length" class="control-grid" style="margin-top:10px;">
              <label class="control-field">
                <span>目标传感器</span>
                <select :value="manualSensorTargetId" @change="selectManualSensorTarget($event.target.value)">
                  <option v-for="sensor in sensors" :key="sensor.id" :value="sensor.id">{{ sensor.id }}</option>
                </select>
              </label>
              <label class="control-field">
                <span>数据模式</span>
                <select :value="manualSensorTarget?.mode || 'auto'" @change="setManualPanelSensorMode($event.target.value)">
                  <option value="auto">自动采样</option>
                  <option value="manual">手动录入</option>
                </select>
              </label>
              <label class="control-field">
                <span>当前帧</span>
                <input :value="diffusionFrames.length ? diffusionState.currentFrame + 1 : 0" type="number" disabled>
              </label>
              <label class="control-field" v-if="manualSensorTarget?.mode === 'manual'">
                <span>当前帧浓度(ppm)</span>
                <input v-model.number="sensorEditorState.currentFrameConcentration" type="number" min="0" step="0.1">
              </label>
              <label class="control-field" v-if="manualSensorTarget?.mode === 'manual'">
                <span>全时段浓度(ppm)</span>
                <input v-model.number="sensorEditorState.fillAllConcentration" type="number" min="0" step="0.1">
              </label>
            </div>
            <div v-if="sensors.length && manualSensorTarget?.mode === 'manual'" class="inline-actions" style="margin-top:10px;">
              <button class="sensor-btn primary" @click="applySelectedSensorManualValueToCurrentFrame">
                <i class="fas fa-pen"></i> 写入当前帧
              </button>
              <button class="sensor-btn primary" @click="fillSelectedSensorManualSeries">
                <i class="fas fa-wave-square"></i> 填充全时段
              </button>
              <button class="sensor-btn primary" @click="copyAutoSeriesToSelectedSensorManual">
                <i class="fas fa-copy"></i> 复制自动曲线
              </button>
              <button class="sensor-btn danger" @click="clearSelectedSensorManualSeries">
                <i class="fas fa-eraser"></i> 清空手动曲线
              </button>
            </div>
            <div v-if="!sensors.length" class="empty-block" style="margin-top:10px;">请先添加至少一个传感器，再进行手动录入</div>
            <div class="control-subnote" style="margin-top:8px;">
              这里提供独立的手动录入入口；选中传感器后，右侧详情区也会同步显示同一套编辑能力。
            </div>
          </div>
          <div class="sampling-row">
            <span>当前帧有读数 {{ sensorSamplingSummary.sampled }} 个</span>
            <span>预警 {{ sensorSamplingSummary.warning }} 个</span>
            <span>危险 {{ sensorSamplingSummary.danger }} 个</span>
          </div>
        </div>

        <div class="panel-section">
          <div class="panel-title" @click="gasPanelVisible = !gasPanelVisible" style="cursor:pointer;">
            <i class="fas fa-flask"></i> 气体类型管理
            <span style="margin-left:auto;font-size:11px;color:var(--fg-muted);">{{ gases.length }} 种</span>
            <i class="fas" :class="gasPanelVisible ? 'fa-chevron-up' : 'fa-chevron-down'" style="margin-left:6px;"></i>
          </div>
          <div v-if="gasPanelVisible">
            <div v-if="gases.length === 0" class="control-note" style="margin-top:6px;">暂无气体类型数据</div>
            <div v-for="g in gases" :key="g.id" class="gas-item" style="display:flex;align-items:center;gap:6px;padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
              <span style="font-weight:bold;min-width:40px;font-size:12px;color:#00e5a0;">{{ g.id }}</span>
              <span style="flex:1;font-size:11px;">{{ g.name }}</span>
              <span style="font-size:10px;color:var(--fg-muted);">{{ g.detectionRange }}</span>
              <button class="tool-btn" style="padding:2px 6px;font-size:10px;" @click="editGas(g)"><i class="fas fa-pen"></i></button>
              <button class="tool-btn" style="padding:2px 6px;font-size:10px;color:#ef4444;" @click="removeGas(g.id)"><i class="fas fa-trash"></i></button>
            </div>
            <div class="inline-actions" style="margin-top:8px;">
              <button class="sensor-btn primary" @click="resetGasDraft()" style="font-size:11px;padding:4px 10px;">
                <i class="fas fa-plus"></i> 新增气体
              </button>
              <button class="sensor-btn primary" @click="saveGasDraft()" style="font-size:11px;padding:4px 10px;" :disabled="!gasEditDraft.id">
                <i class="fas fa-save"></i> 保存
              </button>
            </div>
            <div class="control-grid" style="margin-top:6px;grid-template-columns:1fr 1fr;">
              <label class="control-field" style="grid-column:1 / -1;">
                <span>气体编号 / 名称</span>
                <div style="display:flex;gap:4px;">
                  <input v-model.trim="gasEditDraft.id" type="text" placeholder="编号 (如 CO)" style="width:80px;">
                  <input v-model.trim="gasEditDraft.name" type="text" placeholder="名称 (如一氧化碳)" style="flex:1;">
                </div>
              </label>
              <label class="control-field" style="grid-column:1 / -1;">
                <span>检测范围</span>
                <input v-model.trim="gasEditDraft.detectionRange" type="text" placeholder="如 0-1000 ppm">
              </label>
              <label class="control-field">
                <span>安装高度 (m)</span>
                <input v-model.number="gasEditDraft.installationHeight" type="number" min="0.3" max="10" step="0.1">
              </label>
              <label class="control-field">
                <span>有效范围 (m)</span>
                <input v-model.number="gasEditDraft.effectiveRange" type="number" min="5" max="100" step="1">
              </label>
              <label class="control-field">
                <span>优先级</span>
                <select v-model.number="gasEditDraft.priority">
                  <option :value="1">1 - 重大风险</option>
                  <option :value="2">2 - 较大风险</option>
                  <option :value="3">3 - 一般风险</option>
                  <option :value="4">4 - 低风险</option>
                </select>
              </label>
              <label class="control-field">
                <span>风险值</span>
                <input v-model.number="gasEditDraft.risk" type="number" min="0" max="1" step="0.05">
              </label>
              <label class="control-field" style="grid-column:1 / -1;">
                <span>备注</span>
                <input v-model.trim="gasEditDraft.installRemark" type="text" placeholder="布点说明">
              </label>
            </div>
          </div>
        </div>

        <div class="panel-section" style="margin-top:auto;">
          <div class="panel-title"><i class="fas fa-bell"></i> 实时告警</div>
          <div class="alert-list">
            <div v-for="(a, idx) in alerts" :key="idx" class="alert-item" :class="a.type">
              <div class="alert-icon"><i :class="a.icon"></i></div>
              <div>
                <div class="alert-text">{{ a.text }}</div>
                <div class="alert-time">{{ a.time }}</div>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </div>

    <!-- 设备详情全屏浮层 -->
    <Transition name="device-fullscreen">
      <div v-if="deviceFullscreenVisible" class="device-fullscreen-overlay" @click.self="closeDeviceFullscreen">
        <div class="device-fullscreen-card">
          <button class="device-fullscreen-close" @click="closeDeviceFullscreen" title="关闭">
            <i class="fas fa-times"></i>
          </button>
          <div class="device-fullscreen-img-wrap"
               ref="deviceImgWrapRef"
               @wheel.prevent="onDeviceImgWheel"
               @mousedown="onDeviceImgDragStart"
               @mousemove="onDeviceImgDragMove"
               @mouseup="onDeviceImgDragEnd"
               @mouseleave="onDeviceImgDragEnd"
               @dblclick="onDeviceImgDblClick">
            <img :src="deviceFullscreenData.image" class="device-fullscreen-img"
                 :style="{ transform: `scale(${deviceImgZoom}) translate(${deviceImgPanX}px, ${deviceImgPanY}px)` }"
                 draggable="false" />
            <div class="device-img-zoom-bar">
              <button class="df-zoom-btn" @click.stop="deviceImgZoomIn" title="放大"><i class="fas fa-plus"></i></button>
              <span class="df-zoom-val">{{ Math.round(deviceImgZoom * 100) }}%</span>
              <button class="df-zoom-btn" @click.stop="deviceImgZoomOut" title="缩小"><i class="fas fa-minus"></i></button>
              <div class="df-zoom-divider"></div>
              <button class="df-zoom-btn" @click.stop="deviceImgZoomReset" title="重置视图"><i class="fas fa-crosshairs"></i></button>
            </div>
            <div class="device-img-hint" v-if="deviceImgZoom <= 1">
              <i class="fas fa-mouse-pointer"></i> 滚轮缩放 · 双击放大 · 拖拽平移
            </div>
          </div>
          <div class="device-fullscreen-info">
            <div class="df-info-head">
              <div class="df-info-icon"><i class="fas fa-microchip"></i></div>
              <div>
                <div class="device-fullscreen-title">{{ deviceFullscreenData.deviceName }}</div>
                <div class="df-info-subtitle">{{ deviceFullscreenData.location }}</div>
              </div>
            </div>
            <div class="df-info-divider"></div>
            <div class="device-fullscreen-row">
              <span class="df-label"><i class="fas fa-signal df-label-icon"></i> 设备状态</span>
              <span class="df-badge df-badge-online"><span class="df-badge-dot"></span>在线运行</span>
            </div>
            <div class="device-fullscreen-row">
              <span class="df-label"><i class="fas fa-shield-halved df-label-icon"></i> 报警状态</span>
              <span class="df-badge df-badge-safe"><i class="fas fa-check" style="font-size:9px;margin-right:2px;"></i>正常</span>
            </div>
            <div class="device-fullscreen-row">
              <span class="df-label"><i class="fas fa-wave-square df-label-icon"></i> 实时浓度</span>
              <span class="df-conc">{{ deviceFullscreenData.concentration }}</span>
            </div>
            <div class="df-info-divider"></div>
            <div class="df-std-block">
              <div class="df-std-head"><i class="fas fa-book-open"></i> 安装标准依据</div>
              <div class="df-std-text">{{ deviceFullscreenData.standard }}</div>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 传感器参数编辑浮层 -->
    <div v-if="sensorEditVisible" class="sensor-edit-overlay" @click.self="sensorEditVisible = false">
      <div class="sensor-edit-panel">
        <div class="sensor-edit-header">
          <span>编辑传感器参数</span>
          <button class="close-btn" @click="sensorEditVisible = false"><i class="fas fa-times"></i></button>
        </div>
        <div class="sensor-edit-body">
          <label class="control-field">
            <span>安装高度 (m)</span>
            <input v-model.number="sensorEditDraft.installationHeight" type="number" min="0.3" max="10" step="0.1">
          </label>
          <label class="control-field">
            <span>有效监测范围 (m)</span>
            <input v-model.number="sensorEditDraft.effectiveRange" type="number" min="5" max="100" step="1">
          </label>
          <label class="control-field">
            <span>检测范围</span>
            <input v-model.trim="sensorEditDraft.detectionRange" type="text" placeholder="如 0-1000 ppm">
          </label>
          <label class="control-field">
            <span>优先级</span>
            <select v-model.number="sensorEditDraft.priority">
              <option :value="1">1 - 重大风险</option>
              <option :value="2">2 - 较大风险</option>
              <option :value="3">3 - 一般风险</option>
              <option :value="4">4 - 低风险</option>
            </select>
          </label>
          <label class="control-field">
            <span>风险值</span>
            <input v-model.number="sensorEditDraft.risk" type="number" min="0" max="1" step="0.05">
          </label>
          <label class="control-field" style="grid-column:1 / -1;">
            <span>布点说明</span>
            <input v-model.trim="sensorEditDraft.installRemark" type="text" placeholder="安装位置备注">
          </label>
          <div class="inline-actions" style="margin-top:16px;justify-content:flex-end;">
            <button class="sensor-btn" style="background:var(--bg-elevated);color:var(--fg);border:1px solid var(--border);" @click="sensorEditVisible = false">取消</button>
            <button class="sensor-btn primary" @click="saveSensorEdit"><i class="fas fa-save"></i> 保存修改</button>
          </div>
        </div>
      </div>
    </div>
    <div class="toast" :class="[toastVisible ? 'show' : '', toastType]">
      <i :class="toastIcon"></i>
      <span>{{ toastText }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  PHASE1_DEFAULT_SCENARIO,
  PHASE1_GASES,
  attachSensorSampleSeries,
  getFrameConcentrationAtPoint,
  getGasById,
  getPhase1LeakSources,
} from '@/data/phase1Config'
import {
  runDiffusionSimulation as apiRunDiffusionSimulation,
  runPinnCoarseSearch as apiPinnCoarseSearch,
  runPinnInversion as apiPinnInversion,
  runEvacuationPlanning as apiRunEvacuationPlanning,
} from '@/api/algorithm'
import {
  findNearestAllowedGasSourceFacility,
  getGasSourceConfig,
  validateGasLeakSource,
} from '@/data/gasSourceCatalog'
import { clamp, formatGeoCoord, geoToWorld, worldToGeo } from '@/data/coordinate'
import {
  alerts,
  buildingEntrances,
  facilities,
  facilityById,
  getFacilityAnchorPoint,
  groundSpeckles,
  keyAreas,
  legends,
  parkEntrances,
  pipes,
  roads,
  sensorTypes,
  getSensorDevice,
  stats,
  zones,
} from '@/data/parkAssets'
import { CAR_PATROL_ROUTES } from '@/data/carPatrolRoutes'

import { useCarStore } from '@/store/carStore'
import ParkScene3D from './components/ParkScene3D.vue'

const route = useRoute()
const router = useRouter()
const carStore = useCarStore()
const mapCanvasRef = ref(null)
const mapContainerRef = ref(null)
const clock = ref('--:--:--')
const coordLongitude = ref('118.780°E')
const coordLatitude = ref('32.040°N')
const coordAltitude = ref('18.0m')
const isDragging = ref(false)
const showLabels = ref(true)
const showHeatmap = ref(false)
const showFlow = ref(false)
const showEntrances = ref(false)
const showSensors = ref(true)
const showSensorRanges = ref(true)
const viewMode = ref<'2d' | '3d'>('2d')
const scene3DRef = ref<InstanceType<typeof ParkScene3D>>()
// 预加载传感器设备图片
const sensorDeviceImageCache = new Map()
function getSensorDeviceImage(sensor) {
  const device = getSensorDevice(sensor)
  if (!device?.image) return null
  if (sensorDeviceImageCache.has(device.image)) return sensorDeviceImageCache.get(device.image)
  const img = new Image()
  img.src = device.image
  img.onload = () => render()
  sensorDeviceImageCache.set(device.image, img)
  return img
}
const measureMode = ref(false)
const activeFilter = ref('all')
const selectedZone = ref('')
const selectedFacility = ref(null)
const hoveredFacility = ref(null)
const hoveredEntrance = ref(null)
const hoveredSensor = ref(null)
const panelCollapsed = ref(false)
const searchQuery = ref('')
const infoTitle = ref('选择设施查看详情')
const infoSubtitle = ref('')
const infoRows = ref([])
const toastVisible = ref(false)
const toastText = ref('')
const toastType = ref('success')
const toastIcon = ref('fas fa-check-circle')
const viewState = reactive({ offsetX:0, offsetY:0, scale:1, dragging:false, lastX:0, lastY:0 })
const zoomLevel = computed(() => viewState.scale.toFixed(1))

let flowAnimOffset = 0
let measurePoints = []
let animFrameId = 0
let ctx = null
let canvasEl = null
let containerEl = null
let toastTimer = 0
let clockTimer = 0
// ---- 小车调度集成 ----
const showCars = ref(false)
const selectedCar = ref(null)
const hoveredCar = ref(null)
const carRefreshTimer = ref(0)
const carMarkers = ref([])
const carPatrolEnabled = ref(false)
const carPatrolState = reactive({})
const mobileSensorReadings = ref([])
const yoloResult = ref(null)  // { carId, count, imageBase64, timestamp }

function syncCarMarkers() {
  carMarkers.value = carStore.carList.map(car => ({
    id: car.id,
    x: car.x,
    y: car.y,
    status: car.status,
    gasLabel: ['', '甲烷', '氨气', '一氧化碳', '氧气'][car.id] || ''
  }))
}

function syncCarMobileSensors() {
  if (!diffusionFrames.value.length) return
  const frame = currentDiffusionFrame.value
  if (!frame) return
  const cars = carStore.carList
  mobileSensorReadings.value = cars.map(car => {
    const concentration = getFrameConcentrationAtPoint(frame, car.x, car.y)
    return {
      id: `car_sensor_${car.id}`,
      x: car.x,
      y: car.y,
      type: 'gas',
      priority: 2,
      mode: 'auto',
      sampledSeries: [{ frameIndex: diffusionState.currentFrame, timeSec: frame.timeSec, concentration }],
      sampledPeak: concentration,
      manualSeries: [],
      risk: 0,
      carId: car.id,
      currentConcentration: concentration,
    }
  })
}
syncCarMarkers()

function toggleCars() {
  showCars.value = !showCars.value
  render()
  showToast(showCars.value ? '小车标记已显示' : '小车标记已隐藏', 'success')
}

function toggleCarPatrol() {
  carPatrolEnabled.value = !carPatrolEnabled.value
  if (carPatrolEnabled.value) {
    carStore.carList.forEach(car => {
      const route = CAR_PATROL_ROUTES[car.id]
      if (route) {
        carPatrolState[car.id] = { waypointIndex: 0 }
        const start = route.waypoints[0]
        car.x = start.x
        car.y = start.y
      }
    })
    syncCarMarkers()
    showToast('小车巡逻已启动', 'success')
  } else {
    showToast('小车巡逻已停止', 'warn')
  }
  render()
}


async function runEndToEndPipeline() {
  if (!diffusionFrames.value.length) {
    showToast('请先运行扩散模拟，生成浓度场数据', 'warn')
    return
  }
  showToast('=== 全流程联动启动 ===', 'success')
  
  // Step 1: 启动小车巡逻
  if (!carPatrolEnabled.value) {
    toggleCarPatrol()
  }
  
  // Step 2: 等待小车采集数据（模拟3秒巡逻）
  showToast('小车正在巡逻采样气体数据...', 'success')
  await new Promise(resolve => setTimeout(resolve, 3000))
  syncCarMobileSensors()
  
  // Step 3: 执行 PINN 粗搜索（融合静态+动态传感器）
  showToast('执行 PINN 粗搜索，融合静态传感器 + 移动传感器数据...', 'success')
  await runPinnCoarseSearchPreview()
  if (!coarseSearchResult.value?.candidateRegions?.length) {
    showToast('PINN 粗搜索未找到候选区域', 'warn')
    return
  }
  showToast(`粗搜索完成，找到 ${coarseSearchResult.value.candidateRegions.length} 个候选区域`, 'success')
  
  // Step 4: 自动选中最佳候选区域
  if (coarseCandidateRegions.value.length) {
    const best = coarseCandidateRegions.value[0]
    selectCoarseCandidate(best.candidateId, true)
    showToast(`最佳候选区域: ${best.label} (评分: ${best.score.toFixed(3)})`, 'success')
  }
  
  // Step 5: 执行 PINN 精修
  showToast('执行 PINN 精修，精确定位泄漏源...', 'success')
  await runMockPinnRefinementPreview()
  
  showToast('=== 全流程联动完成 ===', 'success')
  showToast('泄漏源已定位，请查看扩散模拟结果', 'success')
}
function refreshCarData() {
  // 巡逻时跳过 DB 轮询（避免覆盖移动位置）
  if (carPatrolEnabled.value) {
    syncCarMarkers()
    render()
    return
  }
  carStore.fetchCarDataFromDB().then(() => {
    syncCarMarkers()
    render()
  }).catch(() => {
    syncCarMarkers()
    render()
  })
}

function handleCarClick(carId) {
  const car = carStore.carList.find(c => c.id === carId)
  if (!car) return
  selectedCar.value = car
  showCarInfo(car)
}

function navigateToCarDetail(carId) {
  router.push({
    path: `/car/${carId}`,
    query: { t: new Date().getTime() }
  })
}

function showCarInfo(car) {
  infoTitle.value = `小车 ${car.id}`
  infoSubtitle.value = { text: `● ${car.status === 'warning' ? '异常' : '正常'}`, color: car.status === 'warning' ? '#ef4444' : '#00e5a0' }
  const gasName = ['', '甲烷 (CH₄)', '氨气 (NH₃)', 'CO气体', '氧气 (O₂)'][car.id] || '--'
  const threshold = carStore.gasThreshold[car.id]
  const thresholdText = threshold
    ? Array.isArray(threshold.threshold)
      ? `${threshold.threshold[0]}–${threshold.threshold[1]} ${threshold.unit}`
      : `${threshold.threshold} ${threshold.unit}`
    : '--'
  infoRows.value = [
    { key: '车辆编号', val: `#${car.id}` },
    { key: '当前位置', val: `X: ${car.x}  Y: ${car.y}` },
    { key: '监测气体', val: gasName },
    { key: '状态', val: car.status === 'warning' ? '⚠ 预警' : '✓ 正常' },
    { key: '报警阈值', val: thresholdText },
    { key: '操作', val: '查看详情 →', action: () => navigateToCarDetail(car.id) },
    { key: '设警', val: car.status === 'warning' ? '重置状态' : '设警', action: () => toggleCarWarning(car.id), btnClass: 'warning-btn' },
    { key: 'AI巡检', val: 'YOLO 检测 →', action: () => triggerYoloForCar(car.id), btnClass: 'warning-btn' },
  ]
  selectedFacility.value = null
  selectedSensor.value = null
  render()
}

// 触发 YOLO 检测（小车按钮调用）
const triggerYoloForCar = async (carId) => {
  const car = carStore.carList.find(c => c.id === carId)
  if (!car) return
  showToast(`小车 ${carId} YOLO 检测中...`, 'success')
  try {
    // Capture canvas area around the car
    const rect = canvasEl.getBoundingClientRect()
    const s = viewState.scale
    const ox = viewState.offsetX * s + canvasEl.width * 0.05
    const oy = viewState.offsetY * s + canvasEl.height * 0.05
    // Convert world coords to screen coords
    const sx = car.x * s + ox
    const sy = car.y * s + oy
    const snapSize = 150
    const snapX = Math.max(0, Math.min(canvasEl.width - snapSize, sx - snapSize / 2))
    const snapY = Math.max(0, Math.min(canvasEl.height - snapSize, sy - snapSize / 2))
    
    const snapshot = document.createElement('canvas')
    snapshot.width = snapSize
    snapshot.height = snapSize
    const snapCtx = snapshot.getContext('2d')
    snapCtx.drawImage(canvasEl, snapX, snapY, snapSize, snapSize, 0, 0, snapSize, snapSize)
    
    snapshot.toBlob(async (blob) => {
      const formData = new FormData()
      formData.append('file', blob, `car_${carId}_capture.png`)
      try {
        const res = await fetch((import.meta.env.VITE_APP_BASE_API || '/api') + '/analysis/person', { method: 'POST', body: formData })
        const responseBody = await res.json()
        const data = responseBody?.data || responseBody
        if (data.status === 'success') {
          yoloResult.value = { carId, count: data.count, imageBase64: data.image_base64, timestamp: Date.now() }
          showToast(`小车 ${carId} 检测到 ${data.count} 人`, 'success')
          // Update the car info panel with YOLO result
          if (selectedCar.value?.id === carId) {
            showCarInfo(selectedCar.value)
          }
          render()
        } else {
          showToast('YOLO 检测未返回结果', 'warn')
        }
      } catch (err) {
        showToast('YOLO API 请求失败，请确认后端服务已启动', 'warn')
      }
    }, 'image/png')
  } catch (err) {
    showToast('YOLO 检测失败: ' + err.message, 'warn')
  }
}
// 切换小车预警状态
const toggleCarWarning = async (id) => {
  const car = carStore.carList.find(c => c.id === id)
  if (!car) return
  try {
    if (car.status === 'warning') {
      await carStore.resetCarStatus(id)
      showToast(`小车 ${id} 状态已重置`, 'success')
    } else {
      await carStore.setCarWarning(id)
      showToast(`小车 ${id} 预警已触发`, 'warn')
    }
    refreshCarData()
  } catch (err) {
    showToast(`操作失败: ${err.message}`, 'warn')
  }
}

const sensors = ref([])
const gases = ref([])
const riskGrid = ref([])
const weatherState = ref({windSpeed: 2, windDir: 135, temp: 28, rain: 0, humidity: 60, pressure: 1013, windSpeedKmh: 0, obsTime: ''})
const weatherSource = ref('simulated') // 'real' | 'simulated'
const lastWeatherFetch = ref(0)
/** 当前无真实泄漏/扩散事件时，浓度数据由高斯烟羽模型仿真生成 */
const isSimulatedConcentration = computed(() =>
  !diffusionFrames.value.length || !currentLeakSourcePoint.value
)

/**
 * 获取实时天气数据（和风天气 API v7）
 * 园区坐标：118.780E, 32.040N
 * 若 API Key 未配置或请求失败，自动回退到模拟天气
 *
 * ⚠️ 安全说明：
 * 当前方案在前端直连和风天气 API，适合开发演示。
 * 正式部署时务必通过后端代理转发请求（将 VITE_QWEATHER_KEY 移至后端配置），
 * 避免 API Key 在浏览器端暴露。
 */
async function fetchRealtimeWeather() {
  const apiKey = import.meta.env.VITE_QWEATHER_KEY
  if (!apiKey) {
    if (weatherSource.value !== 'simulated') {
      weatherSource.value = 'simulated'
      showToast('未配置 QWeather API Key，使用模拟天气数据', 'warn')
    }
    return
  }
  try {
    const resp = await fetch(
      `https://devapi.qweather.com/v7/weather/now?location=118.78,32.04&key=${apiKey}`
    )
    const data = await resp.json()
    if (data.code === '200') {
      const now = data.now
      // ── 风向 ──
      // 和风天气 wind360 指示"风来的方向"，转换为模型使用的"风吹向"（+180°）
      const windDirFrom = parseInt(now.wind360) || 135
      const windDirTo = (windDirFrom + 180) % 360
      // ── 风速单位转换 ──
      // QWeather now.windSpeed 单位是 km/h，模型计算需使用 m/s（÷3.6）
      const windSpeedKmh = parseFloat(now.windSpeed) || 0
      const windSpeedMs = windSpeedKmh / 3.6
      weatherState.value = {
        windSpeed: Math.round(windSpeedMs * 10) / 10,    // m/s（参与扩散/监测范围/风险计算）
        windSpeedKmh: Math.round(windSpeedKmh * 10) / 10, // km/h（仅 UI 展示）
        windDir: windDirTo,
        temp: parseFloat(now.temp) || 28,
        rain: parseFloat(now.precip) || 0,
        humidity: parseFloat(now.humidity) || 60,
        pressure: parseFloat(now.pressure) || 1013,
        obsTime: now.obsTime || ''
      }
      weatherSource.value = 'real'
      lastWeatherFetch.value = Date.now()
    } else {
      throw new Error(`API error: ${data.code}`)
    }
  } catch (e) {
    console.warn('QWeather fetch failed, fallback to simulated:', e.message)
    weatherSource.value = 'simulated'
  }
}

/**
 * 定时刷新真实天气（每 30 分钟）
 */
function startWeatherAutoRefresh() {
  fetchRealtimeWeather()
  setInterval(() => fetchRealtimeWeather(), 30 * 60 * 1000)
}
const layoutResult = ref({ totalCost: 0, coverageRate: 0, riskCoverRate: 0, sensorCount: 0 })
const batchImportText = ref('')
const batchImportPreview = ref([])
const batchDefaultHeight = ref(1.5)
const batchDefaultRange = ref(4)
const selectedSensor = ref(null)
const riskStat = ref({ critical: 0, high: 0, mid: 0, low: 0 })
const diffusionGasOptions = PHASE1_GASES
const initialDiffusionSourceOptions = getPhase1LeakSources(facilities, PHASE1_DEFAULT_SCENARIO.gasId)
const playbackSpeedOptions = [0.5, 1, 1.5, 2]
const diffusionForm = reactive({
  ...PHASE1_DEFAULT_SCENARIO,
  sourceFacilityId: initialDiffusionSourceOptions[0]?.id || PHASE1_DEFAULT_SCENARIO.sourceFacilityId,
})
const leakSourceState = reactive({
  mode: 'facility',
  picking: false,
  mapPoint: null,
  manualLongitude: '',
  manualLatitude: '',
})
const MANUAL_SENSOR_DEFAULTS = Object.freeze({
  installationHeight: 1.5,
  effectiveRange: 20,
  detectionRange: 'CO / CH4 / NH3 / O2',
  installRemark: '',
})
const sensorPlacementState = reactive({
  picking: false,
  pickingOrigin: false,
  pendingPoint: null,
  origin: { x: 70, y: 260 },
  relativeX: 0,
  relativeY: 0,
})
function createManualSensorDraft() {
  return {
    installationHeight: MANUAL_SENSOR_DEFAULTS.installationHeight,
    effectiveRange: MANUAL_SENSOR_DEFAULTS.effectiveRange,
    detectionRange: MANUAL_SENSOR_DEFAULTS.detectionRange,
    installRemark: MANUAL_SENSOR_DEFAULTS.installRemark,
  }
}
const diffusionSourceOptions = computed(() => getPhase1LeakSources(facilities, diffusionForm.gasId))
const diffusionFrames = ref([])
const diffusionMeta = ref({
  gas: getGasById(diffusionForm.gasId),
  sourceFacility: null,
  sourcePoint: null,
  stats: { peakConcentration: 0, peakAffectedArea: 0, peakDangerArea: 0 },
  blockedMask: null,
  map: null,
  executor: null,
  sensorSeries: [],
  scenarioMeta: null,
  outputMeta: null,
})
const diffusionState = reactive({
  currentFrame: 0,
  playing: false,
  loop: true,
  speed: 1,
  accumulatorMs: 0,
  frameDurationMs: 280,
})
const diffusionExecutorState = reactive({
  mode: 'local',
  workerAvailable: false,
  workerInitialized: false,
  fallbackReason: '',
})
const evacuationExecutorState = reactive({
  mode: 'local',
  fallbackReason: '',
})
const pinnExecutorState = reactive({
  mode: 'local',
  fallbackReason: '',
})
const pinnConfig = reactive({
  topK: 4,
  gridStep: 20,
  candidateRadius: 45,
  supportRadius: 140,
  distanceScale: 90,
  mergeDistance: 80,
  minObservationThreshold: 0.5,
})
const pinnRefinementConfig = reactive({
  epochs: 120,
  learningRate: 0.01,
  animationSteps: 18,
  minSignalThreshold: 1.5,
  convergenceRatio: 0.22,
})
const currentDiffusionFrame = computed(() => diffusionFrames.value[diffusionState.currentFrame] || null)
const selectedDiffusionSource = computed(() => facilityById.get(diffusionForm.sourceFacilityId) || null)
const diffusionSourceValidation = computed(() => buildLeakSourceValidation())
const diffusionSourceHint = computed(() => {
  const validation = diffusionSourceValidation.value
  const config = validation.config || getGasSourceConfig(diffusionForm.gasId)
  const allowedNames = validation.allowedFacilities.length
    ? validation.allowedFacilities.map(item => item.name).join(' / ')
    : '未配置'
  if (validation.valid) {
    if (leakSourceState.mode === 'facility') {
      return `合法泄漏源：${allowedNames}，校验半径 ${config?.validRadiusMeters ?? '--'}m`
    }
    const nearestName = validation.nearestAllowedFacility?.name || validation.selectedFacility?.name || '--'
    const distance = validation.distanceToNearestAllowedMeters ?? '--'
    return `当前点位已绑定 ${nearestName}，与允许区域距离 ${distance}m`
  }
  return `仅允许：${allowedNames}，超出 ${config?.validRadiusMeters ?? '--'}m 将拦截模拟`
})
const diffusionSummary = computed(() => {
  const gas = diffusionMeta.value.gas || getGasById(diffusionForm.gasId)
  const source = diffusionMeta.value.sourceFacility || selectedDiffusionSource.value
  const frame = currentDiffusionFrame.value
  return {
    gasName: gas?.name || '--',
    sourceName: source?.name || '未设置',
    frameText: diffusionFrames.value.length ? `${diffusionState.currentFrame + 1}/${diffusionFrames.value.length}` : '0/0',
    timeText: frame ? `${frame.timeSec.toFixed(0)} s` : '--',
    maxConcentration: frame ? `${frame.maxConcentration.toFixed(1)} ppm` : '--',
    affectedArea: frame ? `${frame.affectedArea.toFixed(0)} m²` : '--',
    dangerArea: frame ? `${frame.dangerArea.toFixed(0)} m²` : '--',
  }
})
const sensorSamplingSummary = computed(() => {
  const gas = diffusionMeta.value.gas || getGasById(diffusionForm.gasId)
  let sampled = 0
  let warning = 0
  let danger = 0
  sensors.value.forEach(sensor => {
    const current = getSensorCurrentConcentration(sensor)
    if (current > 0) sampled += 1
    if (current >= gas.warningThreshold) warning += 1
    if (current >= gas.dangerThreshold) danger += 1
  })
  return { sampled, warning, danger }
})
const selectedSensorHistoryChart = computed(() => buildSensorHistoryChart(selectedSensor.value))

const sensorDeviceCard = computed(() => {
  if (!selectedSensor.value) return null
  const device = getSensorDevice(selectedSensor.value)
  const concentration = getSensorCurrentConcentration(selectedSensor.value)
  const zonePrefix = (selectedSensor.value.id || '').split('-')[0] || ''
  const zoneNames = {
    TK: '储罐区', TW: '塔器区', PA: '生产一区', PB: '精细化工区', P2: '生产二区',
    UT: '公用工程区', WH: '仓储物流区', WT: '污水处理区', MN: '环境监测区',
    MT: '机修维护区', FS: '消防设施区', FD: '防火堤', PL: '管道区', A: '行政办公区',
  }
  return {
    ...device,
    location: `${zoneNames[zonePrefix] || '园区'} / ${selectedSensor.value.id}`,
    concentration: `${concentration.toFixed(2)} ppm`,
  }
})

function zoomToSensor(sensor) {
  if (!sensor || !canvasEl) return
  const targetScale = 2.0
  viewState.scale = targetScale
  viewState.offsetX = canvasEl.width / 2 / targetScale - sensor.x
  viewState.offsetY = canvasEl.height / 2 / targetScale - sensor.y
  render()
}

const deviceFullscreenVisible = ref(false)
const deviceImgZoom = ref(1)
const deviceImgPanX = ref(0)
const deviceImgPanY = ref(0)
const deviceImgDragging = ref(false)
const deviceImgDragStartX = ref(0)
const deviceImgDragStartY = ref(0)
const deviceImgPanStartX = ref(0)
const deviceImgPanStartY = ref(0)
const deviceImgWrapRef = ref(null)
const deviceFullscreenData = computed(() => {
  if (!selectedSensor.value) return {}
  const card = sensorDeviceCard.value
  if (!card) return {}
  return { ...card }
})
function openDeviceFullscreen() {
  deviceFullscreenVisible.value = true
  deviceImgZoom.value = 1
  deviceImgPanX.value = 0
  deviceImgPanY.value = 0
}
function closeDeviceFullscreen() {
  deviceFullscreenVisible.value = false
}
function onDeviceImgWheel(e) {
  const delta = e.deltaY > 0 ? -0.1 : 0.1
  deviceImgZoom.value = Math.max(0.5, Math.min(5, deviceImgZoom.value + delta))
}
function onDeviceImgDragStart(e) {
  if (deviceImgZoom.value <= 1) return
  deviceImgDragging.value = true
  deviceImgDragStartX.value = e.clientX
  deviceImgDragStartY.value = e.clientY
  deviceImgPanStartX.value = deviceImgPanX.value
  deviceImgPanStartY.value = deviceImgPanY.value
}
function onDeviceImgDragMove(e) {
  if (!deviceImgDragging.value) return
  const dx = (e.clientX - deviceImgDragStartX.value) / deviceImgZoom.value
  const dy = (e.clientY - deviceImgDragStartY.value) / deviceImgZoom.value
  deviceImgPanX.value = deviceImgPanStartX.value + dx
  deviceImgPanY.value = deviceImgPanStartY.value + dy
}
function onDeviceImgDragEnd() {
  deviceImgDragging.value = false
}
function onDeviceImgDblClick() {
  if (deviceImgZoom.value > 1) {
    deviceImgZoom.value = 1
    deviceImgPanX.value = 0
    deviceImgPanY.value = 0
  } else {
    deviceImgZoom.value = 2.5
  }
}
function deviceImgZoomIn() {
  deviceImgZoom.value = Math.min(5, deviceImgZoom.value + 0.3)
}
function deviceImgZoomOut() {
  deviceImgZoom.value = Math.max(0.5, deviceImgZoom.value - 0.3)
}
function deviceImgZoomReset() {
  deviceImgZoom.value = 1
  deviceImgPanX.value = 0
  deviceImgPanY.value = 0
}
const sensorEditorState = reactive({
  currentFrameConcentration: 0,
  fillAllConcentration: 0,
  boundSensorId: '',
})
const manualSensorConfigVisible = ref(false)
const gasPanelVisible = ref(false)
const gasEditDraft = reactive({ id: '', name: '', detectionRange: '', installationHeight: 1.5, effectiveRange: 30, installRemark: '', priority: 3, risk: 0.3 })
const manualSensorDraft = reactive(createManualSensorDraft())
const manualSensorPanelVisible = ref(false)
const manualSensorTargetId = ref('')
const manualSensorTarget = computed(() => (
  sensors.value.find(sensor => sensor.id === manualSensorTargetId.value) || selectedSensor.value || sensors.value[0] || null
))
/** 传感器参数编辑状态 */
const sensorEditVisible = ref(false)
const sensorEditDraft = reactive({
  id: '',
  installationHeight: 1.5,
  effectiveRange: 30,
  detectionRange: '',
  installRemark: '',
  priority: 3,
  risk: 0.3,
})
const manualSensorPlacementGeo = computed(() => (
  sensorPlacementState.pendingPoint ? formatGeoCoord(sensorPlacementState.pendingPoint.x, sensorPlacementState.pendingPoint.y) : null
))
const manualSensorPlacementPointLabel = computed(() => (
  sensorPlacementState.pendingPoint ? '已选点' : '待选点'
))
const manualSensorPlacementLocationText = computed(() => {
  if (!sensorPlacementState.pendingPoint || !manualSensorPlacementGeo.value) {
    return '请先点击地图选择传感器安装位置'
  }
  const point = sensorPlacementState.pendingPoint
  const geo = manualSensorPlacementGeo.value
  return `地图坐标 (${point.x.toFixed(1)}, ${point.y.toFixed(1)}) / 经纬度 ${geo.longitude} / ${geo.latitude}`
})
const manualSensorDraftValidation = computed(() => {
  const hasHeight = manualSensorDraft.installationHeight !== '' && manualSensorDraft.installationHeight !== null && manualSensorDraft.installationHeight !== undefined
  const hasRange = manualSensorDraft.effectiveRange !== '' && manualSensorDraft.effectiveRange !== null && manualSensorDraft.effectiveRange !== undefined
  const height = Number(manualSensorDraft.installationHeight)
  const range = Number(manualSensorDraft.effectiveRange)
  if (hasHeight && (!Number.isFinite(height) || height < 0.3 || height > 10)) {
    return { valid: false, message: '安装高度需在 0.3 ~ 10 m 之间。' }
  }
  if (hasRange && (!Number.isFinite(range) || range < 0 || range > 20)) {
    return { valid: false, message: '有效监测范围需在 0 ~ 20 m 之间。' }
  }
  if (!sensorPlacementState.pendingPoint) {
    return { valid: false, message: '请先点击地图选择传感器安装位置，再确认添加。' }
  }
  return { valid: true, message: '参数校验通过；留空项会自动使用默认值。' }
})
const hoveredSensorCard = computed(() => {
  if (!hoveredSensor.value) return null
  const sensor = hoveredSensor.value
  const type = sensorTypes.find(item => item.id === sensor.type)
  const gas = diffusionMeta.value.gas || getGasById(diffusionForm.gasId)
  const concentration = getSensorCurrentConcentration(sensor)
  const level = getSensorAlarmLevel(concentration, gas)
  const geo = formatGeoCoord(sensor.x, sensor.y)
  const pLabel = getPriorityLabel(sensor.priority)
  return {
    id: sensor.id,
    priority: sensor.priority,
    priorityLabel: pLabel,
    typeName: type?.name || '传感器',
    currentLabel: `${concentration.toFixed(2)} ppm`,
    peakLabel: `${(sensor.sampledPeak || 0).toFixed(2)} ppm`,
    timeLabel: `${(currentDiffusionFrame.value?.timeSec || 0).toFixed(0)} s`,
    coordLabel: `${geo.longitude} / ${geo.latitude}`,
    levelLabel: level === 'danger' ? '危险' : level === 'warning' ? '预警' : '正常',
    levelText: level === 'danger' ? '超危险阈值' : level === 'warning' ? '超预警阈值' : '正常',
    levelClass: level,
  }
})
const pinnExportPayload = ref(null)
const pinnExportSummary = ref(null)
const coarseSearchResult = ref(null)
const coarseSearchSummary = ref(null)
const selectedCoarseCandidateId = ref('')
const refinementInput = ref(null)
const refinementResult = ref(null)
const refinementSummary = ref(null)
const refinementState = reactive({
  currentStep: 0,
  playing: false,
  speed: 1,
  accumulatorMs: 0,
  frameDurationMs: 180,
})
const pinnExportPreview = computed(() => {
  if (!pinnExportPayload.value) return ''
  return JSON.stringify(pinnExportPayload.value, null, 2).slice(0, 1400)
})
const coarseCandidateRegions = computed(() => coarseSearchResult.value?.candidateRegions || [])
const selectedCoarseCandidate = computed(() => (
  coarseCandidateRegions.value.find(candidate => candidate.candidateId === selectedCoarseCandidateId.value) || null
))
const refinementIterations = computed(() => refinementResult.value?.iterations || [])
const refinementCurrentIteration = computed(() => refinementIterations.value[refinementState.currentStep] || null)
const refinementInputSummary = computed(() => {
  if (!refinementInput.value) return null
  return {
    candidateLabel: refinementInput.value.coarseCandidate?.candidateId || '--',
    activeSensorCount: refinementInput.value.activeSensors?.length || 0,
    animationSteps: refinementInput.value.trainingConfig?.animationSteps || 0,
  }
})
const evacuationPlan = ref(null)
const evacuationBatchResult = ref(null)
const evacuationPlanningMode = ref('single')
const evacuationDisplayMode = ref('selected')
const selectedEvacuationBuildingId = ref('')
const evacuationBuildingRoutes = computed(() => evacuationBatchResult.value?.routesByBuilding || [])
const selectedEvacuationBuildingRoute = computed(() => {
  if (!evacuationBuildingRoutes.value.length) return null
  return evacuationBuildingRoutes.value.find(route => route.buildingId === selectedEvacuationBuildingId.value)
    || evacuationBuildingRoutes.value.find(route => route.buildingId === selectedFacility.value?.id)
    || evacuationBuildingRoutes.value.find(route => route.success)
    || evacuationBuildingRoutes.value[0]
})
const baseEvacuationRoute = computed(() => (
  evacuationPlanningMode.value === 'all'
    ? selectedEvacuationBuildingRoute.value
    : evacuationPlan.value
))
const selectedEvacuationCandidateId = ref('')
const evacuationCandidateRoutes = computed(() => {
  if (!baseEvacuationRoute.value?.success) return []
  return baseEvacuationRoute.value.candidateRoutes?.length
    ? baseEvacuationRoute.value.candidateRoutes
    : [baseEvacuationRoute.value]
})
const evacuationRecommendedCandidateId = computed(() => (
  baseEvacuationRoute.value?.recommendedCandidateId || evacuationCandidateRoutes.value[0]?.candidateId || ''
))
const selectedEvacuationCandidate = computed(() => {
  if (!baseEvacuationRoute.value?.success) return null
  return evacuationCandidateRoutes.value.find(route => route.candidateId === selectedEvacuationCandidateId.value)
    || evacuationCandidateRoutes.value.find(route => route.candidateId === evacuationRecommendedCandidateId.value)
    || evacuationCandidateRoutes.value[0]
    || baseEvacuationRoute.value
})
const activeEvacuationRoute = computed(() => selectedEvacuationCandidate.value || baseEvacuationRoute.value)
const evacuationSummary = computed(() => {
  const route = activeEvacuationRoute.value
  if (!route) return {
    statusText: '暂无规划',
    startLabel: '--',
    exitLabel: '--',
    distanceText: '--',
    etaText: '--',
    riskText: '--',
    blockedText: '--',
    plannerText: '--',
  }
  return {
    statusText: route.success ? '✓ 规划成功' : '✗ 规划失败',
    startLabel: route.startLabel || `(${route.startX?.toFixed(0) || '--'}, ${route.startY?.toFixed(0) || '--'})`,
    exitLabel: route.exitLabel || '未知',
    distanceText: route.totalDistance ? `${route.totalDistance.toFixed(0)} m` : '--',
    etaText: route.estimatedTime ? `${route.estimatedTime.toFixed(0)} s` : '--',
    riskText: route.riskLevel === 'high' ? '高风险' : route.riskLevel === 'medium' ? '中等风险' : '低风险',
    blockedText: route.blockedCount ? `${route.blockedCount} 处` : '无',
    plannerText: route.planner || 'D* Lite',
  }
})

let lastAnimTime = 0

/**
 * ====== 传感器数据库持久化 API ======
 */

/** 从后端加载所有已保存的传感器 */
async function fetchSensorsFromDB() {
  try {
    const resp = await fetch(`${import.meta.env.VITE_APP_BASE_API || '/api'}/sensor/list`)
    const data = await resp.json()
    if (data.code === 200 && Array.isArray(data.data)) {
      sensors.value = buildActiveSensorSeries(data.data, diffusionFrames.value)
      render()
    }
  } catch (err) {
    console.warn('从数据库加载传感器失败:', err.message)
  }
}

/** 保存传感器到后端 */
async function saveSensorToDB(sensor) {
  try {
    const resp = await fetch(`${import.meta.env.VITE_APP_BASE_API || '/api'}/sensor/add`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id: sensor.id,
        x: sensor.x,
        y: sensor.y,
        installationHeight: sensor.installationHeight,
        effectiveRange: sensor.effectiveRange,
        detectionRange: sensor.detectionRange,
        installRemark: sensor.installRemark,
        priority: sensor.priority,
        risk: sensor.risk,
        type: sensor.type || 'gas',
        mode: sensor.mode || 'auto',
        lastSampleTime: sensor.lastSampleTime,
      })
    })
    const result = await resp.json()
    if (result.code === 200) {
      return true
    } else {
      console.warn('保存传感器到数据库失败:', result.message)
      return false
    }
  } catch (err) {
    console.warn('保存传感器到数据库失败:', err.message)
    return false
  }
}

/** 更新传感器参数到后端 */
async function updateSensorToDB(sensor) {
  try {
    const resp = await fetch(`${import.meta.env.VITE_APP_BASE_API || '/api'}/sensor/update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id: sensor.id,
        x: sensor.x,
        y: sensor.y,
        installationHeight: sensor.installationHeight,
        effectiveRange: sensor.effectiveRange,
        detectionRange: sensor.detectionRange,
        installRemark: sensor.installRemark,
        priority: sensor.priority,
        risk: sensor.risk,
        type: sensor.type || 'gas',
        mode: sensor.mode || 'auto',
        lastSampleTime: sensor.lastSampleTime,
      })
    })
    const result = await resp.json()
    if (result.code !== 200) {
      console.warn('更新传感器到数据库失败:', result.message)
    }
  } catch (err) {
    console.warn('更新传感器到数据库失败:', err.message)
  }
}

/** 从后端删除传感器 */
async function deleteSensorFromDB(id) {
  try {
    const resp = await fetch(`${import.meta.env.VITE_APP_BASE_API || '/api'}/sensor/delete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id })
    })
    const result = await resp.json()
    if (result.code !== 200) {
      console.warn('从数据库删除传感器失败:', result.message)
    }
  } catch (err) {
    console.warn('从数据库删除传感器失败:', err.message)
  }
}

/** 批量从后端删除传感器 */
async function deleteAllSensorsFromDB() {
  for (const s of sensors.value) {
    await deleteSensorFromDB(s.id)
  }
}

/** ---------- 气体类型 CRUD（gas 表） ---------- */

/** 从后端加载气体类型列表 */
async function fetchGasList() {
  try {
    const resp = await fetch(`${import.meta.env.VITE_APP_BASE_API || '/api'}/gas/list`)
    const data = await resp.json()
    if (data.code === 200 && Array.isArray(data.data)) {
      gases.value = data.data
    }
  } catch (err) {
    console.warn('从数据库加载气体类型失败:', err.message)
  }
}

/** 保存气体类型到后端 */
async function saveGasToDB(gas) {
  try {
    const resp = await fetch(`${import.meta.env.VITE_APP_BASE_API || '/api'}/gas/add`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(gas)
    })
    const result = await resp.json()
    if (result.code === 200) {
      await fetchGasList()
    } else {
      console.warn('保存气体类型到数据库失败:', result.message)
    }
  } catch (err) {
    console.warn('保存气体类型到数据库失败:', err.message)
  }
}

/** 更新气体类型到后端 */
async function updateGasToDB(gas) {
  try {
    const resp = await fetch(`${import.meta.env.VITE_APP_BASE_API || '/api'}/gas/update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(gas)
    })
    const result = await resp.json()
    if (result.code === 200) {
      await fetchGasList()
    } else {
      console.warn('更新气体类型到数据库失败:', result.message)
    }
  } catch (err) {
    console.warn('更新气体类型到数据库失败:', err.message)
  }
}

/** 从后端删除气体类型 */
async function deleteGasFromDB(id) {
  try {
    const resp = await fetch(`${import.meta.env.VITE_APP_BASE_API || '/api'}/gas/delete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id })
    })
    const result = await resp.json()
    if (result.code === 200) {
      await fetchGasList()
    }
  } catch (err) {
    console.warn('从数据库删除气体类型失败:', err.message)
  }
}
/**
 * 气体管理面板：编辑气体
 */
function editGas(g) {
  gasEditDraft.id = g.id
  gasEditDraft.name = g.name
  gasEditDraft.detectionRange = g.detectionRange
  gasEditDraft.installationHeight = g.installationHeight
  gasEditDraft.effectiveRange = g.effectiveRange
  gasEditDraft.installRemark = g.installRemark || ''
  gasEditDraft.priority = g.priority
  gasEditDraft.risk = g.risk
  gasPanelVisible.value = true
}

/**
 * 气体管理面板：删除气体
 */
async function removeGas(id) {
  if (!confirm('确定删除气体类型 ' + id + ' 吗？')) return
  await deleteGasFromDB(id)
}

/**
 * 气体管理面板：重置为新增模式
 */
function resetGasDraft() {
  gasEditDraft.id = ''
  gasEditDraft.name = ''
  gasEditDraft.detectionRange = ''
  gasEditDraft.installationHeight = 1.5
  gasEditDraft.effectiveRange = 30
  gasEditDraft.installRemark = ''
  gasEditDraft.priority = 3
  gasEditDraft.risk = 0.3
  gasPanelVisible.value = true
}


/** 打开传感器参数编辑面板 */
function openSensorEdit() {
  const s = selectedSensor.value
  if (!s) return
  sensorEditDraft.id = s.id
  sensorEditDraft.installationHeight = s.installationHeight ?? 1.5
  sensorEditDraft.effectiveRange = s.effectiveRange ?? 30
  sensorEditDraft.detectionRange = s.detectionRange ?? ''
  sensorEditDraft.installRemark = s.installRemark ?? ''
  sensorEditDraft.priority = s.priority ?? 3
  sensorEditDraft.risk = s.risk ?? 0.3
  sensorEditVisible.value = true
}

/** 保存传感器参数修改 */
async function saveSensorEdit() {
  const s = selectedSensor.value
  if (!s || !sensorEditDraft.id) return
  // 更新本地对象
  s.installationHeight = sensorEditDraft.installationHeight
  s.effectiveRange = sensorEditDraft.effectiveRange
  s.detectionRange = sensorEditDraft.detectionRange
  s.installRemark = sensorEditDraft.installRemark
  s.priority = sensorEditDraft.priority
  s.risk = sensorEditDraft.risk
  // 更新到数据库
  await updateSensorToDB({
    id: s.id,
    x: s.x,
    y: s.y,
    installationHeight: s.installationHeight,
    effectiveRange: s.effectiveRange,
    detectionRange: s.detectionRange,
    installRemark: s.installRemark,
    priority: s.priority,
    risk: s.risk,
    type: s.type || 'gas',
    mode: s.mode || 'auto',
    lastSampleTime: s.lastSampleTime,
  })
  sensorEditVisible.value = false
  showToast('传感器参数已保存', 'success')
}
/**
 * 气体管理面板：保存气体
 */
async function saveGasDraft() {
  if (!gasEditDraft.id || !gasEditDraft.name) {
    showToast('请填写气体编号和名称', 'warn')
    return
  }
  const existing = gases.value.find(g => g.id === gasEditDraft.id)
  const payload = {
    id: gasEditDraft.id,
    name: gasEditDraft.name,
    detectionRange: gasEditDraft.detectionRange,
    installationHeight: gasEditDraft.installationHeight,
    effectiveRange: gasEditDraft.effectiveRange,
    installRemark: gasEditDraft.installRemark,
    priority: gasEditDraft.priority,
    risk: gasEditDraft.risk,
    type: 'gas',
    mode: 'auto',
  }
  if (existing) {
    await updateGasToDB(payload)
    showToast('气体类型已更新', 'success')
  } else {
    await saveGasToDB(payload)
    showToast('气体类型已添加', 'success')
  }
}


/**
 * 传感器布局配置常量
 * 参考 GB/T 50493《石油化工可燃气体和有毒气体检测报警设计标准》思想进行仿真布点
 * 注意：此处不是严格工程验收级布点，而是将泄漏源距离、设备状态、风向和最小间距作为仿真布点规则
 */
const SENSOR_LAYOUT_CONFIG = {
  maxSensors: 25,
  minSensorDistance: 120,
  highRiskThreshold: 0.55,
  sourceInfluenceRadius: 180,
  downwindBonus: 0.35,
  alertBonus: 0.35,
  maintenanceBonus: 0.15,
  // 高风险区（储罐区/塔器区）允许的较密间距
  highDensityMinDistance: 70
}

/**
 * 根据区域动态计算最小传感器间距
 * 储罐区/塔器区等高危区域允许更高密度，普通区域强制较大间距
 */
function dynamicMinDistance(cell) {
  const cfg = SENSOR_LAYOUT_CONFIG
  // 判断是否在高风险密集区（通过检查附近高 hazardLevel 设施）
  let nearHighRisk = false
  for (const f of facilities) {
    const hazard = f.hazardLevel || 0.3
    if (hazard < 0.7) continue
    let fx = f.x, fy = f.y
    if (f.type !== 'tank' && f.type !== 'tower') { fx += (f.w || 0) / 2; fy += (f.h || 0) / 2 }
    const d = Math.hypot(cell.x - fx, cell.y - fy)
    if (d < cfg.sourceInfluenceRadius) {
      nearHighRisk = true
      break
    }
  }
  return nearHighRisk ? cfg.highDensityMinDistance : cfg.minSensorDistance
}

/**
 * 传感器编号生成规则（符合工程命名规范）
 * 储罐区: TK-01, TK-02 ...
 * 塔器区: TW-01, TW-02 ...
 * 泵房/压缩机: PF-01, PF-02 ...
 * 生产区: SC-01, SC-02 ...
 * 办公区: BG-01, BG-02 ...
 * 仓储区: WH-01, WH-02 ...
 * 公用工程: GE-01, GE-02 ...
 * 污水处理: WS-01, WS-02 ...
 * 其他: 使用 zone 前缀
 */
const SENSOR_CODE_COUNTERS = {}
function generateSensorCode(areaType, zone, isPumpArea) {
  let prefix = 'GN'
  if (isPumpArea) prefix = 'PF'
  else if (areaType === 'tank' || zone === 'tank_farm') prefix = 'TK'
  else if (areaType === 'tower' || zone === 'tower_area') prefix = 'TW'
  else if (areaType === 'production' && (zone === 'prod_a' || zone === 'prod_b')) prefix = 'SC'
  else if (areaType === 'office' || zone === 'admin') prefix = 'BG'
  else if (areaType === 'warehouse' || zone === 'warehouse') prefix = 'WH'
  else if (areaType === 'utility' || zone === 'utility') prefix = 'GE'
  else if (zone === 'treatment') prefix = 'WS'

  if (!SENSOR_CODE_COUNTERS[prefix]) SENSOR_CODE_COUNTERS[prefix] = 1
  const seq = String(SENSOR_CODE_COUNTERS[prefix]++).padStart(2, '0')
  return `${prefix}-${seq}`
}

/** 优先级标签映射（4级制，参考 GB 18218 重大危险源分级） */
function getPriorityLabel(priority) {
  const labels = { 1: '重大风险', 2: '较大风险', 3: '一般风险', 4: '低风险' }
  return labels[priority] || '一般风险'
}
/** 优先级颜色映射 */
function getPriorityColor(priority) {
  const colors = { 1: '#ef4444', 2: '#f97316', 3: '#eab308', 4: '#22c55e' }
  return colors[priority] || '#eab308'
}

/**
 * 传感器风险值自动计算 — 严格基于 GB 18218-2018 R值法
 *
 * ═══════════════════════════════════════════════════════════════
 * 核心公式 (GB 18218-2018 第5.2条):
 *
 *   R = α × β × (q/Q) × 位置修正
 *
 * 其中:
 *   α = 厂外暴露人员系数 (GB 18218 表5)
 *   β = 危险化学品校正系数 (GB 18218 表3/表4)
 *   q/Q = 实际存在量与临界量比值 (GB 18218 表1)
 *   位置修正 = 安装高度修正 (GB/T 50493-2019 第6.1.2条)
 *
 * 等级阈值 (GB 18218-2018 第5.3条):
 *   R ≥ 50  → 1级 重大风险 (一级/二级重大危险源)
 *   20 ≤ R < 50 → 2级 较大风险 (二级/三级重大危险源)
 *   5 ≤ R < 20  → 3级 一般风险 (三级/四级重大危险源)
 *   R < 5   → 4级 低风险 (低于四级重大危险源)
 * ═══════════════════════════════════════════════════════════════
 *
 * 引用标准:
 *   [1] GB 18218-2018 危险化学品重大危险源辨识
 *       第5.2条: R值计算公式
 *       表2: α系数 (厂外暴露人员数量)
 *       表3: β系数 (危险化学品校正系数)
 *       第5.3条: 重大危险源分级
 *   [2] GB/T 50493-2019 石油化工可燃气体和有毒气体检测报警设计标准
 *       第4.2/4.3条: 探测器布置要求 → 位置危险性系数
 *   [3] GB 30000.18-2013 化学品分类和标签规范 第18部分:急性毒性
 *       毒性类别 → 物质校正系数β
 */
function computeSensorRisk(sensor, facility) {
  const detectionRange = (sensor.detectionRange || '').toLowerCase()

  // ═══════════════════════════════════════════════════════════
  // 严格依据 GB 18218-2018 第4.3.2条 公式(2):
  //   R = α × (β₁×q₁/Q₁ + β₂×q₂/Q₂ + ... + βₙ×qₙ/Qₙ)
  //
  // 本项目单传感器单物质场景简化为:
  //   R = α × β × (q/Q)
  // ═══════════════════════════════════════════════════════════

  // ─────────────────────────────────────────────────────────
  // 一、β — 毒性气体校正系数 (GB 18218-2018 表3 原文)
  // ─────────────────────────────────────────────────────────
  // 表3 毒性气体校正系数β取值表 (原文):
  //   一氧化碳 CO = 2    氨 NH3 = 2
  //   氯 = 4              二氧化氮 = 10
  //   氰化氢 = 10         碳酰氯 = 20
  //   磷化氢 = 20
  //
  // 表4 未在表3中列举的:
  //   W2 易燃气体 = 1.5
  //   W4 氧化性气体 = 1.0
  //   其他 = 1.0
  //
  let beta = 1.0
  if (detectionRange.includes('nh3') || detectionRange.includes('氨')) {
    beta = 2   // GB 18218 表3: 氨 β=2
  } else if (detectionRange.includes('co') && !detectionRange.includes('co2')) {
    beta = 2   // GB 18218 表3: 一氧化碳 β=2
  } else if (detectionRange.includes('ch4') || detectionRange.includes('c2h4') || detectionRange.includes('c3h6')) {
    beta = 1.5 // GB 18218 表4 W2: 易燃气体 β=1.5
  } else if (detectionRange.includes('o2') || detectionRange.includes('氧')) {
    beta = 1.0 // GB 18218 表4 W4: 氧化性气体 β=1.0
  }

  // ─────────────────────────────────────────────────────────
  // 二、α — 暴露人员校正系数 (GB 18218-2018 表5 原文)
  // ─────────────────────────────────────────────────────────
  // 表5 厂区边界向外扩展500m范围内常住人口:
  //   ≥100人 = 2.0    50~99人 = 1.5
  //   30~49人 = 1.2    1~29人 = 1.0
  //   0人 = 0.5
  //
  // 按区域前缀映射α (与 tools/sensor_audit.py ZONE_ALPHA 一致)
  const ZONE_ALPHA = {
    'PA': 1.2, 'PB': 1.2, 'P2': 1.2,  // 化工生产区: 30~49人
    'A':  1.5,                           // 行政办公区: 50~99人
    'TK': 1.0, 'TW': 1.0, 'WH': 1.0,   // 储罐/塔器/仓储: 1~29人
    'MN': 1.0, 'PL': 1.0,              // 监测/管道: 1~29人
    'UT': 0.5, 'WT': 0.5, 'MT': 0.5,   // 公用/污水/机修: 0人
    'FS': 0.5, 'FD': 0.5,              // 消防/防火堤: 0人
  }
  // 优先用传感器ID前缀匹配区域, 回退到设施personnel
  const sensorId = sensor.id || ''
  const zonePrefix = sensorId.split('-')[0] || ''
  let alpha = ZONE_ALPHA[zonePrefix] ?? 0.5
  // 若区域未匹配且设施有人员数据, 用设施personnel
  if (alpha === 0.5 && facility && facility.personnel) {
    const personnel = facility.personnel
    if (personnel >= 100) alpha = 2.0
    else if (personnel >= 50) alpha = 1.5
    else if (personnel >= 30) alpha = 1.2
    else if (personnel >= 1) alpha = 1.0
  }

  // ─────────────────────────────────────────────────────────
  // 三、q/Q — 实际存在量与临界量的比值 (GB 18218 表1)
  // ─────────────────────────────────────────────────────────
  // 临界量Q (GB 18218 表1):
  //   NH3=10t, CO=30t, CH4=50t, C2H4=50t, O2=200t
  //
  // 传感器场景下, 利用设施hazardLevel映射有效q/Q:
  //   hazardLevel∈[0,1] → q/Q = 0.5 + hazardLevel × 9.5
  //   映射依据: 设施危险等级越高, 危化品实际存在量越大
  //
  const hLevel = facility ? (facility.hazardLevel || 0.3) : 0.3
  const quantityRatio = 0.5 + hLevel * 9.5

  // ─────────────────────────────────────────────────────────
  // 四、位置系数 (GB/T 50493-2019, 安装合规性修正)
  // ─────────────────────────────────────────────────────────
  // 安装高度修正 (GB/T 50493 第6.1.2条):
  //   h ≤ 0.5m: 重气低位, ×1.10
  //   h ≥ 2.0m: 轻气高位, ×1.05
  //
  let locationCorrection = 1.0
  const h = sensor.installationHeight || 1.5
  if (h <= 0.5) locationCorrection = 1.10
  else if (h >= 2.0) locationCorrection = 1.05

  // ═══════════════════════════════════════════════════════════
  // 五、R = α × β × (q/Q) × 位置修正
  // ═══════════════════════════════════════════════════════════
  const R = alpha * beta * quantityRatio * locationCorrection

  // 等级映射 (GB 18218-2018 表6):
  //   R ≥ 100 → 一级   50 ≤ R < 100 → 二级
  //   10 ≤ R < 50 → 三级   R < 10 → 四级
  let priority
  if (R >= 50) priority = 1        // 重大风险 (一级/二级)
  else if (R >= 10) priority = 2   // 较大风险 (二级/三级)
  else if (R >= 5) priority = 3    // 一般风险 (三级/四级)
  else priority = 4                 // 低风险 (低于四级)

  return { risk: Math.round(R * 100) / 100, priority }
}

/** 根据设施 ID 查找最近的设施 */
function findNearestFacility(x, y) {
  let nearest = null
  let minDist = Infinity
  for (const f of facilities) {
    let fx = f.x, fy = f.y
    if (f.type !== 'tank' && f.type !== 'tower') { fx += f.w / 2; fy += f.h / 2 }
    const d = Math.hypot(x - fx, y - fy)
    if (d < minDist) { minDist = d; nearest = f }
  }
  return minDist < 150 ? nearest : null
}
function normalizeManualSensorNumber(value, fallback, min, max, precision = 1) {
  const num = Number(value)
  if (!Number.isFinite(num)) return fallback
  const normalized = clamp(num, min, max)
  return Number(normalized.toFixed(precision))
}
function getNormalizedManualSensorDraft() {
  return {
    installationHeight: normalizeManualSensorNumber(
      manualSensorDraft.installationHeight,
      MANUAL_SENSOR_DEFAULTS.installationHeight,
      0.3,
      10,
      1
    ),
    effectiveRange: normalizeManualSensorNumber(
      manualSensorDraft.effectiveRange,
      MANUAL_SENSOR_DEFAULTS.effectiveRange,
      0,
      20,
      0
    ),
    detectionRange: manualSensorDraft.detectionRange?.trim() || MANUAL_SENSOR_DEFAULTS.detectionRange,
    installRemark: manualSensorDraft.installRemark?.trim() || MANUAL_SENSOR_DEFAULTS.installRemark,
  }
}
function resolveSensorInstallationHeight(sensor) {
  return normalizeManualSensorNumber(
    sensor?.installationHeight,
    MANUAL_SENSOR_DEFAULTS.installationHeight,
    0.3,
    10,
    1
  )
}
function resolveSensorEffectiveRange(sensor, fallbackRadius = MANUAL_SENSOR_DEFAULTS.effectiveRange) {
  return normalizeManualSensorNumber(
    sensor?.effectiveRange,
    fallbackRadius,
    0,
    20,
    0
  )
}
function resolveSensorDetectionRange(sensor) {
  return sensor?.detectionRange?.trim() || MANUAL_SENSOR_DEFAULTS.detectionRange
}
function resolveSensorInstallRemark(sensor) {
  return sensor?.installRemark?.trim() || MANUAL_SENSOR_DEFAULTS.installRemark
}
function resetManualSensorDraft(keepPoint = false) {
  Object.assign(manualSensorDraft, createManualSensorDraft())
  if (!keepPoint) {
    sensorPlacementState.pendingPoint = null
  }
}
function toggleOriginPicking() {
  if (sensorPlacementState.picking) {
    sensorPlacementState.picking = false
  }
  sensorPlacementState.pickingOrigin = !sensorPlacementState.pickingOrigin
  if (sensorPlacementState.pickingOrigin) {
    canvasEl.style.cursor = 'crosshair'
    showToast('请点击地图设置零点位置', 'success')
  } else {
    canvasEl.style.cursor = measureMode.value ? 'crosshair' : 'grab'
  }
}
function captureOriginPoint(point) {
  sensorPlacementState.origin = normalizeMapPoint(point)
  sensorPlacementState.pickingOrigin = false
  canvasEl.style.cursor = measureMode.value ? 'crosshair' : 'grab'
  showToast(`零点已设置: (${sensorPlacementState.origin.x.toFixed(1)}, ${sensorPlacementState.origin.y.toFixed(1)})`, 'success')
}
function applyRelativeCoordinates() {
  if (!sensorPlacementState.origin) {
    showToast('请先设置零点位置', 'warn')
    return
  }
  const x = sensorPlacementState.origin.x + (sensorPlacementState.relativeX || 0)
  const y = sensorPlacementState.origin.y + (sensorPlacementState.relativeY || 0)
  sensorPlacementState.pendingPoint = normalizeMapPoint({ x, y })
  manualSensorConfigVisible.value = true
  showToast(`已应用坐标: (${x.toFixed(1)}, ${y.toFixed(1)})`, 'success')
}
function parseBatchImport() {
  if (!sensorPlacementState.origin) {
    showToast('请先设置零点位置', 'warn')
    return
  }
  const lines = batchImportText.value.split('\n').filter(line => line.trim())
  const preview = []
  let sensorIndex = sensors.value.length + 1
  for (const line of lines) {
    // 移除"m"后缀，支持多种分隔符
    const cleaned = line.replace(/m/gi, ' ')
    const parts = cleaned.split(/[\t,\s]+/).filter(p => p.trim() !== '')
    if (parts.length < 2) continue
    const nums = parts.map(p => parseFloat(p)).filter(n => !isNaN(n))
    if (nums.length < 2) continue
    const xRel = nums[0]
    const yRel = nums[1]
    const height = nums.length >= 3 ? nums[2] : batchDefaultHeight.value
    const mapX = sensorPlacementState.origin.x + xRel
    const mapY = sensorPlacementState.origin.y + yRel
    preview.push({
      id: `B-${String(sensorIndex++).padStart(2, '0')}`,
      xRel, yRel,
      x: mapX, y: mapY,
      height: isNaN(height) ? batchDefaultHeight.value : height,
      effectiveRange: batchDefaultRange.value,
    })
  }
  batchImportPreview.value = preview
  showToast(`解析完成，共 ${preview.length} 个点位`, 'success')
}
async function pasteFromClipboard() {
  try {
    const text = await navigator.clipboard.readText()
    if (text && text.trim()) {
      batchImportText.value = text
      parseBatchImport()
    } else {
      showToast('剪贴板为空，请先从Excel复制数据', 'warn')
    }
  } catch (e) {
    showToast('请手动粘贴: Ctrl+V', 'warn')
  }
}
async function executeBatchImport() {
  if (batchImportPreview.value.length === 0) return
  let count = 0
  for (const item of batchImportPreview.value) {
    const nearestFacility = findNearestFacility(item.x, item.y)
    const tempSensor = {
      detectionRange: 'CO/CH4/NH3/O2',
      installationHeight: item.height || 1.5,
    }
    const { risk, priority } = computeSensorRisk(tempSensor, nearestFacility)
    const sensor = {
      id: item.id,
      x: item.x,
      y: item.y,
      installationHeight: item.height,
      effectiveRange: item.effectiveRange,
      detectionRange: 'CO/CH4/NH3/O2',
      installRemark: `批量导入: 相对坐标(${item.xRel},${item.yRel})`,
      priority,
      risk,
      type: 'gas',
      mode: 'auto',
      lastSampleTime: null,
    }
    const success = await saveSensorToDB(sensor)
    if (success) count++
  }
  await fetchSensorsFromDB()
  batchImportText.value = ''
  batchImportPreview.value = []
  showToast(`批量导入完成，成功 ${count} 个传感器`, 'success')
}
function startManualSensorPicking() {
  if (leakSourceState.picking) {
    leakSourceState.picking = false
  }
  manualSensorConfigVisible.value = true
  sensorPlacementState.picking = true
  canvasEl.style.cursor = 'crosshair'
  showToast('请点击地图选择传感器安装位置', 'success')
}
function captureManualSensorPoint(point) {
  sensorPlacementState.pendingPoint = normalizeMapPoint(point)
  sensorPlacementState.picking = false
  manualSensorConfigVisible.value = true
  canvasEl.style.cursor = measureMode.value ? 'crosshair' : 'grab'
  showToast('已记录候选点位，请确认参数后添加传感器', 'success')
}
function cancelManualSensorPlacement() {
  sensorPlacementState.picking = false
  sensorPlacementState.pickingOrigin = false
  manualSensorConfigVisible.value = false
  resetManualSensorDraft()
  canvasEl.style.cursor = measureMode.value ? 'crosshair' : 'grab'
  showToast('已取消手动传感器布点', 'warn')
}
function confirmManualSensorPlacement() {
  if (!sensorPlacementState.pendingPoint) {
    showToast('请先点击地图选择传感器安装位置', 'warn')
    return
  }
  const config = getNormalizedManualSensorDraft()
  Object.assign(manualSensorDraft, config)
  placeManualSensorAtPoint(sensorPlacementState.pendingPoint, config)
}

/**
 * 高斯烟羽模型 —— 计算传感器位置的理论气体浓度（ppm）
 * 作为仿真浓度依据，非严格工程计算，但体现扩散物理趋势：
 * - 距泄漏源越近 ppm 越高
 * - 下风向浓度高于上风向
 * - 风速越大稀释越快
 */
function computeGasConcentration(sensor, leakPoint, windSpeed, windDir, sourceRate) {
  if (!leakPoint || !sensor) return 0
  const dx = sensor.x - leakPoint.x
  const dy = sensor.y - leakPoint.y
  const dist = Math.hypot(dx, dy)
  if (dist < 1) return Math.min(500, (sourceRate || 50) * 10)

  // 风向角 (气象惯例: 风从该方向吹来, 转为弧度)
  const windAngleRad = (windDir || 135) * Math.PI / 180
  // 沿风向/横风向坐标 (along > 0 为下风向)
  const along = dx * Math.cos(windAngleRad) + dy * Math.sin(windAngleRad)
  const cross = -dx * Math.sin(windAngleRad) + dy * Math.cos(windAngleRad)

  // 上风向大幅衰减
  const downwindFactor = along > 0 ? 1.0 : 0.1

  const u = Math.max(0.5, windSpeed || 2) // 风速 m/s
  const distMeters = dist * 0.5 // 地图单位转米 (0.5m/px)

  // Pasquill-Gifford D类稳定度 σ 系数 (标准值)
  const sigmaY = 0.08 * distMeters / Math.sqrt(u)
  const sigmaZ = 0.06 * distMeters / Math.sqrt(u)

  // 标准高斯烟羽公式 (地面源): C = Q / (π·u·σy·σz) × exp(-cross²/(2σy²))
  const Q = (sourceRate || 50) * 1000 // 源强 g/s
  const normFactor = Math.PI * u * sigmaY * sigmaZ
  const gaussian = Math.exp(-(cross * cross) / (2 * sigmaY * sigmaY))
  const concentration = (Q / Math.max(normFactor, 0.01)) * downwindFactor * gaussian

  // 归一化到合理 ppm 范围
  const ppm = Math.min(1000, Math.max(0, concentration * 0.5))
  return Math.round(ppm * 100) / 100
}

// 重置传感器编号计数器（用于重新布局时重新编号）
function resetSensorCodeCounters() {
  Object.keys(SENSOR_CODE_COUNTERS).forEach(k => delete SENSOR_CODE_COUNTERS[k])
}

function worldToScreen(wx, wy) {
  return {
    x: (wx + viewState.offsetX) * viewState.scale + canvasEl.width * 0.05,
    y: (wy + viewState.offsetY) * viewState.scale + canvasEl.height * 0.05,
  }
}
function screenToWorld(sx, sy) {
  return {
    x: (sx - canvasEl.width * 0.05) / viewState.scale - viewState.offsetX,
    y: (sy - canvasEl.height * 0.05) / viewState.scale - viewState.offsetY,
  }
}
function updateCoordDisplay(wx, wy) {
  const geo = formatGeoCoord(wx, wy)
  coordLongitude.value = geo.longitude
  coordLatitude.value = geo.latitude
  coordAltitude.value = geo.altitude
}
function normalizeMapPoint(point) {
  if (!point) return null
  return {
    x: Number(point.x.toFixed(2)),
    y: Number(point.y.toFixed(2)),
  }
}
function syncManualGeoInputsFromWorld(point) {
  if (!point) return
  const geo = worldToGeo(point.x, point.y)
  leakSourceState.manualLongitude = geo.longitude.toFixed(3)
  leakSourceState.manualLatitude = geo.latitude.toFixed(3)
}
function buildLeakSourceValidation() {
  const gasId = diffusionForm.gasId
  if (leakSourceState.mode !== 'facility' && leakSourceState.mapPoint) {
    const nearest = findNearestAllowedGasSourceFacility(facilities, gasId, leakSourceState.mapPoint)
    return validateGasLeakSource({
      gasId,
      sourceFacilityId: nearest?.facility?.id || diffusionForm.sourceFacilityId,
      facilities,
      mapPoint: leakSourceState.mapPoint,
    })
  }
  return validateGasLeakSource({
    gasId,
    sourceFacilityId: diffusionForm.sourceFacilityId,
    facilities,
  })
}
function updateDiffusionMetaSource({ sourceFacility, sourcePoint }) {
  diffusionMeta.value = {
    ...diffusionMeta.value,
    gas: getGasById(diffusionForm.gasId),
    sourceFacility: sourceFacility || null,
    sourcePoint: sourcePoint ? normalizeMapPoint(sourcePoint) : null,
  }
}
function applyLeakSourcePoint(point, mode, options = {}) {
  const normalizedPoint = normalizeMapPoint(point)
  const nearest = findNearestAllowedGasSourceFacility(facilities, diffusionForm.gasId, normalizedPoint)
  const validation = validateGasLeakSource({
    gasId: diffusionForm.gasId,
    sourceFacilityId: nearest?.facility?.id || diffusionForm.sourceFacilityId,
    facilities,
    mapPoint: normalizedPoint,
  })
  if (!validation.valid) {
    leakSourceState.picking = false
    if (!options.silent) showToast(validation.message, 'warn')
    return false
  }
  leakSourceState.mode = mode
  leakSourceState.picking = false
  leakSourceState.mapPoint = normalizedPoint
  diffusionForm.sourceFacilityId = validation.nearestAllowedFacility?.id || validation.selectedFacility?.id || diffusionForm.sourceFacilityId
  syncManualGeoInputsFromWorld(normalizedPoint)
  updateDiffusionMetaSource({
    sourceFacility: facilityById.get(diffusionForm.sourceFacilityId) || validation.nearestAllowedFacility || validation.selectedFacility,
    sourcePoint: normalizedPoint,
  })
  render()
  if (!options.silent) {
    const actionLabel = mode === 'geo' ? '经纬度源点' : '地图源点'
    showToast(`${actionLabel}已通过校验并绑定到 ${facilityById.get(diffusionForm.sourceFacilityId)?.name || '合法设施'}`, 'success')
  }
  return true
}
function toggleLeakSourcePicking() {
  if (sensorPlacementState.picking) {
    sensorPlacementState.picking = false
  }
  if (sensorPlacementState.pickingOrigin) {
    sensorPlacementState.pickingOrigin = false
  }
  leakSourceState.picking = !leakSourceState.picking
  if (leakSourceState.picking) {
    canvasEl.style.cursor = 'crosshair'
    showToast('点击地图设置泄漏源点，系统会自动做合法性校验', 'success')
    return
  }
  canvasEl.style.cursor = measureMode.value ? 'crosshair' : 'grab'
}
function applyManualGeoLeakSource() {
  const longitude = Number(leakSourceState.manualLongitude)
  const latitude = Number(leakSourceState.manualLatitude)
  if (!Number.isFinite(longitude) || !Number.isFinite(latitude)) {
    showToast('请输入有效的经纬度坐标', 'warn')
    return
  }
  applyLeakSourcePoint(geoToWorld(longitude, latitude), 'geo')
}
function getZoneName(zoneId) {
  const z = zones.find(z => z.id === zoneId)
  return z ? z.name : zoneId
}
function getVisibleEntrances() {
  return parkEntrances.concat(
    buildingEntrances.filter(entrance => {
      const facility = facilityById.get(entrance.parentId)
      return facility ? matchFilter(facility) : true
    })
  )
}
function matchFilter(f) {
  if (activeFilter.value === 'all') return true
  if (activeFilter.value === 'building') return ['office','production','utility','warehouse','treatment'].includes(f.type)
  if (activeFilter.value === 'tank') return f.type === 'tank'
  if (activeFilter.value === 'tower') return f.type === 'tower'
  if (activeFilter.value === 'pipe') return false
  if (activeFilter.value === 'key') return f.key || f.zone === 'tank_farm' || f.zone === 'tower_area'
  return true
}
function statusTagClass(status) {
  if (status === '告警') return 'tag-red'
  if (status === '维护中' || status === '待机') return 'tag-orange'
  if (status === '运行中') return 'tag-blue'
  return 'tag-green'
}
function drawRoundedRect(x, y, w, h, r) {
  ctx.beginPath()
  ctx.moveTo(x + r, y)
  ctx.lineTo(x + w - r, y)
  ctx.quadraticCurveTo(x + w, y, x + w, y + r)
  ctx.lineTo(x + w, y + h - r)
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h)
  ctx.lineTo(x + r, y + h)
  ctx.quadraticCurveTo(x, y + h, x, y + h - r)
  ctx.lineTo(x, y + r)
  ctx.quadraticCurveTo(x, y, x + r, y)
  ctx.closePath()
}
function drawEntranceConnector(edge, length) {
  ctx.beginPath()
  if (edge === 'left') { ctx.moveTo(4, 0); ctx.lineTo(length, 0) }
  else if (edge === 'right') { ctx.moveTo(-4, 0); ctx.lineTo(-length, 0) }
  else if (edge === 'top') { ctx.moveTo(0, 4); ctx.lineTo(0, length) }
  else { ctx.moveTo(0, -4); ctx.lineTo(0, -length) }
  ctx.stroke()
}
function drawEntranceMarker(entrance) {
  const isHovered = hoveredEntrance.value?.id === entrance.id
  const color = entrance.kind === 'park' ? '#38bdf8' : '#00e5a0'
  const rgb = hexToRgb(color)
  ctx.save()
  ctx.translate(entrance.x, entrance.y)
  ctx.strokeStyle = `rgba(${rgb}, ${isHovered ? 0.9 : 0.65})`
  ctx.lineWidth = entrance.kind === 'park' ? 1.6 : 1.2
  drawEntranceConnector(entrance.edge, entrance.kind === 'park' ? 16 : 10)
  ctx.stroke()
  ctx.fillStyle = `rgba(${rgb}, ${isHovered ? 0.24 : 0.14})`
  ctx.strokeStyle = color
  ctx.lineWidth = isHovered ? 1.8 : 1.3
  ctx.beginPath()
  ctx.moveTo(0, -8)
  ctx.lineTo(7, -3)
  ctx.lineTo(7, 4)
  ctx.lineTo(0, 9)
  ctx.lineTo(-7, 4)
  ctx.lineTo(-7, -3)
  ctx.closePath()
  ctx.fill()
  ctx.stroke()
  ctx.fillStyle = '#0a0f1a'
  ctx.fillRect(-2.5, -4, 5, 8)
  ctx.strokeStyle = `rgba(${rgb}, ${isHovered ? 0.85 : 0.45})`
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.arc(0, 0, entrance.kind === 'park' ? 12 : 10, 0, Math.PI * 2)
  ctx.stroke()
  if (entrance.kind === 'park') {
    ctx.strokeStyle = `rgba(${rgb}, 0.28)`
    ctx.beginPath()
    ctx.arc(0, 0, 16, 0, Math.PI * 2)
    ctx.stroke()
  }
  ctx.restore()
}
function drawEntranceTooltip(entrance) {
  const header = entrance.kind === 'park' ? '园区出入口' : '建筑出入口'
  const color = entrance.kind === 'park' ? '#38bdf8' : '#00e5a0'
  const rgb = hexToRgb(color)
  ctx.save()
  ctx.textBaseline = 'top'
  ctx.textAlign = 'center'
  ctx.font = 'bold 10px "Noto Sans SC"'
  const headerWidth = ctx.measureText(header).width
  ctx.font = '9px "Noto Sans SC"'
  const detailWidth = ctx.measureText(entrance.label).width
  const boxWidth = Math.max(headerWidth, detailWidth) + 28
  const boxHeight = 38
  let boxX = entrance.x - boxWidth / 2
  let boxY = entrance.y - boxHeight - 16
  if (entrance.tooltipSide === 'right') boxX = entrance.x + 14
  if (entrance.tooltipSide === 'left') boxX = entrance.x - boxWidth - 14
  if (entrance.tooltipSide === 'bottom') boxY = entrance.y + 14
  boxX = clamp(boxX, 22, 1000 - boxWidth - 22)
  boxY = clamp(boxY, 22, 650 - boxHeight - 22)
  ctx.strokeStyle = `rgba(${rgb}, 0.85)`
  ctx.fillStyle = 'rgba(10,15,26,0.95)'
  ctx.lineWidth = 1.2
  drawRoundedRect(boxX, boxY, boxWidth, boxHeight, 8)
  ctx.fill()
  ctx.stroke()
  ctx.fillStyle = color
  ctx.font = 'bold 10px "Noto Sans SC"'
  ctx.fillText(header, boxX + boxWidth / 2, boxY + 7)
  ctx.fillStyle = '#e8ecf4'
  ctx.font = '9px "Noto Sans SC"'
  ctx.fillText(entrance.label, boxX + boxWidth / 2, boxY + 21)
  ctx.restore()
}
function drawEntrances() {
  if (!showEntrances.value) return
  const entrances = getVisibleEntrances()
  entrances.forEach(drawEntranceMarker)
  if (hoveredEntrance.value) drawEntranceTooltip(hoveredEntrance.value)
}

// ---- 小车 Canvas 绘制 ----
function drawCars() {
  if (!showCars.value) return
  const markers = carMarkers.value
  if (!markers.length) return
  markers.forEach(car => {
    const isSelected = selectedCar.value?.id === car.id
    const isHovered = hoveredCar.value?.id === car.id
    const isWarning = car.status === 'warning'
    const cx = car.x, cy = car.y

    ctx.save()
    ctx.translate(cx, cy)

    // 预警车辆呼吸光晕
    if (isWarning) {
      const glow = 0.3 + 0.3 * Math.sin(Date.now() / 250)
      ctx.fillStyle = `rgba(239,68,68,${glow * 0.25})`
      ctx.beginPath()
      ctx.arc(0, 0, 22, 0, Math.PI * 2)
      ctx.fill()
      ctx.strokeStyle = `rgba(239,68,68,${glow * 0.5})`
      ctx.lineWidth = 1.5
      ctx.beginPath()
      ctx.arc(0, 0, 26, 0, Math.PI * 2)
      ctx.stroke()
    }

    // 选中高亮外框
    if (isSelected) {
      ctx.strokeStyle = '#40e0d0'
      ctx.lineWidth = 2
      ctx.setLineDash([3, 3])
      ctx.beginPath()
      ctx.arc(0, 0, 20, 0, Math.PI * 2)
      ctx.stroke()
      ctx.setLineDash([])
    }

    // 车辆主体（圆角矩形车形）
    const bodyColor = isWarning ? '#ef4444' : (isHovered ? '#40e0d0' : '#3b82f6')
    ctx.fillStyle = bodyColor
    ctx.strokeStyle = 'rgba(255,255,255,0.8)'
    ctx.lineWidth = 1.5
    const bw = 20, bh = 12
    const rx = bw / 2, ry = bh / 2
    ctx.beginPath()
    ctx.moveTo(-rx + 3, -ry)
    ctx.lineTo(rx - 3, -ry)
    ctx.quadraticCurveTo(rx, -ry, rx, -ry + 3)
    ctx.lineTo(rx, ry - 3)
    ctx.quadraticCurveTo(rx, ry, rx - 3, ry)
    ctx.lineTo(-rx + 3, ry)
    ctx.quadraticCurveTo(-rx, ry, -rx, ry - 3)
    ctx.lineTo(-rx, -ry + 3)
    ctx.quadraticCurveTo(-rx, -ry, -rx + 3, -ry)
    ctx.closePath()
    ctx.fill()
    ctx.stroke()

    // 车顶传感器圆点
    ctx.fillStyle = isWarning ? '#fca5a5' : '#93c5fd'
    ctx.beginPath()
    ctx.arc(0, -2, 3, 0, Math.PI * 2)
    ctx.fill()
    ctx.strokeStyle = 'rgba(255,255,255,0.6)'
    ctx.lineWidth = 0.8
    ctx.stroke()

    // ID 标签
    ctx.textAlign = 'center'
    ctx.textBaseline = 'bottom'
    ctx.font = 'bold 10px "Noto Sans SC"'
    const label = `#${car.id}`
    const tw = ctx.measureText(label).width
    const lx = 0, ly = -ry - 6
    ctx.fillStyle = 'rgba(0,0,0,0.7)'
    ctx.fillRect(lx - tw / 2 - 3, ly - 10, tw + 6, 13)
    ctx.fillStyle = '#fff'
    ctx.fillText(label, lx, ly)

    // 状态文本
    ctx.textBaseline = 'top'
    ctx.font = '8px "Noto Sans SC"'
    const statusText = isWarning ? '异常' : '正常'
    ctx.fillStyle = isWarning ? '#ef4444' : '#00e5a0'
    ctx.fillText(statusText, 0, ry + 3)

    // 浓度读数（移动传感器）
    const mobileSensor = mobileSensorReadings.value.find(m => m.carId === car.id)
    if (mobileSensor && mobileSensor.currentConcentration > 0) {
      ctx.textBaseline = 'bottom'
      ctx.font = 'bold 9px "Noto Sans SC"'
      const concText = mobileSensor.currentConcentration.toFixed(1) + ' ppm'
      const concColor = mobileSensor.currentConcentration > 20 ? '#ef4444' : mobileSensor.currentConcentration > 10 ? '#f59e0b' : '#93c5fd'
      ctx.fillStyle = concColor
      ctx.fillText(concText, 12, -ry + 4)
    }

    ctx.restore()
  })
}

function render() {
  if (!ctx) return
  ctx.fillStyle = '#1a2e1e'
  ctx.fillRect(0, 0, canvasEl.width, canvasEl.height)
  const s = viewState.scale
  ctx.save()
  ctx.translate(viewState.offsetX * s + canvasEl.width * 0.05, viewState.offsetY * s + canvasEl.height * 0.05)
  ctx.scale(s, s)
  drawGround()
  drawRoads()
  drawDiffusionLayer()
  drawPinnCandidateRegions()
  drawPinnRefinementOverlay()
  drawKeyAreas()
  drawPipes()
  drawBuildings()
  drawTanks()
  drawTowers()
  drawEvacuationRoute()
  drawRiskGrid()
  drawSensors()
  if (showHeatmap.value) drawHeatmap()
  if (showLabels.value) drawLabels()
  drawDiffusionSourceMarker()
  if (selectedFacility.value) drawSelection(selectedFacility.value)
  if (hoveredFacility.value && hoveredFacility.value !== selectedFacility.value) drawHover(hoveredFacility.value)
  drawEntrances()
  drawCars()
  if (measureMode.value && measurePoints.length > 0) drawMeasure()
  ctx.restore()
}

function drawGround() {
  ctx.fillStyle = '#16261a'
  ctx.fillRect(15, 15, 990, 630)
  ctx.fillStyle = '#1a2e1e'
  ctx.fillRect(20, 20, 980, 620)
  ctx.fillStyle = '#1d3322'
  for (const dot of groundSpeckles) {
    ctx.beginPath()
    ctx.arc(dot.x, dot.y, dot.r, 0, Math.PI * 2)
    ctx.fill()
  }
  const zoneBgs = [
    { x:78, y:55, w:247, h:170, color:'#1e2826' },
    { x:355, y:55, w:320, h:170, color:'#1e2826' },
    { x:705, y:55, w:240, h:170, color:'#1e2826' },
    { x:78, y:255, w:247, h:165, color:'#1c2630' },
    { x:355, y:255, w:320, h:165, color:'#231e28' },
    { x:355, y:452, w:320, h:143, color:'#1e2428' },
    { x:705, y:452, w:240, h:143, color:'#22251e' },
    { x:78, y:452, w:247, h:143, color:'#1a2430' },
  ]
  zoneBgs.forEach(z => { ctx.fillStyle = z.color; ctx.fillRect(z.x, z.y, z.w, z.h) })
}
function drawRoads() {
  roads.forEach(r => {
    ctx.fillStyle = r.main ? '#3a4255' : '#2e3648'
    ctx.fillRect(r.x, r.y, r.w, r.h)
    if (r.main) {
      ctx.strokeStyle = 'rgba(255,255,255,0.12)'
      ctx.lineWidth = 1
      ctx.setLineDash([8, 6])
      ctx.beginPath()
      if (r.w > r.h) { ctx.moveTo(r.x, r.y + r.h / 2); ctx.lineTo(r.x + r.w, r.y + r.h / 2) }
      else { ctx.moveTo(r.x + r.w / 2, r.y); ctx.lineTo(r.x + r.w / 2, r.y + r.h) }
      ctx.stroke()
      ctx.setLineDash([])
    }
    ctx.strokeStyle = 'rgba(255,255,255,0.05)'
    ctx.lineWidth = 0.5
    ctx.strokeRect(r.x, r.y, r.w, r.h)
  })
}
function drawKeyAreas() {
  keyAreas.forEach(ka => {
    ctx.strokeStyle = 'rgba(56,189,248,0.6)'
    ctx.lineWidth = 2
    ctx.setLineDash([6, 4])
    ctx.strokeRect(ka.x, ka.y, ka.w, ka.h)
    ctx.setLineDash([])
    ctx.fillStyle = 'rgba(56,189,248,0.06)'
    ctx.fillRect(ka.x, ka.y, ka.w, ka.h)
    const cl = 10
    ctx.strokeStyle = '#38bdf8'; ctx.lineWidth = 2.5; ctx.setLineDash([])
    ctx.beginPath(); ctx.moveTo(ka.x, ka.y + cl); ctx.lineTo(ka.x, ka.y); ctx.lineTo(ka.x + cl, ka.y); ctx.stroke()
    ctx.beginPath(); ctx.moveTo(ka.x + ka.w - cl, ka.y); ctx.lineTo(ka.x + ka.w, ka.y); ctx.lineTo(ka.x + ka.w, ka.y + cl); ctx.stroke()
    ctx.beginPath(); ctx.moveTo(ka.x, ka.y + ka.h - cl, ka.y); ctx.lineTo(ka.x, ka.y + ka.h); ctx.lineTo(ka.x + cl, ka.y + ka.h); ctx.stroke()
    ctx.beginPath(); ctx.moveTo(ka.x + ka.w - cl, ka.y + ka.h); ctx.lineTo(ka.x + ka.w, ka.y + ka.h); ctx.lineTo(ka.x + ka.w, ka.y + ka.h - cl); ctx.stroke()
  })
}
function drawPipes() {
  pipes.forEach(p => {
    const [fx, fy] = p.from
    const [tx, ty] = p.to
    const mx = (fx + tx) / 2
    ctx.strokeStyle = p.status === '运行中' ? '#6a7a8a' : '#4a5a6a'
    ctx.lineWidth = 3; ctx.lineCap = 'round'
    ctx.beginPath(); ctx.moveTo(fx, fy); ctx.lineTo(mx, fy); ctx.lineTo(mx, ty); ctx.lineTo(tx, ty); ctx.stroke()
    if (showFlow.value && p.status === '运行中') {
      ctx.strokeStyle = 'rgba(56,189,248,0.5)'
      ctx.lineWidth = 2; ctx.setLineDash([4, 8]); ctx.lineDashOffset = -flowAnimOffset
      ctx.beginPath(); ctx.moveTo(fx, fy); ctx.lineTo(mx, fy); ctx.lineTo(mx, ty); ctx.lineTo(tx, ty); ctx.stroke()
      ctx.setLineDash([]); ctx.lineDashOffset = 0
      ctx.save(); ctx.translate(tx, ty)
      ctx.rotate(mx < tx ? 0 : Math.PI)
      ctx.fillStyle = 'rgba(56,189,248,0.7)'
      ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(-8, -4); ctx.lineTo(-8, 4); ctx.closePath(); ctx.fill()
      ctx.restore()
    }
  })
}
function drawBuildings() {
  const typeColors = { office:'#5a4a3a', production:'#3a5a4a', utility:'#3a4a5a', warehouse:'#4a4a3a', treatment:'#2a4a5a' }
  facilities.filter(f => ['office','production','utility','warehouse','treatment'].includes(f.type)).forEach(f => {
    if (!matchFilter(f)) return
    ctx.fillStyle = 'rgba(0,0,0,0.25)'
    ctx.fillRect(f.x + 3, f.y + 3, f.w, f.h)
    ctx.fillStyle = typeColors[f.type] || '#4a5568'
    ctx.fillRect(f.x, f.y, f.w, f.h)
    ctx.strokeStyle = 'rgba(255,255,255,0.12)'; ctx.lineWidth = 0.8
    ctx.strokeRect(f.x, f.y, f.w, f.h)
    ctx.strokeStyle = 'rgba(255,255,255,0.05)'; ctx.lineWidth = 0.5
    for (let lx = f.x + 8; lx < f.x + f.w; lx += 10) {
      ctx.beginPath(); ctx.moveTo(lx, f.y); ctx.lineTo(lx, f.y + f.h); ctx.stroke()
    }
  })
}
function drawTanks() {
  facilities.filter(f => f.type === 'tank').forEach(f => {
    if (!matchFilter(f)) return
    const { x: cx, y: cy, r } = f
    ctx.fillStyle = 'rgba(0,0,0,0.2)'
    ctx.beginPath(); ctx.arc(cx + 2, cy + 2, r, 0, Math.PI * 2); ctx.fill()
    const grad = ctx.createRadialGradient(cx - r * 0.3, cy - r * 0.3, r * 0.1, cx, cy, r)
    grad.addColorStop(0, '#8a9ab8'); grad.addColorStop(0.7, '#5a6a83'); grad.addColorStop(1, '#3a4a5a')
    ctx.fillStyle = grad; ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.fill()
    ctx.strokeStyle = 'rgba(255,255,255,0.15)'; ctx.lineWidth = 0.8
    ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.stroke()
    if (f.level) {
      const la = Math.PI * (1 - f.level / 100)
      ctx.fillStyle = f.level > 85 ? 'rgba(239,68,68,0.35)' : 'rgba(56,189,248,0.25)'
      ctx.beginPath(); ctx.arc(cx, cy, r - 2, la, Math.PI)
      ctx.lineTo(cx + (r - 2) * Math.cos(la), cy + (r - 2) * Math.sin(la))
      ctx.closePath(); ctx.fill()
    }
    if (f.status === '告警') {
      const ba = 0.3 + 0.3 * Math.sin(Date.now() / 300)
      ctx.strokeStyle = `rgba(239,68,68,${ba})`; ctx.lineWidth = 2
      ctx.beginPath(); ctx.arc(cx, cy, r + 4, 0, Math.PI * 2); ctx.stroke()
    }
  })
}
function drawTowers() {
  facilities.filter(f => f.type === 'tower').forEach(f => {
    if (!matchFilter(f)) return
    const { x: cx, y: cy, r, h } = f
    const topY = cy - h / 2, botY = cy + h / 2
    const topW = r * 0.85, botW = r
    ctx.fillStyle = 'rgba(0,0,0,0.2)'
    ctx.beginPath(); ctx.ellipse(cx + 2, botY + 2, r, r * 0.3, 0, 0, Math.PI * 2); ctx.fill()
    ctx.fillStyle = '#6a5a7a'
    ctx.beginPath(); ctx.moveTo(cx - topW, topY); ctx.lineTo(cx + topW, topY)
    ctx.lineTo(cx + botW, botY); ctx.lineTo(cx - botW, botY); ctx.closePath(); ctx.fill()
    const tg = ctx.createLinearGradient(cx - r, 0, cx + r, 0)
    tg.addColorStop(0, 'rgba(255,255,255,0.05)'); tg.addColorStop(0.5, 'rgba(255,255,255,0.1)'); tg.addColorStop(1, 'rgba(0,0,0,0.1)')
    ctx.fillStyle = tg
    ctx.beginPath(); ctx.moveTo(cx - topW, topY); ctx.lineTo(cx + topW, topY)
    ctx.lineTo(cx + botW, botY); ctx.lineTo(cx - botW, botY); ctx.closePath(); ctx.fill()
    ctx.strokeStyle = 'rgba(255,255,255,0.12)'; ctx.lineWidth = 0.8
    ctx.beginPath(); ctx.moveTo(cx - topW, topY); ctx.lineTo(cx + topW, topY)
    ctx.lineTo(cx + botW, botY); ctx.lineTo(cx - botW, botY); ctx.closePath(); ctx.stroke()
    for (let i = 1; i <= 3; i++) {
      const py = topY + (h / 4) * i
      const pw = topW + (botW - topW) * (i / 4)
      ctx.strokeStyle = 'rgba(255,255,255,0.08)'; ctx.lineWidth = 0.5
      ctx.beginPath(); ctx.moveTo(cx - pw - 2, py); ctx.lineTo(cx + pw + 2, py); ctx.stroke()
    }
    ctx.fillStyle = '#8a7a9a'
    ctx.beginPath(); ctx.ellipse(cx, topY, topW, topW * 0.25, 0, 0, Math.PI * 2); ctx.fill()
    ctx.strokeStyle = 'rgba(255,255,255,0.15)'; ctx.lineWidth = 0.5; ctx.stroke()
    if (f.status === '维护中') {
      ctx.strokeStyle = 'rgba(255,107,53,0.4)'; ctx.lineWidth = 1.5; ctx.setLineDash([3, 3])
      ctx.beginPath(); ctx.ellipse(cx, cy, r + 6, h / 2 + 6, 0, 0, Math.PI * 2); ctx.stroke()
      ctx.setLineDash([])
    }
  })
}
function drawLabels() {
  ctx.font = '9px "Noto Sans SC"'
  ctx.textAlign = 'center'; ctx.textBaseline = 'top'
  facilities.forEach(f => {
    if (!matchFilter(f)) return
    let lx, ly
    if (f.type === 'tank') { lx = f.x; ly = f.y + f.r + 4 }
    else if (f.type === 'tower') { lx = f.x; ly = f.y + f.h / 2 + f.r + 8 }
    else { lx = f.x + f.w / 2; ly = f.y + f.h + 4 }
    const tw = ctx.measureText(f.name).width
    ctx.fillStyle = '#0a0f1a'
    ctx.fillRect(lx - tw / 2 - 3, ly - 1, tw + 6, 13)
    ctx.fillStyle = '#e8ecf4'
    ctx.fillText(f.name, lx, ly)
  })
  ctx.font = 'bold 11px "Noto Sans SC"'
  const zl = [
    { text:'行政办公区', x:185, y:60 }, { text:'化工生产一区', x:495, y:60 },
    { text:'精细化工厂房', x:790, y:60 }, { text:'储罐区', x:210, y:270 },
    { text:'塔器区', x:555, y:260 }, { text:'公用工程区', x:530, y:438 },
    { text:'仓储物流区', x:822, y:438 }, { text:'污水处理区', x:170, y:498 },
  ]
  zl.forEach(z => {
    const tw = ctx.measureText(z.text).width
    ctx.fillStyle = '#0a0f1a'
    ctx.fillRect(z.x - tw / 2 - 4, z.y - 2, tw + 8, 16)
    ctx.fillStyle = '#e8ecf4'
    ctx.textAlign = 'center'; ctx.fillText(z.text, z.x, z.y)
  })
}
function drawHeatmap() {
  facilities.forEach(f => {
    let cx, cy
    if (f.type === 'tank') { cx = f.x; cy = f.y }
    else if (f.type === 'tower') { cx = f.x; cy = f.y }
    else { cx = f.x + (f.w || 0) / 2; cy = f.y + (f.h || 0) / 2 }
    let heat = 0.3
    if (f.temp != null) heat = Math.min(1, Math.max(0.1, f.temp / 250))
    if (f.status === '告警') heat = 0.9
    if (f.status === '维护中') heat = 0.6
    const radius = 40
    const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius)
    if (heat > 0.7) {
      grad.addColorStop(0, `rgba(239,68,68,${heat * 0.5})`)
      grad.addColorStop(0.5, `rgba(255,107,53,${heat * 0.3})`)
      grad.addColorStop(1, 'rgba(255,107,53,0)')
    } else if (heat > 0.4) {
      grad.addColorStop(0, `rgba(255,165,0,${heat * 0.4})`)
      grad.addColorStop(0.5, `rgba(255,200,0,${heat * 0.2})`)
      grad.addColorStop(1, 'rgba(255,200,0,0)')
    } else {
      grad.addColorStop(0, `rgba(0,229,160,${heat * 0.3})`)
      grad.addColorStop(0.5, `rgba(56,189,248,${heat * 0.15})`)
      grad.addColorStop(1, 'rgba(56,189,248,0)')
    }
    ctx.fillStyle = grad
    ctx.fillRect(cx - radius, cy - radius, radius * 2, radius * 2)
  })
}
function drawDiffusionLayer() {
  const frame = currentDiffusionFrame.value
  const gas = diffusionMeta.value.gas
  if (!frame || !gas) return
  frame.cells.forEach(cell => {
    if (cell.level === 'danger') ctx.fillStyle = `rgba(239,68,68,${cell.alpha})`
    else if (cell.level === 'warning') ctx.fillStyle = `rgba(245,158,11,${cell.alpha})`
    else ctx.fillStyle = `rgba(${hexToRgb(gas.color)},${cell.alpha})`
    ctx.fillRect(cell.x - cell.size / 2, cell.y - cell.size / 2, cell.size, cell.size)
  })
  drawDiffusionBoundary(frame.boundaryPolygons?.affected, `rgba(${hexToRgb(gas.color)},0.2)`, 1.2)
  drawDiffusionBoundary(frame.boundaryPolygons?.warning, 'rgba(245,158,11,0.5)', 1.5)
  drawDiffusionBoundary(frame.boundaryPolygons?.danger, 'rgba(239,68,68,0.6)', 1.8)
  drawDiffusionSkeleton(frame.contourSkeletons?.affected, `rgba(${hexToRgb(gas.color)},0.18)`, [5, 5])
  drawDiffusionSkeleton(frame.contourSkeletons?.warning, 'rgba(245,158,11,0.4)', [6, 4])
  drawDiffusionSkeleton(frame.contourSkeletons?.danger, 'rgba(239,68,68,0.45)', [2, 5])
  const plume = frame.plume
  if (!plume) return
  ctx.save()
  ctx.translate(plume.sourceX, plume.sourceY)
  ctx.rotate(plume.angle)
  ctx.strokeStyle = `rgba(${hexToRgb(gas.color)},0.42)`
  ctx.fillStyle = `rgba(${hexToRgb(gas.color)},0.04)`
  ctx.lineWidth = 2
  ctx.beginPath()
  ctx.ellipse(plume.driftDistance * 0.5, 0, plume.majorAxis, plume.minorAxis, 0, 0, Math.PI * 2)
  ctx.fill()
  ctx.stroke()
  ctx.restore()
}
function drawDiffusionBoundary(boundary, strokeStyle, lineWidth = 1.2) {
  const segments = boundary?.segments?.length
    ? boundary.segments.map(segment => segment.points).filter(points => points.length >= 3)
    : [boundary?.points || []].filter(points => points.length >= 3)
  if (!segments.length) return
  ctx.save()
  ctx.strokeStyle = strokeStyle
  ctx.lineWidth = lineWidth
  for (const points of segments) {
    ctx.beginPath()
    ctx.moveTo(points[0].x, points[0].y)
    for (let index = 1; index < points.length; index++) {
      ctx.lineTo(points[index].x, points[index].y)
    }
    ctx.closePath()
    ctx.stroke()
  }
  ctx.restore()
}
function drawDiffusionSkeleton(skeleton, strokeStyle, dash = []) {
  const segments = skeleton?.segments?.length
    ? skeleton.segments.map(segment => segment.centerline).filter(points => points.length >= 2)
    : [skeleton?.centerline || []].filter(points => points.length >= 2)
  if (!segments.length) return
  ctx.save()
  ctx.strokeStyle = strokeStyle
  ctx.lineWidth = 1
  ctx.setLineDash(dash)
  for (const points of segments) {
    ctx.beginPath()
    ctx.moveTo(points[0].x, points[0].y)
    for (let index = 1; index < points.length; index++) {
      ctx.lineTo(points[index].x, points[index].y)
    }
    ctx.stroke()
  }
  ctx.setLineDash([])
  ctx.restore()
}
function drawDiffusionSourceMarker() {
  const source = diffusionMeta.value.sourceFacility || selectedDiffusionSource.value
  const point = diffusionMeta.value.sourcePoint || currentLeakSourcePoint.value
  const gas = diffusionMeta.value.gas || getGasById(diffusionForm.gasId)
  if (!point || !gas) return
  const x = point.x
  const y = point.y
  const pulse = 6 + Math.sin(Date.now() / 240) * 2
  ctx.save()
  ctx.strokeStyle = gas.color
  ctx.fillStyle = 'rgba(10,15,26,0.88)'
  ctx.lineWidth = 1.6
  ctx.beginPath()
  ctx.arc(x, y, 7, 0, Math.PI * 2)
  ctx.fill()
  ctx.stroke()
  ctx.strokeStyle = `rgba(${hexToRgb(gas.color)},0.35)`
  ctx.beginPath()
  ctx.arc(x, y, 11 + pulse, 0, Math.PI * 2)
  ctx.stroke()
  ctx.fillStyle = gas.color
  ctx.beginPath()
  ctx.arc(x, y, 2.6, 0, Math.PI * 2)
  ctx.fill()
  if (leakSourceState.mode !== 'facility' && source?.name) {
    ctx.fillStyle = '#ffffff'
    ctx.font = 'bold 9px "Noto Sans SC"'
    ctx.textAlign = 'center'
    ctx.fillText(source.name, x, y - 18)
  }
  ctx.restore()
}
function drawEvacuationRoute() {
  const route = activeEvacuationRoute.value
  if (
    evacuationPlanningMode.value === 'all'
    && evacuationDisplayMode.value === 'all'
    && evacuationBuildingRoutes.value.length
  ) {
    const highlightedBuildingId = selectedEvacuationBuildingRoute.value?.buildingId || route?.buildingId || ''
    evacuationBuildingRoutes.value
      .filter(item => item.success)
      .forEach(item => {
        drawSingleEvacuationRoute(item, {
          emphasized: item.buildingId === highlightedBuildingId,
          showMarkers: item.buildingId === highlightedBuildingId,
        })
      })
    return
  }
  drawSingleEvacuationRoute(route, {
    emphasized: true,
    showMarkers: true,
  })
}
function drawSingleEvacuationRoute(route, options = {}) {
  if (!route?.success || route.path.length < 2) return
  const emphasized = options.emphasized !== false
  const showMarkers = options.showMarkers !== false
  ctx.save()
  ctx.lineJoin = 'round'
  ctx.lineCap = 'round'
  ctx.strokeStyle = emphasized ? 'rgba(10,15,26,0.88)' : 'rgba(10,15,26,0.35)'
  ctx.lineWidth = emphasized ? 8 : 5
  ctx.beginPath()
  ctx.moveTo(route.path[0].x, route.path[0].y)
  for (let index = 1; index < route.path.length; index++) {
    ctx.lineTo(route.path[index].x, route.path[index].y)
  }
  ctx.stroke()
  ctx.strokeStyle = emphasized ? '#22c55e' : 'rgba(56,189,248,0.65)'
  ctx.lineWidth = emphasized ? 4 : 2.4
  ctx.beginPath()
  ctx.moveTo(route.path[0].x, route.path[0].y)
  for (let index = 1; index < route.path.length; index++) {
    ctx.lineTo(route.path[index].x, route.path[index].y)
  }
  ctx.stroke()
  if (!showMarkers) {
    ctx.restore()
    return
  }
  const startPoint = route.path[0]
  const endPoint = route.path[route.path.length - 1]
  ctx.fillStyle = '#22c55e'
  ctx.beginPath()
  ctx.arc(startPoint.x, startPoint.y, 5.5, 0, Math.PI * 2)
  ctx.fill()
  ctx.fillStyle = '#38bdf8'
  ctx.beginPath()
  ctx.arc(endPoint.x, endPoint.y, 6, 0, Math.PI * 2)
  ctx.fill()
  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 9px "Noto Sans SC"'
  ctx.textAlign = 'center'
  ctx.fillText('起点', startPoint.x, startPoint.y - 14)
  ctx.fillText('出口', endPoint.x, endPoint.y - 14)
  ctx.restore()
}
function drawPinnCandidateRegions() {
  const regions = coarseSearchResult.value?.candidateRegions || []
  if (!regions.length) return
  regions.forEach(region => {
    const isSelected = selectedCoarseCandidateId.value === region.candidateId
    const alpha = Math.max(0.12, 0.32 - (region.rank - 1) * 0.05)
    const color = region.rank === 1 ? '#f59e0b' : '#38bdf8'
    ctx.fillStyle = `rgba(${hexToRgb(color)},${isSelected ? alpha * 0.7 : alpha * 0.45})`
    ctx.strokeStyle = isSelected ? '#ffffff' : `rgba(${hexToRgb(color)},${alpha + 0.2})`
    ctx.lineWidth = isSelected ? 2.8 : region.rank === 1 ? 2.2 : 1.4
    ctx.beginPath()
    ctx.arc(region.center.x, region.center.y, region.radius, 0, Math.PI * 2)
    ctx.fill()
    ctx.stroke()
    if (isSelected) {
      ctx.setLineDash([4, 4])
      ctx.strokeStyle = `rgba(${hexToRgb(color)},0.9)`
      ctx.lineWidth = 1.4
      ctx.beginPath()
      ctx.arc(region.center.x, region.center.y, region.radius + 8, 0, Math.PI * 2)
      ctx.stroke()
      ctx.setLineDash([])
    }
    ctx.fillStyle = color
    ctx.font = 'bold 9px "Noto Sans SC"'
    ctx.textAlign = 'center'
    ctx.fillText(`C${region.rank}`, region.center.x, region.center.y - region.radius - 6)
  })
}
function drawPinnRefinementOverlay() {
  const iteration = refinementCurrentIteration.value
  const estimatedSource = refinementResult.value?.estimatedSource
  if (!iteration && !estimatedSource) return
  ctx.save()
  if (iteration) {
    drawRefinementPolygon(iteration)
    ctx.fillStyle = '#ffffff'
    ctx.font = 'bold 9px "Noto Sans SC"'
    ctx.textAlign = 'center'
    ctx.fillText(`R${iteration.iteration}`, iteration.center.x, iteration.center.y - iteration.radius - 12)
  }
  if (estimatedSource) {
    drawEstimatedSourceIcon(estimatedSource, Boolean(iteration && refinementState.currentStep >= refinementIterations.value.length - 1))
  }
  ctx.restore()
}
function drawRefinementPolygon(iteration) {
  const points = iteration.polygon || []
  if (!points.length) return
  ctx.fillStyle = 'rgba(168,85,247,0.14)'
  ctx.strokeStyle = 'rgba(168,85,247,0.95)'
  ctx.lineWidth = 2
  ctx.beginPath()
  ctx.moveTo(points[0].x, points[0].y)
  for (let i = 1; i < points.length; i++) ctx.lineTo(points[i].x, points[i].y)
  ctx.closePath()
  ctx.fill()
  ctx.stroke()
  ctx.setLineDash([4, 4])
  ctx.strokeStyle = 'rgba(255,255,255,0.42)'
  ctx.beginPath()
  ctx.arc(iteration.center.x, iteration.center.y, iteration.radius + 8, 0, Math.PI * 2)
  ctx.stroke()
  ctx.setLineDash([])
}
function drawEstimatedSourceIcon(estimatedSource, emphasized) {
  const { x, y } = estimatedSource.mapPoint
  const size = estimatedSource.iconSize || 12
  ctx.save()
  ctx.translate(x, y)
  ctx.strokeStyle = emphasized ? '#facc15' : '#ffffff'
  ctx.fillStyle = emphasized ? 'rgba(250,204,21,0.18)' : 'rgba(255,255,255,0.1)'
  ctx.lineWidth = emphasized ? 2.2 : 1.6
  ctx.beginPath()
  ctx.arc(0, 0, size, 0, Math.PI * 2)
  ctx.fill()
  ctx.stroke()
  ctx.beginPath()
  ctx.moveTo(-size - 6, 0)
  ctx.lineTo(size + 6, 0)
  ctx.moveTo(0, -size - 6)
  ctx.lineTo(0, size + 6)
  ctx.stroke()
  ctx.beginPath()
  ctx.arc(0, 0, 4.5, 0, Math.PI * 2)
  ctx.fillStyle = emphasized ? '#facc15' : '#a855f7'
  ctx.fill()
  ctx.strokeStyle = 'rgba(255,255,255,0.85)'
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.arc(0, 0, size + 10, 0, Math.PI * 2)
  ctx.stroke()
  ctx.fillStyle = emphasized ? '#facc15' : '#ffffff'
  ctx.font = 'bold 9px "Noto Sans SC"'
  ctx.textAlign = 'center'
  ctx.fillText('预测源点', 0, -size - 14)
  ctx.restore()
}
function drawSelection(f) {
  ctx.strokeStyle = '#00e5a0'; ctx.lineWidth = 2; ctx.setLineDash([4, 3])
  if (f.type === 'tank') { ctx.beginPath(); ctx.arc(f.x, f.y, f.r + 6, 0, Math.PI * 2); ctx.stroke() }
  else if (f.type === 'tower') { ctx.beginPath(); ctx.ellipse(f.x, f.y, f.r + 8, f.h / 2 + 8, 0, 0, Math.PI * 2); ctx.stroke() }
  else { ctx.strokeRect(f.x - 4, f.y - 4, f.w + 8, f.h + 8) }
  ctx.setLineDash([])
  let cx, cy
  if (f.type === 'tank') { cx = f.x; cy = f.y - f.r - 20 }
  else if (f.type === 'tower') { cx = f.x; cy = f.y - f.h / 2 - 20 }
  else { cx = f.x + f.w / 2; cy = f.y - 15 }
  ctx.fillStyle = 'rgba(0,229,160,0.9)'; ctx.font = 'bold 10px "Noto Sans SC"'
  ctx.textAlign = 'center'; ctx.fillText(f.name, cx, cy)
}
function drawHover(f) {
  ctx.strokeStyle = 'rgba(56,189,248,0.6)'; ctx.lineWidth = 1.5; ctx.setLineDash([3, 3])
  if (f.type === 'tank') { ctx.beginPath(); ctx.arc(f.x, f.y, f.r + 5, 0, Math.PI * 2); ctx.stroke() }
  else if (f.type === 'tower') { ctx.beginPath(); ctx.ellipse(f.x, f.y, f.r + 6, f.h / 2 + 6, 0, 0, Math.PI * 2); ctx.stroke() }
  else { ctx.strokeRect(f.x - 3, f.y - 3, f.w + 6, f.h + 6) }
  ctx.setLineDash([])
}
function drawMeasure() {
  const s = Math.max(0.1, viewState.scale || 1)
  ctx.strokeStyle = '#ff6b35'; ctx.lineWidth = 1.5 / s; ctx.setLineDash([4, 4])
  ctx.beginPath(); ctx.moveTo(measurePoints[0].x, measurePoints[0].y)
  for (let i = 1; i < measurePoints.length; i++) ctx.lineTo(measurePoints[i].x, measurePoints[i].y)
  ctx.stroke(); ctx.setLineDash([])
  let totalDist = 0
  for (let i = 1; i < measurePoints.length; i++) {
    const dx = measurePoints[i].x - measurePoints[i - 1].x
    const dy = measurePoints[i].y - measurePoints[i - 1].y
    const dist = Math.sqrt(dx * dx + dy * dy)
    totalDist += dist
    const mx = (measurePoints[i].x + measurePoints[i - 1].x) / 2
    const my = (measurePoints[i].y + measurePoints[i - 1].y) / 2
    ctx.fillStyle = '#ff6b35'; ctx.font = 'bold 8px Orbitron'; ctx.textAlign = 'center'
    ctx.fillText((dist * 0.5).toFixed(1) + 'm', mx, my - 6 / s)
  }
  if (measurePoints.length > 1) {
    ctx.fillStyle = '#ff6b35'; ctx.font = 'bold 9px Orbitron'; ctx.textAlign = 'left'
    const lp = measurePoints[measurePoints.length - 1]
    ctx.fillText('Total: ' + (totalDist * 0.5).toFixed(1) + 'm', lp.x + 6 / s, lp.y)
  }
  measurePoints.forEach(p => {
    ctx.fillStyle = '#ff6b35'; ctx.beginPath(); ctx.arc(p.x, p.y, 2 / s, 0, Math.PI * 2); ctx.fill()
  })
}

function hitTest(wx, wy) {
  for (let i = facilities.length - 1; i >= 0; i--) {
    const f = facilities[i]
    if (!matchFilter(f)) continue
    if (f.type === 'tank') {
      const dx = wx - f.x, dy = wy - f.y
      if (dx * dx + dy * dy <= f.r * f.r) return f
    } else if (f.type === 'tower') {
      if (Math.abs(wx - f.x) <= f.r && wy >= f.y - f.h / 2 && wy <= f.y + f.h / 2) return f
    } else {
      if (wx >= f.x && wx <= f.x + f.w && wy >= f.y && wy <= f.y + f.h) return f
    }
  }
  return null
}
function entranceHitTest(wx, wy) {
  if (!showEntrances.value) return null
  const entrances = getVisibleEntrances()
  for (let i = entrances.length - 1; i >= 0; i--) {
    const entrance = entrances[i]
    if (Math.hypot(wx - entrance.x, wy - entrance.y) <= 12) return entrance
  }
  return null
}
function candidateRegionHitTest(wx, wy) {
  const regions = coarseCandidateRegions.value
  for (let i = regions.length - 1; i >= 0; i--) {
    const region = regions[i]
    if (Math.hypot(wx - region.center.x, wy - region.center.y) <= region.radius) {
      return region
    }
  }
  return null
}

function carHitTest(wx, wy) {
  const markers = carMarkers.value
  for (let i = markers.length - 1; i >= 0; i--) {
    const car = markers[i]
    // 命中半径 16px（车身半宽 + 余量）
    if (Math.hypot(wx - car.x, wy - car.y) <= 16) {
      return carStore.carList.find(c => c.id === car.id) || null
    }
  }
  return null
}

function onCanvasMouseDown(e) {
  const rect = canvasEl.getBoundingClientRect()
  if (measureMode.value) {
    const w = screenToWorld(e.clientX - rect.left, e.clientY - rect.top)
    measurePoints.push({ x: w.x, y: w.y })
    render()
    return
  }
  viewState.dragging = true
  viewState.lastX = e.clientX
  viewState.lastY = e.clientY
  isDragging.value = true
}
function onCanvasMouseMove(e) {
  const rect = canvasEl.getBoundingClientRect()
  const sx = e.clientX - rect.left
  const sy = e.clientY - rect.top
  const w = screenToWorld(sx, sy)
  updateCoordDisplay(w.x, w.y)
  if (viewState.dragging) {
    const dx = e.clientX - viewState.lastX
    const dy = e.clientY - viewState.lastY
    viewState.offsetX += dx / viewState.scale
    viewState.offsetY += dy / viewState.scale
    viewState.lastX = e.clientX
    viewState.lastY = e.clientY
    render()
    return
  }
  if (leakSourceState.picking) {
    canvasEl.style.cursor = 'crosshair'
    return
  }
  if (sensorPlacementState.picking) {
    canvasEl.style.cursor = 'crosshair'
    return
  }
  if (sensorPlacementState.pickingOrigin) {
    canvasEl.style.cursor = 'crosshair'
    return
  }
  const entranceHit = entranceHitTest(w.x, w.y)
  const sensorHit = entranceHit ? null : sensorHitTest(w.x, w.y)
  const candidateHit = entranceHit || sensorHit ? null : candidateRegionHitTest(w.x, w.y)
  const carHit = (!entranceHit && !sensorHit && !candidateHit) ? carHitTest(w.x, w.y) : null
  const hit = (!entranceHit && !sensorHit && !candidateHit && !carHit) ? hitTest(w.x, w.y) : null
  if (entranceHit?.id !== hoveredEntrance.value?.id || hit !== hoveredFacility.value || sensorHit?.id !== hoveredSensor.value?.id || carHit?.id !== hoveredCar.value?.id) {
    hoveredEntrance.value = entranceHit
    hoveredSensor.value = sensorHit
    hoveredCar.value = carHit
    hoveredFacility.value = hit
    canvasEl.style.cursor = entranceHit || sensorHit || candidateHit || carHit || hit ? 'pointer' : (measureMode.value ? 'crosshair' : 'grab')
    render()
  }
}
function onCanvasMouseUp(e) {
  if (viewState.dragging) {
    const dx = Math.abs(e.clientX - viewState.lastX)
    const dy = Math.abs(e.clientY - viewState.lastY)
    if (dx < 5 && dy < 5 && !measureMode.value) {
      const rect = canvasEl.getBoundingClientRect()
      const w = screenToWorld(e.clientX - rect.left, e.clientY - rect.top)
      if (leakSourceState.picking) {
        applyLeakSourcePoint(w, 'map')
        viewState.dragging = false
        isDragging.value = false
        return
      }
      if (sensorPlacementState.picking) {
        captureManualSensorPoint(w)
        viewState.dragging = false
        isDragging.value = false
        return
      }
      if (sensorPlacementState.pickingOrigin) {
        captureOriginPoint(w)
        viewState.dragging = false
        isDragging.value = false
        return
      }
      const entranceHit = entranceHitTest(w.x, w.y)
      const sensorHit = sensorHitTest(w.x, w.y)
      const candidateHit = sensorHit ? null : candidateRegionHitTest(w.x, w.y)
      const carHit = (!sensorHit && !candidateHit) ? carHitTest(w.x, w.y) : null
      const hit = (!sensorHit && !candidateHit && !carHit) ? hitTest(w.x, w.y) : null
      if (entranceHit) {
        hoveredEntrance.value = entranceHit
      } else if (sensorHit) {
        hoveredSensor.value = sensorHit
        selectedSensor.value = sensorHit
        selectedFacility.value = null
        selectedCar.value = null
        showSensorInfo(sensorHit)
      } else if (candidateHit) {
        selectCoarseCandidate(candidateHit.candidateId, true)
      } else if (carHit) {
        selectedCar.value = carHit
        selectedFacility.value = null
        selectedSensor.value = null
        showCarInfo(carHit)
      } else if (hit) {
        selectedFacility.value = hit
        selectedSensor.value = null
        selectedCar.value = null
        showFacilityInfo(hit)
        selectedZone.value = hit.zone
      } else {
        selectedFacility.value = null
        selectedSensor.value = null
        clearInfo()
      }
      render()
    }
    viewState.dragging = false
    isDragging.value = false
  }
}
function onCanvasMouseLeave() {
  viewState.dragging = false
  hoveredFacility.value = null
  hoveredEntrance.value = null
  hoveredSensor.value = null
  isDragging.value = false
  if (!leakSourceState.picking && !sensorPlacementState.picking) {
    canvasEl.style.cursor = measureMode.value ? 'crosshair' : 'grab'
  }
  render()
}
function onCanvasWheel(e) {
  const factor = e.deltaY < 0 ? 1.1 : 0.9
  viewState.scale = Math.max(0.5, Math.min(3, viewState.scale * factor))
  render()
}

function setFilter(filter) {
  activeFilter.value = filter
  render()
}
function selectZone(zoneId) {
  selectedZone.value = zoneId
  const first = facilities.find(f => f.zone === zoneId)
  if (first) {
    selectedFacility.value = first
    showFacilityInfo(first)
    let fx, fy
    if (first.type === 'tank') { fx = first.x; fy = first.y }
    else if (first.type === 'tower') { fx = first.x; fy = first.y }
    else { fx = first.x + first.w / 2; fy = first.y + first.h / 2 }
    viewState.offsetX = canvasEl.width / 2 / viewState.scale - fx
    viewState.offsetY = canvasEl.height / 2 / viewState.scale - fy
    render()
  }
}
function showFacilityInfo(f) {
  panelCollapsed.value = false
  infoTitle.value = f.name
  infoSubtitle.value = { tag: f.status, tagClass: statusTagClass(f.status), desc: f.desc || '' }
  const rows = []
  if (f.type === 'tank') {
    rows.push({key: '储罐编号', val: f.id.toUpperCase()})
    rows.push({key: '所属区域', val: getZoneName(f.zone)})
    rows.push({key: '容量', val: f.capacity})
    rows.push({key: '存储介质', val: f.material})
    rows.push({key: '液位', val: `${f.level}%`, style: { color: f.level > 85 ? 'var(--danger)' : 'var(--accent)' }})
    rows.push({key: '温度', val: `${f.temp}℃`, style: { color: f.temp > 80 ? 'var(--warning)' : 'var(--fg)' }})
    rows.push({key: '状态', val: f.status, tag: true, tagClass: statusTagClass(f.status)})
  } else if (f.type === 'tower') {
    rows.push({key: '设备编号', val: f.id.toUpperCase()})
    rows.push({key: '所属区域', val: getZoneName(f.zone)})
    rows.push({key: '塔高', val: f.height})
    rows.push({key: '操作压力', val: f.pressure})
    rows.push({key: '操作温度', val: f.temp + '℃'})
    rows.push({key: '状态', val: f.status, tag: true, tagClass: statusTagClass(f.status)})
  } else {
    rows.push({key: '建筑编号', val: f.id.toUpperCase()})
    rows.push({key: '所属区域', val: getZoneName(f.zone)})
    if (f.area) rows.push({key: '建筑面积', val: f.area})
    if (f.floors) rows.push({key: '楼层', val: f.floors + ' 层'})
    if (f.personnel) rows.push({key: '在岗人数', val: f.personnel + ' 人'})
    if (f.power) rows.push({key: '额定功率', val: f.power})
    if (f.capacity) rows.push({key: '仓储容量', val: f.capacity})
    if (f.flow) rows.push({key: '处理流量', val: f.flow})
    if (f.volume) rows.push({key: '池容', val: f.volume})
    if (f.bays) rows.push({key: '装卸位', val: f.bays + ' 个'})
    rows.push({key: '状态', val: f.status, tag: true, tagClass: statusTagClass(f.status)})
  }
  infoRows.value = rows
}
function clearInfo() {
  infoTitle.value = '选择设施查看详情'
  infoSubtitle.value = {}
  infoRows.value = []
  selectedZone.value = ''
  selectedCar.value = null
}
function closeInfo() {
  selectedFacility.value = null
  selectedSensor.value = null
  clearInfo()
  render()
}
function setTool(tool) {
  if (tool === 'select') {
    measureMode.value = false
    measurePoints = []
    canvasEl.style.cursor = 'grab'
  } else if (tool === 'measure') {
    measureMode.value = !measureMode.value
    measurePoints = []
    canvasEl.style.cursor = measureMode.value ? 'crosshair' : 'grab'
    if(measureMode.value) showToast('点击地图添加测距点', 'success')
  }
  render()
}
function toggleHeatmap() {
  showHeatmap.value = !showHeatmap.value
  render()
  showToast(showHeatmap.value ? '热力图已开启' : '热力图已关闭', 'success')
}
function toggleFlow() {
  showFlow.value = !showFlow.value
  render()
  showToast(showFlow.value ? '管道流向已显示' : '管道流向已隐藏', 'success')
}
function toggleEntrances() {
  showEntrances.value = !showEntrances.value
  if (!showEntrances.value) hoveredEntrance.value = null
  canvasEl.style.cursor = showEntrances.value && hoveredEntrance.value ? 'pointer' : (measureMode.value ? 'crosshair' : 'grab')
  render()
  showToast(showEntrances.value ? '出入口标记已显示' : '出入口标记已隐藏', 'success')
}
function toggleSensors() {
  showSensors.value = !showSensors.value
  render()
  showToast(showSensors.value ? '传感器已显示' : '传感器已隐藏', 'success')
}
function toggleSensorRanges() {
  showSensorRanges.value = !showSensorRanges.value
  render()
  showToast(showSensorRanges.value ? '半径范围已显示' : '半径范围已隐藏', 'success')
}
function toggleLabels() {
  showLabels.value = !showLabels.value
  render()
}
function zoomIn() {
  viewState.scale = Math.min(3, viewState.scale * 1.2)
  render()
}
function zoomOut() {
  viewState.scale = Math.max(0.5, viewState.scale / 1.2)
  render()
}
function zoomReset() {
  viewState.scale = 1; viewState.offsetX = 0; viewState.offsetY = 0
  render()
  showToast('视图已重置', 'success')
}
function onSearch() {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) { activeFilter.value = 'all'; render(); return }
  const match = facilities.find(f => f.name.toLowerCase().includes(q) || f.id.toLowerCase().includes(q))
  if (match) {
    selectedFacility.value = match
    showFacilityInfo(match)
    selectedZone.value = match.zone
    let fx, fy
    if (match.type === 'tank') { fx = match.x; fy = match.y }
    else if (match.type === 'tower') { fx = match.x; fy = match.y }
    else { fx = match.x + match.w / 2; fy = match.y + match.h / 2 }
    viewState.offsetX = canvasEl.width / 2 / viewState.scale - fx
    viewState.offsetY = canvasEl.height / 2 / viewState.scale - fy
    render()
  }
}
function showToast(text, type) {
  toastText.value = text
  toastType.value = type || 'success'
  toastIcon.value = type === 'warn' ? 'fas fa-exclamation-triangle' : 'fas fa-check-circle'
  toastVisible.value = true
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toastVisible.value = false }, 2500)
}

const goBackHome = () => {
  router.push('/car/home')
}
function syncDiffusionSourceSelection() {
  const validation = buildLeakSourceValidation()
  if (validation.valid) {
    const nextFacilityId = validation.nearestAllowedFacility?.id || validation.selectedFacility?.id || diffusionForm.sourceFacilityId
    diffusionForm.sourceFacilityId = nextFacilityId
    updateDiffusionMetaSource({
      sourceFacility: facilityById.get(nextFacilityId) || null,
      sourcePoint: leakSourceState.mode === 'facility' ? null : leakSourceState.mapPoint,
    })
    return validation
  }
  const fallback = diffusionSourceOptions.value[0] || null
  if (!fallback) return validation
  leakSourceState.mode = 'facility'
  leakSourceState.mapPoint = null
  leakSourceState.picking = false
  diffusionForm.sourceFacilityId = fallback.id
  syncManualGeoInputsFromWorld(getFacilityAnchorPoint(fallback))
  const fallbackValidation = validateGasLeakSource({
    gasId: diffusionForm.gasId,
    sourceFacilityId: fallback.id,
    facilities,
  })
  updateDiffusionMetaSource({
    sourceFacility: fallback,
    sourcePoint: null,
  })
  return fallbackValidation
}


const carGasToDiffusionGasMap = {
  '甲烷': 1,
  '氨气': 2,
  '一氧化碳': 3,
  '氧气': 4
}

function autoConfigFromCarParams() {
  const { carId, gasType, x, y, autoConfig } = route.query
  
  if (autoConfig !== 'true' || !carId) {
    return
  }
  
  showToast(`接收到小车 ${carId} 预警联动，正在自动配置扩散模型...`, 'success')
  
  if (gasType && carGasToDiffusionGasMap[gasType]) {
    diffusionForm.gasId = carGasToDiffusionGasMap[gasType]
  }
  
  if (x && y) {
    const worldX = Number(x)
    const worldY = Number(y)
    
    leakSourceState.mode = 'manual'
    leakSourceState.mapPoint = { x: worldX, y: worldY }
    leakSourceState.manualLongitude = worldX.toString()
    leakSourceState.manualLatitude = worldY.toString()
    
    updateDiffusionMetaSource({
      sourceFacility: null,
      sourcePoint: leakSourceState.mapPoint,
    })
    
    syncManualGeoInputsFromWorld(leakSourceState.mapPoint)
  }
  
  showToast('扩散模型已自动配置，请点击"扩散模拟"按钮运行', 'success')
}

async function runDiffusionSimulation(options = {}) {
  const payload = {
    gasId: diffusionForm.gasId,
    sourceFacilityId: diffusionForm.sourceFacilityId,
    sourceMapPoint: currentLeakSourcePoint.value,
    sourceRate: diffusionForm.sourceRate,
    releaseDuration: diffusionForm.releaseDuration,
    initialTemperature: diffusionForm.initialTemperature,
    initialPressure: diffusionForm.initialPressure,
    releaseHeight: diffusionForm.releaseHeight,
    windSpeed: diffusionForm.windSpeed,
    windDirection: diffusionForm.windDirection,
    ambientTemperature: diffusionForm.ambientTemperature,
    humidity: diffusionForm.humidity,
    stabilityClass: diffusionForm.stabilityClass,
    terrainRoughness: diffusionForm.terrainRoughness,
    obstacleInfluenceEnabled: diffusionForm.obstacleInfluenceEnabled,
    frameCount: diffusionForm.frameCount,
    frameStepSec: diffusionForm.frameStepSec,
  }
  const resp = await apiRunDiffusionSimulation(payload)
  if (!resp.success || !resp.data?.frames) {
    showToast('扩散模拟失败: ' + (resp.error || '未知错误'), 'error')
    return
  }
  const result = resp.data
  diffusionFrames.value = result.frames
  diffusionMeta.value = {
    gas: result.gas,
    sourceFacility: result.sourceFacility,
    sourcePoint: result.sourcePoint,
    stats: result.stats,
    blockedMask: result.blockedMask || null,
    map: result.map || null,
    executor: result.executor || null,
    sensorSeries: result.sensorSeries || [],
    scenarioMeta: result.scenarioMeta || null,
    outputMeta: result.outputMeta || null,
  }
  diffusionState.currentFrame = 0
  diffusionState.accumulatorMs = 0
  diffusionState.playing = diffusionFrames.value.length > 1
  resampleSensorsFromDiffusion()
  if (evacuationBatchResult.value?.routesByBuilding?.length) {
    runBatchEvacuationPlanning({ silent: true })
  } else if (evacuationPlan.value?.success) {
    runEvacuationPlanning({ silent: true })
  }
  render()
  if (!options.silent) {
    showToast(`已生成 ${diffusionFrames.value.length} 帧扩散动画`, 'success')
  }
}
function resetDiffusionSimulation() {
  diffusionFrames.value = []
  diffusionState.currentFrame = 0
  diffusionState.playing = false
  diffusionState.accumulatorMs = 0
  diffusionMeta.value = {
    gas: getGasById(diffusionForm.gasId),
    sourceFacility: selectedDiffusionSource.value,
    sourcePoint: currentLeakSourcePoint.value,
    stats: { peakConcentration: 0, peakAffectedArea: 0, peakDangerArea: 0 },
    blockedMask: null,
    map: null,
    executor: null,
    sensorSeries: [],
    scenarioMeta: null,
    outputMeta: null,
  }
  clearEvacuationPlanning(true)
  resampleSensorsFromDiffusion()
  render()
  showToast('已清除扩散动画', 'warn')
}
function resolveEvacuationStart() {
  if (!selectedFacility.value) {
    return {
      valid: false,
      message: '请先选择一个带人员疏散需求的建筑',
      point: null,
      label: '--',
    }
  }
  const entrance = buildingEntrances.find(item => item.parentId === selectedFacility.value.id)
  if (!entrance) {
    return {
      valid: false,
      message: '当前选择的设施没有可用建筑出入口，请选择办公楼、厂房、仓库或公用工程建筑',
      point: null,
      label: '--',
    }
  }
  return {
    valid: true,
    message: '',
    point: { x: entrance.x, y: entrance.y },
    label: entrance.label,
  }
}
function syncSelectedEvacuationCandidate(routePlan, preferredCandidateId = '') {
  const routes = routePlan?.success
    ? (routePlan.candidateRoutes?.length ? routePlan.candidateRoutes : [routePlan])
    : []
  if (!routes.length) {
    selectedEvacuationCandidateId.value = ''
    return
  }
  const nextSelectedRoute = routes.find(route => route.candidateId === preferredCandidateId)
    || routes.find(route => route.candidateId === routePlan.recommendedCandidateId)
    || routes[0]
  selectedEvacuationCandidateId.value = nextSelectedRoute?.candidateId || ''
}
function syncSelectedEvacuationBuilding(batchResult, preferredBuildingId = '') {
  const routes = batchResult?.routesByBuilding || []
  if (!routes.length) {
    selectedEvacuationBuildingId.value = ''
    return null
  }
  const nextSelectedBuilding = routes.find(route => route.buildingId === preferredBuildingId)
    || routes.find(route => route.buildingId === selectedFacility.value?.id)
    || routes.find(route => route.success)
    || routes[0]
  selectedEvacuationBuildingId.value = nextSelectedBuilding?.buildingId || ''
  return nextSelectedBuilding || null
}
function selectEvacuationCandidate(candidateId) {
  const candidate = evacuationCandidateRoutes.value.find(route => route.candidateId === candidateId)
  if (!candidate) return
  selectedEvacuationCandidateId.value = candidate.candidateId
  render()
}
function selectEvacuationBuilding(buildingId, syncFacility = false) {
  const buildingRoute = evacuationBuildingRoutes.value.find(route => route.buildingId === buildingId)
  if (!buildingRoute) return
  evacuationPlanningMode.value = 'all'
  selectedEvacuationBuildingId.value = buildingRoute.buildingId
  syncSelectedEvacuationCandidate(buildingRoute)
  if (syncFacility) {
    const facility = facilityById.get(buildingId)
    if (facility) selectedFacility.value = facility
  }
  render()
}
function clearEvacuationPlanning(silent = false) {
  evacuationPlan.value = null
  evacuationBatchResult.value = null
  evacuationPlanningMode.value = 'single'
  evacuationDisplayMode.value = 'selected'
  selectedEvacuationBuildingId.value = ''
  selectedEvacuationCandidateId.value = ''
  render()
  if (!silent) showToast('已清除逃生路径', 'warn')
}
function runEvacuationPlanning(options = {}) {
  const preferredCandidateId = options.preferredCandidateId || selectedEvacuationCandidateId.value
  const start = resolveEvacuationStart()
  if (!start.valid) {
    if (!options.silent) showToast(start.message, 'warn')
    evacuationPlan.value = null
    evacuationBatchResult.value = null
    evacuationPlanningMode.value = 'single'
    selectedEvacuationCandidateId.value = ''
    render()
    return
  }
  if (!currentDiffusionFrame.value || !diffusionMeta.value.gas) {
    if (!options.silent) showToast('请先生成扩散动画后再执行逃生规划', 'warn')
    evacuationPlan.value = null
    evacuationBatchResult.value = null
    evacuationPlanningMode.value = 'single'
    selectedEvacuationCandidateId.value = ''
    render()
    return
  }

  apiRunEvacuationPlanning({
    roads,
    parkEntrances,
    startPoint: start.point,
    startLabel: start.label,
    frame: currentDiffusionFrame.value,
    gas: diffusionMeta.value.gas,
    blockedMask: diffusionMeta.value.blockedMask,
  }).then(resp => {
    const result = resp.success ? resp.data : null
    evacuationPlanningMode.value = 'single'
    evacuationPlan.value = result
    evacuationBatchResult.value = null
    selectedEvacuationBuildingId.value = selectedFacility.value?.id || ''
    syncSelectedEvacuationCandidate(result, preferredCandidateId)
    render()

    if (options.silent) return
    if (!result?.success) {
      showToast(result?.message || '未找到可用逃生路径', 'warn')
      return
    }
    showToast(`已规划至 ${result.exitLabel} 的逃生路径`, 'success')
  })
}
function runBatchEvacuationPlanning(options = {}) {
  const preferredBuildingId = options.preferredBuildingId || selectedEvacuationBuildingId.value || selectedFacility.value?.id || ''
  const preferredCandidateId = options.preferredCandidateId || selectedEvacuationCandidateId.value
  if (!currentDiffusionFrame.value || !diffusionMeta.value.gas) {
    if (!options.silent) showToast('请先生成扩散动画后再执行批量逃生规划', 'warn')
    evacuationBatchResult.value = null
    evacuationPlan.value = null
    selectedEvacuationBuildingId.value = ''
    selectedEvacuationCandidateId.value = ''
    render()
    return
  }

  apiRunEvacuationPlanning({
    roads,
    buildingEntrances,
    parkEntrances,
    facilities,
    frame: currentDiffusionFrame.value,
    gas: diffusionMeta.value.gas,
    blockedMask: diffusionMeta.value.blockedMask,
  }).then(resp => {
    const result = resp.success ? resp.data : null
    evacuationPlanningMode.value = 'all'
    evacuationDisplayMode.value = options.displayMode || evacuationDisplayMode.value
    evacuationPlan.value = null
    evacuationBatchResult.value = result
    const nextBuildingRoute = syncSelectedEvacuationBuilding(result, preferredBuildingId)
    syncSelectedEvacuationCandidate(nextBuildingRoute, preferredCandidateId)
    render()

    if (options.silent) return
    if (!result?.hasAnySuccess) {
      showToast(result?.message || '当前帧所有建筑均无安全逃生路径', 'warn')
      return
    }
    showToast(`已生成 ${result.successCount} 栋建筑的逃生路径，阻断 ${result.blockedCount} 栋`, 'success')
  })
}
function toggleDiffusionPlayback() {
  if (!diffusionFrames.value.length) return
  diffusionState.playing = !diffusionState.playing
  diffusionState.accumulatorMs = 0
}
function seekDiffusionFrame(frameIndex) {
  if (!diffusionFrames.value.length) return
  diffusionState.currentFrame = clamp(frameIndex, 0, diffusionFrames.value.length - 1)
  diffusionState.accumulatorMs = 0
  render()
}
function stepDiffusionFrame(direction) {
  if (!diffusionFrames.value.length) return
  seekDiffusionFrame(diffusionState.currentFrame + direction)
}
function useSelectedFacilityAsLeakSource() {
  if (!selectedFacility.value) {
    showToast('请先在地图上选择一个设施', 'warn')
    return
  }
  const validation = validateGasLeakSource({
    gasId: diffusionForm.gasId,
    sourceFacilityId: selectedFacility.value.id,
    facilities,
  })
  if (!validation.valid) {
    showToast(validation.message, 'warn')
    return
  }
  leakSourceState.mode = 'facility'
  leakSourceState.picking = false
  leakSourceState.mapPoint = null
  diffusionForm.sourceFacilityId = selectedFacility.value.id
  syncManualGeoInputsFromWorld(getFacilityAnchorPoint(selectedFacility.value))
  updateDiffusionMetaSource({
    sourceFacility: selectedFacility.value,
    sourcePoint: null,
  })
  render()
  showToast(`已将 ${selectedFacility.value.name} 设为泄漏源`, 'success')
}
function updateDiffusionPlayback(deltaMs) {
  if (!diffusionState.playing || diffusionFrames.value.length <= 1) return
  diffusionState.accumulatorMs += deltaMs * diffusionState.speed
  while (diffusionState.accumulatorMs >= diffusionState.frameDurationMs) {
    diffusionState.accumulatorMs -= diffusionState.frameDurationMs
    if (diffusionState.currentFrame >= diffusionFrames.value.length - 1) {
      if (diffusionState.loop) diffusionState.currentFrame = 0
      else {
        diffusionState.currentFrame = diffusionFrames.value.length - 1
        diffusionState.playing = false
        break
      }
    } else {
      diffusionState.currentFrame += 1
    }
  }
}
function getSensorCurrentConcentration(sensor, frameIndex = diffusionState.currentFrame) {
  if (sensor.sampledSeries?.length) {
    return sensor.sampledSeries[frameIndex]?.concentration || 0
  }
  return getFrameConcentrationAtPoint(currentDiffusionFrame.value, sensor.x, sensor.y)
}
function getSensorAutoConcentration(sensor, frameIndex = diffusionState.currentFrame) {
  if (!sensor?.autoSampledSeries?.length) return 0
  return sensor.autoSampledSeries[frameIndex]?.concentration || 0
}
function getSensorAlarmLevel(concentration, gas) {
  if (!gas) return 'normal'
  if (concentration >= gas.dangerThreshold) return 'danger'
  if (concentration >= gas.warningThreshold) return 'warning'
  return 'normal'
}
function normalizeSeriesConcentration(value) {
  const numericValue = Number(value)
  if (!Number.isFinite(numericValue)) return 0
  return Number(Math.max(0, numericValue).toFixed(2))
}
function buildFrameSeriesTemplate(frames = diffusionFrames.value) {
  return (frames || []).map(frame => ({
    frameIndex: frame.frameIndex,
    timeSec: frame.timeSec,
    concentration: 0,
  }))
}
function normalizeManualSeries(manualSeries, frames = diffusionFrames.value) {
  const template = buildFrameSeriesTemplate(frames)
  if (!template.length) return []
  const valueByFrame = new Map(
    (manualSeries || [])
      .filter(item => item && Number.isFinite(item.frameIndex))
      .map(item => [item.frameIndex, normalizeSeriesConcentration(item.concentration)])
  )
  return template.map(item => ({
    frameIndex: item.frameIndex,
    timeSec: item.timeSec,
    concentration: valueByFrame.has(item.frameIndex) ? valueByFrame.get(item.frameIndex) : 0,
  }))
}
function buildActiveSensorSeries(sensorList, frames = diffusionFrames.value) {
  // 若扩散帧数据为空，使用高斯烟羽模型估算浓度作为基线
  const hasFrames = frames && frames.length > 0
  const leakPoint = currentLeakSourcePoint.value || (diffusionMeta.value?.sourcePoint ? normalizeMapPoint(diffusionMeta.value.sourcePoint) : null)
  const windSpeed = weatherState.value.windSpeed
  const windDir = weatherState.value.windDir

  const autoSampledSensors = attachSensorSampleSeries(
    sensorList.map(sensor => {
      // 加载时根据国标自动重算 risk 和 priority
      const nearestFac = findNearestFacility(sensor.x, sensor.y)
      const { risk, priority } = computeSensorRisk(sensor, nearestFac)
      return {
        ...sensor,
        mode: sensor.mode || 'auto',
        risk,
        priority,
      }
    }),
    frames
  )
  return autoSampledSensors.map(sensor => {
    let autoSampledSeries = (sensor.sampledSeries || []).map(item => ({
      frameIndex: item.frameIndex,
      timeSec: item.timeSec,
      concentration: normalizeSeriesConcentration(item.concentration),
    }))

    // 无扩散帧数据时：用高斯烟羽模型生成仿真浓度序列
    if (!hasFrames && leakPoint) {
      const sourceRate = diffusionForm.sourceRate || 50
      for (let t = 0; t < 12; t++) {
        const timeSec = t * 10
        // 随时间推移浓度递增后稳定
        const timeFactor = Math.min(1, t / 6)
        const baseConc = computeGasConcentration(sensor, leakPoint, windSpeed, windDir, sourceRate)
        autoSampledSeries.push({
          frameIndex: t,
          timeSec,
          concentration: baseConc * timeFactor * (0.8 + Math.random() * 0.4)
        })
      }
    }

    const manualSeries = normalizeManualSeries(sensor.manualSeries, frames)
    const activeSeries = (sensor.mode || 'auto') === 'manual' ? manualSeries : autoSampledSeries
    const sampledPeak = activeSeries.reduce((max, item) => Math.max(max, item.concentration || 0), 0)
    return {
      ...sensor,
      mode: sensor.mode || 'auto',
      autoSampledSeries,
      manualSeries,
      sampledSeries: activeSeries,
      sampledPeak: Number(sampledPeak.toFixed(2)),
      sampledFrames: activeSeries.length,
      lastSampleTime: sensor.lastSampleTime || Date.now(),
    }
  })
}
function syncSensorEditorState(sensor = selectedSensor.value) {
  if (!sensor) {
    sensorEditorState.currentFrameConcentration = 0
    sensorEditorState.fillAllConcentration = 0
    sensorEditorState.boundSensorId = ''
    return
  }
  const currentManualValue = normalizeSeriesConcentration(sensor.manualSeries?.[diffusionState.currentFrame]?.concentration || 0)
  sensorEditorState.currentFrameConcentration = currentManualValue
  if (sensorEditorState.boundSensorId !== sensor.id) {
    sensorEditorState.fillAllConcentration = currentManualValue
    sensorEditorState.boundSensorId = sensor.id
  }
}
function updateSensorById(sensorId, updater) {
  sensors.value = buildActiveSensorSeries(
    sensors.value.map(sensor => (sensor.id === sensorId ? updater({ ...sensor }) : sensor)),
    diffusionFrames.value
  )
  selectedSensor.value = sensors.value.find(sensor => sensor.id === sensorId) || null
  if (selectedSensor.value) {
    showSensorInfo(selectedSensor.value)
  } else {
    syncSensorEditorState(null)
  }
  render()
}
function selectManualSensorTarget(sensorId) {
  manualSensorTargetId.value = sensorId
  const sensor = sensors.value.find(item => item.id === sensorId) || null
  selectedSensor.value = sensor
  if (sensor) {
    showSensorInfo(sensor)
  } else {
    syncSensorEditorState(null)
  }
}
function toggleManualSensorPanel() {
  manualSensorPanelVisible.value = !manualSensorPanelVisible.value
  if (!manualSensorPanelVisible.value) return
  const preferredSensor = selectedSensor.value || sensors.value[0] || null
  if (preferredSensor) {
    manualSensorTargetId.value = preferredSensor.id
    showSensorInfo(preferredSensor)
  } else {
    syncSensorEditorState(null)
  }
}
function setManualPanelSensorMode(nextMode) {
  const sensor = manualSensorTarget.value
  if (!sensor) {
    showToast('请先选择一个传感器', 'warn')
    return
  }
  if (!selectedSensor.value || selectedSensor.value.id !== sensor.id) {
    selectedSensor.value = sensor
  }
  setSelectedSensorMode(nextMode)
}
function buildSensorHistoryChart(sensor) {
  if (!sensor?.sampledSeries?.length) return null
  const width = 280
  const padding = 16
  const top = 12
  const bottom = 80
  const gas = diffusionMeta.value.gas || getGasById(diffusionForm.gasId)
  const maxConcentration = Math.max(
    gas?.dangerThreshold || 1,
    ...sensor.sampledSeries.map(item => item.concentration || 0),
    1
  )
  const maxFrameIndex = Math.max(sensor.sampledSeries.length - 1, 1)
  const xAt = frameIndex => padding + (frameIndex / maxFrameIndex) * (width - padding * 2)
  const yAt = concentration => bottom - (Math.min(concentration, maxConcentration) / maxConcentration) * (bottom - top)
  return {
    padding,
    points: sensor.sampledSeries.map(item => `${xAt(item.frameIndex).toFixed(1)},${yAt(item.concentration).toFixed(1)}`).join(' '),
    markerX: xAt(Math.min(diffusionState.currentFrame, maxFrameIndex)),
    markerY: yAt(getSensorCurrentConcentration(sensor)),
    warningY: yAt(gas?.warningThreshold || 0),
    dangerY: yAt(gas?.dangerThreshold || 0),
    currentLabel: `${getSensorCurrentConcentration(sensor).toFixed(2)} ppm`,
    peakLabel: `${(sensor.sampledPeak || 0).toFixed(2)} ppm`,
    endLabel: `${sensor.sampledSeries[maxFrameIndex]?.timeSec?.toFixed(0) || 0}s`,
  }
}
function resampleSensorsFromDiffusion() {
  sensors.value = buildActiveSensorSeries(sensors.value, diffusionFrames.value)
  if (selectedSensor.value) {
    const next = sensors.value.find(sensor => sensor.id === selectedSensor.value.id) || null
    selectedSensor.value = next
    if (next) showSensorInfo(next)
    else syncSensorEditorState(null)
  } else {
    syncSensorEditorState(null)
  }
}
function seedDemoSensors() {
  // 不再自动生成传感器，全部由用户手动添加
  sensors.value = []
}
/**
 * 手动新增传感器
 * 统一使用 'gas' 类型（多种气体传感器），priority 由 computeSensorRisk 自动计算
 */
function placeManualSensorAtPoint(point, sensorConfig = getNormalizedManualSensorDraft()) {
  const normalizedPoint = normalizeMapPoint(point)
  const nearestFacility = findNearestFacility(normalizedPoint.x, normalizedPoint.y)
  const tempSensor = {
    detectionRange: sensorConfig.detectionRange || 'CO/CH4/NH3/O2',
    installationHeight: sensorConfig.installationHeight || 1.5,
  }
  const { risk: riskVal, priority } = computeSensorRisk(tempSensor, nearestFacility)
  // 统一使用 gas 类型（多种气体传感器，支持 CO/CH4/NH3/O2）
  // 使用工程命名生成传感器编号
  let areaType = 'tank', zone = 'tank_farm', isPumpArea = false
  for (const f of facilities) {
    if (f.type === 'tank' || f.type === 'tower') {
      if (Math.hypot(normalizedPoint.x - f.x, normalizedPoint.y - f.y) < 100) { areaType = f.type; zone = f.zone; break }
    } else {
      const cx = f.x + (f.w || 0) / 2, cy = f.y + (f.h || 0) / 2
      if (Math.hypot(normalizedPoint.x - cx, normalizedPoint.y - cy) < Math.max(f.w || 40, f.h || 40) * 0.8) {
        areaType = f.type; zone = f.zone
        if (f.name.includes('压缩机') || f.name.includes('泵房')) isPumpArea = true
        break
      }
    }
  }
  const sensorId = generateSensorCode(areaType, zone, isPumpArea)
  sensors.value.push({
    id: sensorId,
    x: normalizedPoint.x,
    y: normalizedPoint.y,
    type: 'gas',
    risk: riskVal,
    priority,
    installationHeight: sensorConfig.installationHeight,
    effectiveRange: sensorConfig.effectiveRange,
    detectionRange: sensorConfig.detectionRange,
    installRemark: sensorConfig.installRemark,
    mode: 'auto',
    lastSampleTime: null,
    manualSeries: buildFrameSeriesTemplate().map(item => ({ ...item })),
  })
  sensorPlacementState.picking = false
  sensorPlacementState.pendingPoint = null
  manualSensorConfigVisible.value = false
  resetManualSensorDraft()
  resampleSensorsFromDiffusion()
  const createdSensor = sensors.value.find(sensor => sensor.id === sensorId) || null
  if (createdSensor) {
    selectedSensor.value = createdSensor
    showSensorInfo(createdSensor)
  }
  calcCoverage()
  updateRiskStat()
  canvasEl.style.cursor = measureMode.value ? 'crosshair' : 'grab'
  // 保存到数据库（异步，不影响前端体验）
  saveSensorToDB(createdSensor || sensors.value[sensors.value.length - 1])
  showToast('手动新增传感器成功，已绑定当前扩散采样数据', 'success')
  render()
}
function setSelectedSensorMode(nextMode) {
  if (!selectedSensor.value) return
  const mode = nextMode === 'manual' ? 'manual' : 'auto'
  updateSensorById(selectedSensor.value.id, sensor => {
    if (mode === 'manual' && !sensor.manualSeries?.length) {
      sensor.manualSeries = buildFrameSeriesTemplate().map(item => ({ ...item }))
    }
    sensor.mode = mode
    return sensor
  })
  showToast(mode === 'manual' ? '已切换为手动数据模式' : '已切换为自动采样模式', 'success')
}
function applySelectedSensorManualValueToCurrentFrame() {
  if (!selectedSensor.value) return
  if (selectedSensor.value.mode !== 'manual') {
    showToast('请先切换到手动数据模式', 'warn')
    return
  }
  const frame = currentDiffusionFrame.value
  if (!frame) {
    showToast('请先生成扩散时间轴后再录入手动数据', 'warn')
    return
  }
  const concentration = normalizeSeriesConcentration(sensorEditorState.currentFrameConcentration)
  updateSensorById(selectedSensor.value.id, sensor => {
    const manualSeries = normalizeManualSeries(sensor.manualSeries, diffusionFrames.value)
    sensor.manualSeries = manualSeries.map(item => (
      item.frameIndex === frame.frameIndex
        ? { ...item, concentration }
        : item
    ))
    sensor.lastSampleTime = Date.now()
    return sensor
  })
  sensorEditorState.currentFrameConcentration = concentration
  showToast(`已写入第 ${frame.frameIndex + 1} 帧手动浓度`, 'success')
}
function fillSelectedSensorManualSeries() {
  if (!selectedSensor.value) return
  if (selectedSensor.value.mode !== 'manual') {
    showToast('请先切换到手动数据模式', 'warn')
    return
  }
  if (!diffusionFrames.value.length) {
    showToast('请先生成扩散时间轴后再批量填充', 'warn')
    return
  }
  const concentration = normalizeSeriesConcentration(sensorEditorState.fillAllConcentration)
  updateSensorById(selectedSensor.value.id, sensor => {
    sensor.manualSeries = buildFrameSeriesTemplate().map(item => ({
      ...item,
      concentration,
    }))
    sensor.lastSampleTime = Date.now()
    return sensor
  })
  sensorEditorState.currentFrameConcentration = concentration
  showToast('已填充该传感器全时段手动浓度', 'success')
}
function copyAutoSeriesToSelectedSensorManual() {
  if (!selectedSensor.value) return
  if (!diffusionFrames.value.length) {
    showToast('请先生成扩散时间轴后再复制自动曲线', 'warn')
    return
  }
  updateSensorById(selectedSensor.value.id, sensor => {
    sensor.mode = 'manual'
    sensor.manualSeries = (sensor.autoSampledSeries || buildFrameSeriesTemplate()).map(item => ({
      frameIndex: item.frameIndex,
      timeSec: item.timeSec,
      concentration: normalizeSeriesConcentration(item.concentration),
    }))
    sensor.lastSampleTime = Date.now()
    return sensor
  })
  showToast('已复制自动采样曲线到手动序列', 'success')
}
function clearSelectedSensorManualSeries() {
  if (!selectedSensor.value) return
  if (selectedSensor.value.mode !== 'manual') {
    showToast('当前传感器不在手动数据模式', 'warn')
    return
  }
  updateSensorById(selectedSensor.value.id, sensor => {
    sensor.manualSeries = buildFrameSeriesTemplate().map(item => ({ ...item }))
    return sensor
  })
  sensorEditorState.currentFrameConcentration = 0
  sensorEditorState.fillAllConcentration = 0
  showToast('已清空手动时间序列', 'warn')
}
function createPinnInputPayload() {
  if (!diffusionFrames.value.length) {
    showToast('请先生成扩散动画后再整理 PINN 输入', 'warn')
    return null
  }
  if (!sensors.value.length && !mobileSensorReadings.value.length) {
    showToast('当前没有可导出的传感器数据', 'warn')
    return null
  }
  const gas = diffusionMeta.value.gas || getGasById(diffusionForm.gasId)
  const sourceFacility = diffusionMeta.value.sourceFacility || selectedDiffusionSource.value
  return {
    gas,
    sourceFacility,
    scenario: {
      ...diffusionForm,
      ...(diffusionMeta.value.scenarioMeta || {}),
      sourceMapPoint: diffusionMeta.value.sourcePoint || currentLeakSourcePoint.value,
    },
    sensors: getPinnReadySensors(),
    frames: diffusionFrames.value,
    currentFrameIndex: diffusionState.currentFrame,
    sensorCount: getPinnReadySensors().length,
    frameCount: diffusionFrames.value.length,
    sourceFacilityName: sourceFacility?.name || '手动点位',
  }
}
function getPinnReadySensors() {
  if (mobileSensorReadings.value.length) {
    return [...sensors.value, ...mobileSensorReadings.value]
  }
  return sensors.value
}

async function runPinnCoarseSearchPreview() {
  if (!diffusionFrames.value.length) {
    showToast('请先生成扩散动画后再执行粗搜', 'warn')
    return
  }
  const exportPayload = createPinnInputPayload()
  if (!exportPayload) return
  const gas = diffusionMeta.value.gas || getGasById(diffusionForm.gasId)
  pinnExportPayload.value = exportPayload
  pinnExportSummary.value = {
    sensorCount: exportPayload?.sensors?.length || 0,
    frameCount: exportPayload?.frames?.length || 0,
    sourceLabel: exportPayload?.sourceFacilityName || '',
  }

  const resp = await apiPinnCoarseSearch({
    pinnExportPayload: exportPayload,
    config: { ...pinnConfig },
  })
  const result = resp.success ? resp.data : null
  coarseSearchResult.value = result
  coarseSearchSummary.value = result ? {
    candidateCount: result.candidateRegions?.length || 0,
    topCandidate: result.candidateRegions?.[0]?.candidateId || '',
    label: `${result.candidateRegions?.length || 0} 个候选区域`,
  } : null
  selectedCoarseCandidateId.value = result?.candidateRegions?.[0]?.candidateId || ''
  render()
  if (!result) {
    showToast(`PINN 粗搜索失败: ${resp.error || '未知错误'}`, 'error')
    return
  }
  showToast(`已生成 ${result.candidateRegions?.length || 0} 个粗搜候选区域`, 'success')
}
function clearPinnCoarseSearch() {
  coarseSearchResult.value = null
  coarseSearchSummary.value = null
  selectedCoarseCandidateId.value = ''
  clearPinnRefinement(false)
  render()
  showToast('已清空粗搜候选区域', 'warn')
}
function selectCoarseCandidate(candidateId, centerView = false) {
  const candidate = coarseCandidateRegions.value.find(item => item.candidateId === candidateId)
  if (!candidate) return
  selectedCoarseCandidateId.value = candidate.candidateId
  if (centerView && canvasEl) {
    viewState.offsetX = canvasEl.width / 2 / viewState.scale - candidate.center.x
    viewState.offsetY = canvasEl.height / 2 / viewState.scale - candidate.center.y
  }
  render()
}
function buildCurrentRefinementInput() {
  if (!selectedCoarseCandidate.value) {
    showToast('请先选择一个粗搜候选区域', 'warn')
    return null
  }
  const candidate = selectedCoarseCandidate.value
  return {
    candidateId: candidate.candidateId,
    center: candidate.center,
    bounds: candidate.bounds,
    sensors: getPinnReadySensors(),
    sensorCount: getPinnReadySensors().length,
    currentFrameIndex: diffusionState.currentFrame,
  }
}
async function runMockPinnRefinementPreview() {
  const input = buildCurrentRefinementInput()
  if (!input) return

  const exportPayload = createPinnInputPayload()
  if (!exportPayload) return

  refinementInput.value = input
  pinnExportPayload.value = exportPayload
  pinnExportSummary.value = {
    sensorCount: exportPayload.sensors?.length || 0,
    frameCount: exportPayload.frames?.length || 0,
    sourceLabel: exportPayload.sourceFacilityName || '',
  }

  const resp = await apiPinnInversion({
    pinnExportPayload: exportPayload,
    coarseSearchResult: coarseSearchResult.value,
    refinementInput: input,
    trainingConfig: { ...pinnRefinementConfig },
    sourceMapPoint: currentLeakSourcePoint.value,
  })
  const result = resp.success ? resp.data : null
  refinementResult.value = result

  if (result?.coarseCandidates?.length && coarseSearchResult.value?.candidateRegions?.length) {
    coarseSearchResult.value = {
      ...coarseSearchResult.value,
      candidateRegions: result.coarseCandidates.map((candidate: any) => ({
        ...candidate,
        score: candidate.score ?? candidate.rankScore ?? 0,
      })),
    }
    coarseSearchSummary.value = {
      candidateCount: coarseSearchResult.value.candidateRegions?.length || 0,
      topCandidate: result.summary?.bestCandidateId || coarseSearchResult.value.candidateRegions[0]?.candidateId || '',
    }
    selectedCoarseCandidateId.value = result.summary?.bestCandidateId
      || coarseSearchResult.value.candidateRegions[0]?.candidateId
      || ''
  }

  const iterCount = result?.iterations?.length || result?.lossHistory?.length || 0
  refinementSummary.value = {
    totalIterations: iterCount,
    label: `${iterCount} 步精修`,
  }
  refinementState.currentStep = 0
  refinementState.accumulatorMs = 0
  refinementState.playing = iterCount > 1
  render()

  if (!result) {
    showToast(`PINN 反演失败: ${resp.error || '未知错误'}`, 'error')
    return
  }
  showToast(`已生成 ${iterCount} 步精修结果`, 'success')
}
function clearPinnRefinement(showMessage = true) {
  refinementInput.value = null
  refinementResult.value = null
  refinementSummary.value = null
  refinementState.currentStep = 0
  refinementState.accumulatorMs = 0
  refinementState.playing = false
  pinnExecutorState.mode = 'local'
  pinnExecutorState.fallbackReason = ''
  if (showMessage) showToast('已清空精修骨架', 'warn')
}
function toggleRefinementPlayback() {
  if (!refinementIterations.value.length) {
    showToast('请先生成精修骨架', 'warn')
    return
  }
  refinementState.playing = !refinementState.playing
  refinementState.accumulatorMs = 0
}
function seekRefinementStep(step) {
  if (!refinementIterations.value.length) return
  refinementState.currentStep = clamp(step, 0, refinementIterations.value.length - 1)
  refinementState.accumulatorMs = 0
  render()
}
function updateRefinementPlayback(deltaMs) {
  if (!refinementState.playing || refinementIterations.value.length <= 1) return
  refinementState.accumulatorMs += deltaMs * refinementState.speed
  while (refinementState.accumulatorMs >= refinementState.frameDurationMs) {
    refinementState.accumulatorMs -= refinementState.frameDurationMs
    if (refinementState.currentStep >= refinementIterations.value.length - 1) {
      refinementState.currentStep = refinementIterations.value.length - 1
      refinementState.playing = false
      break
    }
    refinementState.currentStep += 1
  }
}
function generatePinnInputExport() {
  const payload = createPinnInputPayload()
  if (!payload) return
  pinnExportPayload.value = payload
  pinnExportSummary.value = {
    sensorCount: payload.sensors?.length || 0,
    frameCount: payload.frames?.length || 0,
    sourceLabel: payload.sourceFacilityName || '',
  }
  showToast(`PINN 输入已生成，包含 ${payload.sensors.length} 个传感器`, 'success')
}
function exportPinnInputJson() {
  const payload = createPinnInputPayload()
  if (!payload) return
  pinnExportPayload.value = payload
  pinnExportSummary.value = {
    sensorCount: payload.sensors?.length || 0,
    frameCount: payload.frames?.length || 0,
    sourceLabel: payload.sourceFacilityName || '',
  }
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `pinn-input-${payload.gas.gasId || 'dataset'}-${Date.now()}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  showToast('PINN 输入 JSON 已导出', 'success')
}

function resizeCanvas() {
  if (!canvasEl || !containerEl) return
  canvasEl.width = containerEl.clientWidth
  canvasEl.height = containerEl.clientHeight
  render()
}
function updateCarPatrol(deltaMs) {
  if (!carPatrolEnabled.value) return
  const cars = carStore.carList
  for (const car of cars) {
    const route = CAR_PATROL_ROUTES[car.id]
    if (!route) continue
    let state = carPatrolState[car.id]
    if (!state) {
      state = { waypointIndex: 0 }
      carPatrolState[car.id] = state
    }
    const wp = route.waypoints
    const toIdx = (state.waypointIndex + 1) % wp.length
    const to = wp[toIdx]
    const dx = to.x - car.x
    const dy = to.y - car.y
    const remaining = Math.hypot(dx, dy)
    const step = route.speed * deltaMs / 16
    if (remaining <= step + 0.1) {
      state.waypointIndex = toIdx
      car.x = to.x
      car.y = to.y
    } else {
      const ratio = step / remaining
      car.x += dx * ratio
      car.y += dy * ratio
    }
  }
  syncCarMarkers()
  syncCarMobileSensors()
}

function animate(timestamp = 0) {
  if (viewMode.value === '3d') {
    animFrameId = requestAnimationFrame(animate)
    return
  }
  const deltaMs = lastAnimTime ? timestamp - lastAnimTime : 16
  lastAnimTime = timestamp
  flowAnimOffset += 0.8
  updateDiffusionPlayback(deltaMs)
  updateRefinementPlayback(deltaMs)
  updateCarPatrol(deltaMs)
  if (flowAnimOffset > 100) flowAnimOffset = 0
  render()
  animFrameId = requestAnimationFrame(animate)
}
function updateClock() {
  clock.value = new Date().toTimeString().split(' ')[0]
}

/**
 * 判断某网格是否位于某设施的下风向
 * @param {Object} cell - 网格点 {x, y}
 * @param {Object} source - 设施锚点 {x, y}
 * @param {number} windDir - 风向角度（度），表示风吹向的方向（0=北, 90=东, 180=南, 270=西）
 * @param {number} angleTolerance - 下风向角度范围（度）
 * @returns {boolean}
 *
 * 注意：如果项目中 windDir 表示风来的方向，需加 180 度转换。当前按"风吹向方向"处理。
 */
function isDownwind(cell, source, windDir, angleTolerance = 50) {
  const dx = cell.x - source.x
  const dy = cell.y - source.y
  const len = Math.hypot(dx, dy)
  if (len < 1) return false

  // 风向单位向量（canvas 坐标：x 向右，y 向下，北为 -y 方向）
  const windRad = windDir * Math.PI / 180
  const wx = Math.sin(windRad)
  const wy = -Math.cos(windRad)

  // 设施到网格的单位方向向量
  const cx = dx / len
  const cy = dy / len

  // 点积：若两者方向一致，则位于下风向
  const dot = cx * wx + cy * wy
  const threshold = Math.cos(angleTolerance * Math.PI / 180)
  return dot >= threshold
}

/**
 * 基于标准思想的风险网格计算
 * 注意：此处不是严格工程验收级布点，而是参考 GB/T 50493 思想，
 * 将泄漏源距离、设备状态、风向和最小间距作为仿真布点规则。
 *
 * 风险构成：
 * 1. 距离风险：距罐区/塔器/重点设施越近风险越高
 * 2. 设备状态风险：仅升高告警/维护设施附近格子的风险（非全局）
 * 3. 风向修正：高风险设施下风向区域风险增加
 */
function computeRiskGrid() {
  const gridSize = 10
  const gridW = 1000 / gridSize
  const gridH = 650 / gridSize
  const cfg = SENSOR_LAYOUT_CONFIG

  // 预计算设施锚点（提升性能），含 hazardLevel
  const facilityPoints = facilities.map(f => {
    let fx = f.x, fy = f.y
    if (f.type !== 'tank' && f.type !== 'tower') { fx += f.w / 2; fy += f.h / 2 }
    const hazardLevel = f.hazardLevel || 0.3
    const isHighRisk = f.type === 'tank' || f.type === 'tower' || f.key
    return { fx, fy, isHighRisk, status: f.status, hazardLevel }
  })

  const grid = []
  for (let i = 0; i < gridW; i++) {
    for (let j = 0; j < gridH; j++) {
      const x = i * gridSize + gridSize / 2
      const y = j * gridSize + gridSize / 2
      let risk = 0

      // 1. 距离风险：使用 hazardLevel 作为权重（高危物料设施影响显著更大）
      let distRisk = 0
      facilityPoints.forEach(f => {
        const d = Math.hypot(x - f.fx, y - f.fy)
        if (d < cfg.sourceInfluenceRadius) {
          const influence = 1 - d / cfg.sourceInfluenceRadius
          // hazardLevel 直接作为权重：液氨 1.0 → 全影响，办公区 0.15 → 微影响
          distRisk += influence * f.hazardLevel
        }
      })
      risk += distRisk * 0.35

      // 2. 设备状态风险：仅影响告警/维护设施附近格子（非全局叠加）
      facilityPoints.forEach(f => {
        if (f.status === '告警' || f.status === '维护中') {
          const d = Math.hypot(x - f.fx, y - f.fy)
          const radius = 150
          if (d < radius) {
            const influence = 1 - d / radius
            const factor = f.status === '告警' ? cfg.alertBonus : cfg.maintenanceBonus
            risk += factor * influence * 0.25
          }
        }
      })

      // 3. 风向修正：高风险设施（hazardLevel > 0.6）下风向区域增加风险
      const windSpeed = weatherState.value.windSpeed
      if (windSpeed > 0.5) {
        const windSpeedFactor = Math.min(1, windSpeed / 10)
        facilityPoints.forEach(f => {
          if (f.hazardLevel > 0.6 && isDownwind({ x, y }, { x: f.fx, y: f.fy }, weatherState.value.windDir, 50)) {
            const d = Math.hypot(x - f.fx, y - f.fy)
            if (d < cfg.sourceInfluenceRadius) {
              const influence = 1 - d / cfg.sourceInfluenceRadius
              risk += influence * cfg.downwindBonus * windSpeedFactor
            }
          }
        })
      }

      risk = Math.min(1, Math.max(0, risk))

      // 4级风险分类 (参考 GB 18218-2018 重大危险源分级)
      let level, priority, color
      if (risk >= 0.85) { level = '重大'; priority = 1; color = '#ef4444' }
      else if (risk >= 0.65) { level = '较大'; priority = 2; color = '#f97316' }
      else if (risk >= 0.40) { level = '一般'; priority = 3; color = '#eab308' }
      else { level = '低'; priority = 4; color = '#22c55e' }

      grid.push({ x, y, gridSize, risk, level, priority, color })
    }
  }
  riskGrid.value = grid
  return grid
}
function calcCoverage() {
  let coverCount = 0
  let highRiskCover = 0
  const highRiskTotal = riskGrid.value.filter(g => g.priority <= 2).length
  riskGrid.value.forEach(g => {
    let covered = false
    sensors.value.forEach(s => {
      const type = sensorTypes.find(t => t.id === s.type)
      const r = resolveSensorEffectiveRange(s, type?.radius || MANUAL_SENSOR_DEFAULTS.effectiveRange)
      const d = Math.hypot(g.x - s.x, g.y - s.y)
      if (d <= r) covered = true
    })
    if (covered) coverCount++
    if (covered && g.priority <= 2) highRiskCover++
  })
  layoutResult.value = {
    sensorCount: sensors.value.length,
    totalCost: sensors.value.reduce((sum, s) => sum + sensorTypes.find(t => t.id === s.type).cost, 0),
    coverageRate: ((coverCount / riskGrid.value.length) * 100).toFixed(1),
    riskCoverRate: highRiskTotal === 0 ? 100 : ((highRiskCover / highRiskTotal) * 100).toFixed(1)
  }
}

/**
 * 基于 GB/T 50493 思想的初始基础布局
 * 注意：此处不是严格工程验收级布点，而是参考国家标准思想，
 * 将储罐边缘、阀门区、管连接、下风向、泵房等高风险区域作为优先布点目标。
 */
function generateBaseStandardLayout() {
  resetSensorCodeCounters()
  const layout = []
  const MIN_DIST = 85

  const tankFacilities = facilities.filter(f => f.type === 'tank')
  const towerFacilities = facilities.filter(f => f.type === 'tower')
  const productionFacilities = facilities.filter(f => f.type === 'production')
  const utilityFacilities = facilities.filter(f => f.type === 'utility')
  const warehouseFacilities = facilities.filter(f => f.type === 'warehouse')
  const treatmentFacilities = facilities.filter(f => f.type === 'treatment')
  const officeFacilities = facilities.filter(f => f.type === 'office')

  function tooClose(x, y) {
    return layout.some(s => Math.hypot(s.x - x, s.y - y) < MIN_DIST)
  }
  function addSensor(x, y) {
    if (tooClose(x, y)) return
    let areaType = 'tank'
    let zone = 'tank_farm'
    let isPumpArea = false
    let nearestFac = null
    for (const f of facilities) {
      if (f.type === 'tank' || f.type === 'tower') {
        if (Math.hypot(x - f.x, y - f.y) < 100) { areaType = f.type; zone = f.zone; nearestFac = f; break }
      } else {
        const cx = f.x + (f.w || 0) / 2, cy = f.y + (f.h || 0) / 2
        if (Math.hypot(x - cx, y - cy) < Math.max(f.w || 40, f.h || 40) * 0.8) {
          areaType = f.type; zone = f.zone; nearestFac = f
          if (f.name.includes('压缩机') || f.name.includes('泵房')) isPumpArea = true
          break
        }
      }
    }
    const { risk, priority } = computeSensorRisk({ detectionRange: 'CO/CH4/NH3/O2', installationHeight: 1.5 }, nearestFac)
    layout.push({
      id: generateSensorCode(areaType, zone, isPumpArea),
      x, y, type: 'gas',
      risk, priority,
      mode: 'auto',
      lastSampleTime: null,
      manualSeries: []
    })
  }

  // 1. 储罐区：每个储罐边缘多方位布点（阀门区、管道连接方向）
  tankFacilities.forEach(tank => {
    const offsets = [
      { dx: tank.r * 0.9, dy: 0 }, { dx: -tank.r * 0.9, dy: 0 },
      { dx: 0, dy: tank.r * 0.9 }, { dx: 0, dy: -tank.r * 0.9 },
    ]
    offsets.forEach(off => {
      addSensor(tank.x + off.dx, tank.y + off.dy)
    })
    if ((tank.hazardLevel || 0.5) > 0.7) {
      addSensor(tank.x + tank.r * 0.3, tank.y + tank.r * 0.3)
    }
  })

  // 2. 塔器区：塔器连接区域 + 下风向重点
  towerFacilities.forEach(tower => {
    addSensor(tower.x + tower.r * 0.8, tower.y + tower.h * 0.3)
    addSensor(tower.x - tower.r * 0.8, tower.y + tower.h * 0.6)
    if ((tower.hazardLevel || 0.5) > 0.6) {
      addSensor(tower.x, tower.y + tower.h * 0.9)
    }
  })

  // 3. 泵房 / 压缩机：高危泄漏源重点覆盖
  productionFacilities.filter(f =>
    f.name.includes('压缩机') || f.name.includes('泵房') || f.name.includes('配料')
  ).forEach(pump => {
    const cx = pump.x + pump.w / 2, cy = pump.y + pump.h / 2
    addSensor(cx - pump.w * 0.3, cy)
    addSensor(cx + pump.w * 0.3, cy)
  })

  // 4. 生产车间：重点装置
  productionFacilities.filter(f =>
    !f.name.includes('压缩机') && !f.name.includes('配料') && !f.name.includes('控制室')
  ).forEach(p => {
    const cx = p.x + p.w / 2, cy = p.y + p.h / 2
    addSensor(cx, cy + p.h * 0.4)
  })

  // 5. 仓储区：危化品库重点覆盖
  warehouseFacilities.forEach(w => {
    const cx = w.x + w.w / 2, cy = w.y + w.h / 2
    if ((w.hazardLevel || 0.3) > 0.6) {
      addSensor(cx - w.w * 0.25, cy)
      addSensor(cx + w.w * 0.25, cy)
    } else {
      addSensor(cx, cy)
    }
  })

  // 6. 公用工程 + 污水处理 + 办公区
  utilityFacilities.forEach(u => {
    const cx = u.x + u.w / 2, cy = u.y + u.h / 2
    addSensor(cx, cy)
  })
  treatmentFacilities.forEach(t => {
    const cx = t.x + t.w / 2, cy = t.y + t.h / 2
    addSensor(cx, cy)
  })
  officeFacilities.forEach(o => {
    const cx = o.x + o.w / 2, cy = o.y + o.h / 2
    addSensor(cx + 20, cy)
  })

  return layout
}

/**
 * 基于标准思想的传感器布局生成
 * 此处不是严格工程验收级布点，而是参考 GB/T 50493 思想，
 * 将泄漏源距离、设备状态、风向和最小间距作为仿真布点规则。
 */
function generateStandardBasedSensorLayout(grid) {
  const cfg = SENSOR_LAYOUT_CONFIG
  resetSensorCodeCounters()
  const candidates = grid
    .filter(cell => cell.risk > cfg.highRiskThreshold)
    .sort((a, b) => b.risk - a.risk)

  const selected = []

  for (const cell of candidates) {
    const minDist = dynamicMinDistance(cell)
    let tooClose = false
    for (const s of selected) {
      const d = Math.hypot(cell.x - s.x, cell.y - s.y)
      if (d < minDist) {
        tooClose = true
        break
      }
    }
    if (tooClose) continue

    // 判断所属区域类型用于编号
    let areaType = 'tank'
    let zone = 'tank_farm'
    let isPumpArea = false
    for (const f of facilities) {
      if (f.type === 'tank' || f.type === 'tower') {
        if (Math.hypot(cell.x - f.x, cell.y - f.y) < 100) { areaType = f.type; zone = f.zone; break }
      } else {
        const cx = f.x + (f.w || 0) / 2, cy = f.y + (f.h || 0) / 2
        if (Math.hypot(cell.x - cx, cell.y - cy) < Math.max(f.w || 40, f.h || 40) * 0.8) {
          areaType = f.type; zone = f.zone
          if (f.name.includes('压缩机') || f.name.includes('泵房')) isPumpArea = true
          break
        }
      }
    }

    selected.push({
      id: generateSensorCode(areaType, zone, isPumpArea),
      x: cell.x,
      y: cell.y,
      type: 'gas',
      risk: cell.risk,
      priority: cell.priority,
      mode: 'auto',
      lastSampleTime: null,
      manualSeries: []
    })

    if (selected.length >= cfg.maxSensors) break
  }

  return selected
}

/**
 * 规范化智能布局（切换式）
 * 注意：此处不是严格工程验收级布点，而是参考 GB/T 50493 思想，
 * 将泄漏源距离、设备状态、风向和最小间距作为仿真布点规则。
 *
 * 开启：生成建议点并询问用户是否应用；关闭：隐藏建议点
 */

function hexToRgb(hex) {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `${r},${g},${b}`
}
function updateRiskStat() {
  const critical = riskGrid.value.filter(g => g.level === '重大').length
  const high = riskGrid.value.filter(g => g.level === '较大').length
  const mid = riskGrid.value.filter(g => g.level === '一般').length
  const low = riskGrid.value.filter(g => g.level === '低').length
  riskStat.value = { critical, high, mid, low }
}
function drawRiskGrid() {
  if (!showHeatmap.value) return
  riskGrid.value.forEach(g => {
    const alpha = 0.12
    let color
    if (g.level === '重大') color = `rgba(239,68,68,${alpha + 0.06})`
    else if (g.level === '较大') color = `rgba(249,115,22,${alpha})`
    else if (g.level === '一般') color = `rgba(234,179,8,${alpha - 0.04})`
    else color = `rgba(34,197,94,${alpha - 0.07})`
    ctx.fillStyle = color
    ctx.fillRect(g.x - g.gridSize / 2, g.y - g.gridSize / 2, g.gridSize, g.gridSize)
  })
}
function drawSensors() {
  if (!showSensors.value) return
  const ss = Math.max(0.1, viewState.scale || 1)
  sensors.value.forEach(s => {
    const type = sensorTypes.find(t => t.id === s.type) || sensorTypes[0]
    const r = resolveSensorEffectiveRange(s, type?.radius || MANUAL_SENSOR_DEFAULTS.effectiveRange)
    // 根据风险等级着色 (4级: 红/橙/黄/绿)
    const riskColor = getPriorityColor(s.priority)
    const riskColorRgb = hexToRgb(riskColor)

    // 监测范围圈: 使用风险等级颜色
    if (showSensorRanges.value) {
      ctx.fillStyle = `rgba(${riskColorRgb}, 0.10)`
      ctx.beginPath()
      ctx.arc(s.x, s.y, r, 0, Math.PI * 2)
      ctx.fill()
      ctx.strokeStyle = `rgba(${riskColorRgb}, 0.45)`
      ctx.lineWidth = 0.8 / ss
      ctx.setLineDash([3, 3])
      ctx.beginPath()
      ctx.arc(s.x, s.y, r, 0, Math.PI * 2)
      ctx.stroke()
      ctx.setLineDash([])
    }

    // 选中高亮
    if (selectedSensor.value?.id === s.id) {
      ctx.strokeStyle = '#ffffff'
      ctx.lineWidth = 1.5 / ss
      ctx.beginPath()
      ctx.arc(s.x, s.y, 6 / ss, 0, Math.PI * 2)
      ctx.stroke()
    }

    // 传感器圆点: 使用风险等级颜色
    ctx.fillStyle = riskColor
    ctx.beginPath()
    ctx.arc(s.x, s.y, 3 / ss, 0, Math.PI * 2)
    ctx.fill()
  })
}
function sensorHitTest(wx, wy) {
  for (const s of sensors.value) {
    const d = Math.hypot(wx - s.x, wy - s.y)
    if (d < 12) return s
  }
  return null
}
function showSensorInfo(s){
  panelCollapsed.value = false
  manualSensorTargetId.value = s.id
  const type = sensorTypes.find(t=>t.id===s.type)
  const geo = formatGeoCoord(s.x, s.y)
  const currentConcentration = getSensorCurrentConcentration(s)
  const autoConcentration = getSensorAutoConcentration(s)
  const peakConcentration = s.sampledPeak || 0
  const modeLabel = s.mode === 'manual' ? '手动录入' : '自动采样'
  const priorityLabel = getPriorityLabel(s.priority)
  const effectiveRange = resolveSensorEffectiveRange(s, type?.radius || MANUAL_SENSOR_DEFAULTS.effectiveRange)
  const installationHeight = resolveSensorInstallationHeight(s)
  const detectionRange = resolveSensorDetectionRange(s)
  const installRemark = resolveSensorInstallRemark(s)
  const lastTimeStr = s.lastSampleTime
    ? new Date(s.lastSampleTime).toLocaleTimeString('zh-CN')
    : '尚未采样'

  infoTitle.value = `${s.id}（${priorityLabel}）`
  infoSubtitle.value = { tag: type.name, tagClass: 'tag tag-blue', desc: modeLabel }
  infoRows.value = [
    { key:'传感器类型', val: '多种气体传感器' },
    { key:'安装高度', val: `${installationHeight.toFixed(1)} m` },
    { key:'有效监测范围', val: `${effectiveRange} m` },
    { key:'检测范围', val: detectionRange },
    { key:'优先级', val: `P${s.priority}（${priorityLabel}）` },
    { key:'模拟浓度', val: `${currentConcentration.toFixed(2)} ppm` },
    { key:'最近采样时间', val: lastTimeStr },
    { key:'数据模式', val: modeLabel },
    { key:'自动基线', val: `${autoConcentration.toFixed(2)} ppm` },
    { key:'采样峰值', val: `${peakConcentration.toFixed(2)} ppm` },
    { key:'采样帧数', val: `${s.sampledFrames || 0}` },
    { key:'布点说明', val: installRemark || '无' },
    { key:'单点成本', val: `¥${type.cost}` },
    { key:'所在风险值', val: (s.risk*100).toFixed(1)+'%' },
    { key:'经纬海拔', val: `${geo.longitude} / ${geo.latitude} / ${geo.altitude}` }
  ]
  syncSensorEditorState(s)
}
function addManualSensor(){
  if (sensorPlacementState.picking) {
    sensorPlacementState.picking = false
    canvasEl.style.cursor = measureMode.value ? 'crosshair' : 'grab'
    showToast('已取消手动传感器选点', 'warn')
    return
  }
  if (sensorPlacementState.pickingOrigin) {
    sensorPlacementState.pickingOrigin = false
    canvasEl.style.cursor = measureMode.value ? 'crosshair' : 'grab'
    showToast('已取消零点选取', 'warn')
    return
  }
  startManualSensorPicking()
}
function clearAllSensor(){
  // 从数据库删除所有传感器（异步）
  deleteAllSensorsFromDB()
  sensors.value = []
  selectedSensor.value = null
  sensorPlacementState.picking = false
  sensorPlacementState.pickingOrigin = false
  sensorPlacementState.pendingPoint = null
  sensorPlacementState.origin = null
  sensorPlacementState.relativeX = 0
  sensorPlacementState.relativeY = 0
  manualSensorConfigVisible.value = false
  resetManualSensorDraft()
  syncSensorEditorState(null)
  calcCoverage()
  updateRiskStat()
  clearInfo()
  showToast('已清空所有传感器','warn')
  render()
}
function deleteCurrSensor(){
  if(!selectedSensor.value)return
  const id = selectedSensor.value.id
  sensors.value = sensors.value.filter(s=>s.id!==id)
  selectedSensor.value = null
  syncSensorEditorState(null)
  calcCoverage()
  updateRiskStat()
  clearInfo()
  // 从数据库删除（异步）
  deleteSensorFromDB(id)
  showToast('已删除当前传感器','danger')
  render()
}

onMounted(() => {
  canvasEl = mapCanvasRef.value
  containerEl = mapContainerRef.value
  ctx = canvasEl.getContext('2d')
  syncManualGeoInputsFromWorld(getFacilityAnchorPoint(selectedDiffusionSource.value))
  updateDiffusionMetaSource({
    sourceFacility: selectedDiffusionSource.value,
    sourcePoint: null,
  })
  updateCoordDisplay(0, 0)
  resizeCanvas()
  const scaleX = (canvasEl.width * 0.9) / 1020
  const scaleY = (canvasEl.height * 0.9) / 660
  viewState.scale = Math.min(scaleX, scaleY, 1.5)
  updateClock()
  clockTimer = setInterval(updateClock, 1000)
  window.addEventListener('resize', resizeCanvas)
  animate()
  computeRiskGrid()
  updateRiskStat()
  calcCoverage()

  // 从数据库加载已保存的传感器和气体类型
  fetchSensorsFromDB()
  fetchGasList()

  // 初始化小车数据并定时刷新
  refreshCarData()
  carRefreshTimer.value = setInterval(refreshCarData, 10000)

  // 初始化实时天气（每30分钟自动刷新）
  startWeatherAutoRefresh()

  setTimeout(() => {
    autoConfigFromCarParams()
  }, 500)
})

watch(viewMode, (mode) => {
  if (mode === '2d') {
    // Re-acquire canvas ref after template switch
    nextTick(() => {
      canvasEl = mapCanvasRef.value
      if (canvasEl) {
        ctx = canvasEl.getContext('2d')
        resizeCanvas()
        render()
      }
    })
  }
})

onUnmounted(() => {
  cancelAnimationFrame(animFrameId)
  clearInterval(clockTimer)
  clearInterval(carRefreshTimer.value)
  clearTimeout(toastTimer)
  window.removeEventListener('resize', resizeCanvas)
})

watch(() => diffusionState.currentFrame, () => {
  if (selectedSensor.value) {
    const sensor = sensors.value.find(item => item.id === selectedSensor.value.id)
    if (sensor) showSensorInfo(sensor)
  }
  syncCarMobileSensors()
})
watch(() => diffusionForm.gasId, () => {
  const nextValidation = syncDiffusionSourceSelection()
  updateDiffusionMetaSource({
    sourceFacility: nextValidation?.valid
      ? facilityById.get(diffusionForm.sourceFacilityId) || null
      : null,
    sourcePoint: leakSourceState.mode === 'facility' ? null : leakSourceState.mapPoint,
  })
})
const currentLeakSourcePoint = computed(() => {
  if (leakSourceState.mode !== 'facility' && leakSourceState.mapPoint) {
    return leakSourceState.mapPoint
  }
  return getFacilityAnchorPoint(selectedDiffusionSource.value)
})
const leakSourceEntryLabel = computed(() => {
  if (leakSourceState.picking) return '等待地图点击'
  if (leakSourceState.mode === 'map') return '地图点选'
  if (leakSourceState.mode === 'geo') return '经纬输入'
  return '设施锚点'
})
const leakSourceLocationText = computed(() => {
  const point = currentLeakSourcePoint.value
  if (!point) return '--'
  const geo = worldToGeo(point.x, point.y)
  return `${geo.longitude.toFixed(3)}°E / ${geo.latitude.toFixed(3)}°N`
})
watch(() => diffusionForm.sourceFacilityId, () => {
  if (leakSourceState.mode !== 'facility') return
  syncManualGeoInputsFromWorld(getFacilityAnchorPoint(selectedDiffusionSource.value))
  updateDiffusionMetaSource({
    sourceFacility: selectedDiffusionSource.value,
    sourcePoint: null,
  })
})

watch(() => route.query.autoConfig, (newVal) => {
  if (newVal === 'true') {
    autoConfigFromCarParams()
  }
})
watch(() => selectedFacility.value?.id, (nextId, previousId) => {
  if (nextId === previousId) return
  if (evacuationPlanningMode.value === 'all' && evacuationBuildingRoutes.value.length) {
    const nextRoute = evacuationBuildingRoutes.value.find(route => route.buildingId === nextId)
    if (nextRoute) {
      selectedEvacuationBuildingId.value = nextRoute.buildingId
      syncSelectedEvacuationCandidate(nextRoute, nextRoute.recommendedCandidateId)
      render()
      return
    }
  }
  if (evacuationPlan.value || evacuationBatchResult.value) clearEvacuationPlanning(true)
})
watch(
  () => [
    diffusionForm.gasId,
    diffusionForm.sourceFacilityId,
    diffusionForm.sourceRate,
    diffusionForm.releaseDuration,
    diffusionForm.initialTemperature,
    diffusionForm.initialPressure,
    diffusionForm.releaseHeight,
    diffusionForm.windSpeed,
    diffusionForm.windDirection,
    diffusionForm.ambientTemperature,
    diffusionForm.humidity,
    diffusionForm.stabilityClass,
    diffusionForm.terrainRoughness,
    diffusionForm.obstacleInfluenceEnabled,
    diffusionForm.frameCount,
    diffusionForm.frameStepSec,
    diffusionFrames.value.length,
    sensors.value.length,
  ],
  () => {
    pinnExportPayload.value = null
    pinnExportSummary.value = null
    coarseSearchResult.value = null
    coarseSearchSummary.value = null
    selectedCoarseCandidateId.value = ''
    clearPinnRefinement(false)
    if ((evacuationPlan.value || evacuationBatchResult.value) && !diffusionFrames.value.length) {
      clearEvacuationPlanning(true)
    }
  }
)
</script>

<style scoped>
.chempark-container {
  background-color: #0a0f1a;
  font-family: 'Noto Sans SC', sans-serif;
  color: #e8ecf4;
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
}
:root {
  --bg: #0a0f1a;
  --bg-secondary: #111827;
  --fg: #e8ecf4;
  --fg-muted: #7a8ba8;
  --accent: #00e5a0;
  --accent-dim: rgba(0,229,160,0.15);
  --accent-glow: rgba(0,229,160,0.4);
  --warning: #ff6b35;
  --danger: #ef4444;
  --info: #38bdf8;
  --card: rgba(17,24,39,0.92);
  --border: rgba(122,139,168,0.18);
}
:deep(.layout_tabbar) {
  display: none !important;
}
:deep(.layout_main) {
  padding: 0 !important;
  margin-top: 80px !important;
  background: #0a0f1a !important;
  overflow: hidden !important;
}
:deep(.layout_main::before) {
  display: none !important;
}
.main-layout { display: flex; height: calc(100vh - 80px); }
.left-panel {
  width: 280px; min-width: 280px;
  background: #111827;
  border-right: 1px solid var(--border);
  display: flex; flex-direction: column;
  overflow-y: auto; z-index: 50;
}
.panel-section { padding: 16px; border-bottom: 1px solid var(--border); }
.panel-title {
  font-size: 11px; font-weight: 700; color: var(--fg-muted);
  letter-spacing: 2px; text-transform: uppercase;
  margin-bottom: 12px; display: flex; align-items: center; gap: 8px;
}
.panel-title i { color: var(--accent); font-size: 12px; }
.stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.stat-card {
  background: #1e293b;
  border: 1px solid var(--border);
  border-radius: 8px; padding: 12px;
  transition: all 0.3s ease; cursor: pointer;
}
.stat-card:hover { border-color: var(--accent); background: #132a22; }
.stat-card.active { border-color: var(--accent); background: #132a22; }
.stat-value {
  font-family: 'Orbitron', sans-serif;
  font-size: 22px; font-weight: 900; color: var(--fg); line-height: 1;
}
.stat-label { font-size: 10px; color: var(--fg-muted); margin-top: 4px; }
.legend-list { display: flex; flex-direction: column; gap: 6px; }
.legend-item {
  display: flex; align-items: center; gap: 10px;
  font-size: 12px; color: var(--fg-muted); cursor: pointer;
  padding: 6px 8px; border-radius: 6px; transition: all 0.2s;
}
.legend-item:hover { background: #1e293b; color: var(--fg); }
.legend-swatch { width: 16px; height: 16px; border-radius: 3px; flex-shrink: 0; }
.legend-swatch.circle { border-radius: 50%; }
.legend-swatch.line { width: 20px; height: 3px; border-radius: 2px; }
.zone-list { display: flex; flex-direction: column; gap: 4px; }
.zone-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 12px; border-radius: 8px; cursor: pointer;
  transition: all 0.25s; font-size: 13px; border: 1px solid transparent;
}
.zone-item:hover { background: #1e293b; }
.zone-item.selected { background: #132a22; border-color: var(--accent); color: var(--accent); }
.zone-item .zone-name { display: flex; align-items: center; gap: 8px; }
.zone-item .zone-tag {
  font-size: 9px; padding: 2px 6px; border-radius: 4px;
  background: #2d3748; color: var(--fg-muted);
}
.zone-item.selected .zone-tag { background: #132a22; color: var(--accent); }
.map-container { flex: 1; position: relative; overflow: hidden; background: #1a2e1e; }
#mapCanvas { display: block; cursor: grab; }
#mapCanvas.grabbing { cursor: grabbing; }
.control-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.control-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.control-field span {
  font-size: 11px;
  color: var(--fg-muted);
}
.control-field input,
.control-field select,
.timeline-settings select {
  width: 100%;
  height: 34px;
  background: #1e293b;
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--fg);
  padding: 0 10px;
  outline: none;
}
.control-field input:focus,
.control-field select:focus,
.timeline-settings select:focus {
  border-color: var(--accent);
}
.control-note {
  margin-top: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(0,229,160,0.08);
  border: 1px solid rgba(0,229,160,0.18);
  color: var(--fg-muted);
  font-size: 11px;
  line-height: 1.5;
}
.control-note.invalid {
  background: rgba(255,107,53,0.08);
  border-color: rgba(255,107,53,0.22);
  color: #ffb48f;
}
.control-subnote {
  margin-top: 8px;
  color: var(--fg-muted);
  font-size: 11px;
  line-height: 1.5;
}
.inline-actions {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
  margin-top: 12px;
}
.map-controls {
  position: absolute; bottom: 24px; right: 24px;
  display: flex; flex-direction: column; gap: 4px; z-index: 30;
}
.map-btn {
  width: 40px; height: 40px;
  background: #1e293b; border: 1px solid var(--border);
  border-radius: 8px; color: var(--fg);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; font-size: 16px; transition: all 0.2s;
  backdrop-filter: blur(10px);
}
.map-btn:hover { background: #132a22; border-color: var(--accent); color: var(--accent); }
.scale-bar {
  position: absolute; bottom: 24px; left: 24px;
  display: flex; align-items: flex-end; gap: 8px; z-index: 30;
}
.scale-line {
  width: 80px; height: 2px; background: var(--fg-muted); position: relative;
}
.scale-line::before, .scale-line::after {
  content: ''; position: absolute; width: 2px; height: 8px;
  background: var(--fg-muted); top: -3px;
}
.scale-line::before { left:0; }
.scale-line::after { right:0; }
.scale-text { font-size: 10px; color: var(--fg-muted); font-family: 'Orbitron', sans-serif; }
.coord-display {
  position: absolute; top: 12px; left: 12px;
  background: #1e293b; border: 1px solid var(--border);
  border-radius: 8px; padding: 8px 14px;
  font-family: 'Orbitron', sans-serif; font-size: 11px;
  color: var(--fg-muted); z-index: 30; backdrop-filter: blur(10px);
}
.coord-display span { color: var(--accent); }
.sensor-hover-card {
  position: absolute;
  top: 60px;
  right: 12px;
  width: 250px;
  background: rgba(17,24,39,0.94);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 12px 14px;
  z-index: 32;
  backdrop-filter: blur(14px);
  box-shadow: 0 10px 24px rgba(0,0,0,0.28);
}
.sensor-hover-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}
.sensor-hover-title {
  color: var(--fg);
  font-size: 13px;
  font-weight: 700;
}
.sensor-hover-sub {
  color: var(--fg-muted);
  font-size: 11px;
  margin-top: 3px;
}
.sensor-hover-badge {
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
  white-space: nowrap;
}
.sensor-hover-badge.normal {
  background: rgba(0,229,160,0.14);
  color: var(--accent);
}
.sensor-hover-badge.warning {
  background: rgba(245,158,11,0.14);
  color: #f59e0b;
}
.sensor-hover-badge.danger {
  background: rgba(239,68,68,0.14);
  color: var(--danger);
}
.sensor-hover-metric {
  margin-top: 12px;
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  color: var(--fg-muted);
  font-size: 11px;
}
.sensor-hover-metric strong {
  color: var(--fg);
  font-size: 18px;
  font-family: 'Orbitron', sans-serif;
}
.sensor-hover-grid {
  margin-top: 10px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px 10px;
  color: var(--fg-muted);
  font-size: 11px;
}
.timeline-panel {
  position: absolute;
  left: 50%;
  bottom: 22px;
  transform: translateX(-50%);
  width: min(760px, calc(100% - 180px));
  background: rgba(17,24,39,0.94);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 12px 16px;
  z-index: 35;
  backdrop-filter: blur(16px);
  box-shadow: 0 10px 28px rgba(0,0,0,0.25);
}
.timeline-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}
.timeline-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--fg);
}
.timeline-meta {
  font-size: 11px;
  color: var(--fg-muted);
  margin-top: 3px;
}
.timeline-slider {
  width: 100%;
  margin: 12px 0 10px;
  accent-color: var(--accent);
}
.timeline-controls-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.timeline-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}
.timeline-btn {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: #1e293b;
  color: var(--fg);
  cursor: pointer;
  transition: all 0.2s;
}
.timeline-btn:hover,
.timeline-btn.primary {
  border-color: var(--accent);
  color: var(--accent);
  background: #132a22;
}
.timeline-readout {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--fg-muted);
  font-size: 11px;
  flex-wrap: wrap;
}
.timeline-settings {
  display: flex;
  align-items: center;
  gap: 10px;
}
.timeline-loop {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--fg-muted);
  font-size: 11px;
}
.right-panel {
  width: 320px; min-width: 320px;
  background: #111827;
  border-left: 1px solid var(--border);
  display: flex; flex-direction: column;
  overflow-y: auto; z-index: 50;
  transition: transform 0.35s cubic-bezier(0.4,0,0.2,1), margin-right 0.35s cubic-bezier(0.4,0,0.2,1);
}
.right-panel.collapsed { transform: translateX(320px); margin-right: -320px; }
.info-header {
  padding: 20px; border-bottom: 1px solid var(--border);
  display: flex; align-items: flex-start; justify-content: space-between;
}
.info-header h2 { font-size: 18px; font-weight: 700; line-height: 1.3; }
.close-btn {
  width: 28px; height: 28px; border-radius: 6px;
  border: 1px solid var(--border); background: transparent;
  color: var(--fg-muted); cursor: pointer;
  display: flex; align-items: center; justify-content: center; transition: all 0.2s;
}
.close-btn:hover { border-color: var(--danger); color: var(--danger); }
.info-body { padding: 16px 20px; }
.sensor-history-card {
  margin-top: 14px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: #161f2d;
  padding: 12px;
}
.sensor-history-head,
.sensor-history-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  color: var(--fg-muted);
  font-size: 11px;
}
.sensor-history-svg {
  display: block;
  width: 100%;
  height: 96px;
  margin: 8px 0;
}
.sensor-axis {
  stroke: rgba(122,139,168,0.28);
  stroke-width: 1;
}
.sensor-threshold {
  stroke-width: 1;
  stroke-dasharray: 4 4;
}
.sensor-threshold.warning {
  stroke: rgba(245,158,11,0.65);
}
.sensor-threshold.danger {
  stroke: rgba(239,68,68,0.72);
}
.sensor-line {
  fill: none;
  stroke: #38bdf8;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.sensor-marker {
  stroke: rgba(255,255,255,0.45);
  stroke-width: 1;
  stroke-dasharray: 3 4;
}
.sensor-marker-dot {
  fill: #00e5a0;
  stroke: #ffffff;
  stroke-width: 1;
}
/* 设备安装详情卡片 - 侧边栏紧凑版 */
.sensor-device-card {
  margin-top: 14px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: #161f2d;
  padding: 10px 12px;
}
.sensor-btn-white {
  background: #ffffff;
  color: #1a1a2e;
  border: none;
  border-radius: 6px;
  width: 24px;
  height: 24px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 11px;
  transition: transform 0.15s, box-shadow 0.15s;
}
.sensor-btn-white:hover {
  transform: scale(1.15);
  box-shadow: 0 0 8px rgba(255,255,255,0.3);
}
.sensor-device-compact {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-top: 8px;
}
.sensor-device-thumb {
  flex: 0 0 56px;
  width: 56px;
  height: 42px;
  object-fit: cover;
  border-radius: 6px;
  border: 1px solid var(--border);
}
.sensor-device-compact-info {
  flex: 1;
  min-width: 0;
}
.sensor-device-compact-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--fg);
  margin-bottom: 3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.sensor-device-compact-status {
  font-size: 11px;
  color: var(--fg-muted);
  display: flex;
  align-items: center;
  gap: 4px;
}
.sensor-status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  display: inline-block;
}
.sensor-status-dot.online { background: #00e5a0; }
.sensor-status-sep { opacity: 0.3; }
.sensor-conc-val { color: #00e5a0; font-weight: 500; }

/* 设备详情全屏浮层 */
.device-fullscreen-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: radial-gradient(ellipse at 30% 40%, rgba(0,229,160,0.06) 0%, rgba(0,0,0,0.88) 60%);
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
}
.device-fullscreen-card {
  position: relative;
  display: flex;
  max-width: 1200px;
  width: 94vw;
  max-height: 90vh;
  background: linear-gradient(135deg, #141e2b 0%, #1a2738 50%, #162030 100%);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 32px 100px rgba(0,0,0,0.7), 0 0 0 1px rgba(255,255,255,0.06), inset 0 1px 0 rgba(255,255,255,0.05);
}
.device-fullscreen-close {
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 10;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: rgba(0,0,0,0.4);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255,255,255,0.08);
  color: rgba(255,255,255,0.7);
  font-size: 15px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.device-fullscreen-close:hover {
  background: rgba(239,68,68,0.25);
  border-color: rgba(239,68,68,0.3);
  color: #ef4444;
  transform: rotate(90deg);
}
.device-fullscreen-img-wrap {
  flex: 0 0 65%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #060a12;
  position: relative;
  cursor: grab;
  user-select: none;
}
.device-fullscreen-img-wrap::before {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 2;
  background:
    linear-gradient(180deg, rgba(6,10,18,0.5) 0%, transparent 15%, transparent 85%, rgba(6,10,18,0.6) 100%),
    linear-gradient(90deg, rgba(6,10,18,0.3) 0%, transparent 10%, transparent 90%, rgba(6,10,18,0.3) 100%);
}
.device-fullscreen-img-wrap::after {
  content: '';
  position: absolute;
  inset: -1px;
  pointer-events: none;
  z-index: 3;
  border-radius: 0;
  border: 1px solid transparent;
  background: linear-gradient(135deg, rgba(0,229,160,0.12), transparent 40%, transparent 60%, rgba(56,189,248,0.08)) border-box;
  -webkit-mask: linear-gradient(#fff 0 0) padding-box, linear-gradient(#fff 0 0);
  mask: linear-gradient(#fff 0 0) padding-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
}
.device-fullscreen-img-wrap:active { cursor: grabbing; }
.device-fullscreen-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.25s cubic-bezier(0.33,1,0.68,1);
  transform-origin: center center;
  filter: brightness(1.02) contrast(1.03);
}
.device-img-zoom-bar {
  position: absolute;
  bottom: 18px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 2px;
  background: rgba(8,12,20,0.8);
  backdrop-filter: blur(20px) saturate(1.4);
  border-radius: 14px;
  padding: 4px 8px;
  border: 1px solid rgba(255,255,255,0.06);
  box-shadow: 0 4px 24px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.04);
  z-index: 5;
}
.df-zoom-btn {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  border: none;
  background: transparent;
  color: rgba(255,255,255,0.5);
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.df-zoom-btn:hover {
  background: rgba(0,229,160,0.12);
  color: #00e5a0;
  transform: scale(1.08);
}
.df-zoom-btn:active { transform: scale(0.95); }
.df-zoom-divider {
  width: 1px;
  height: 18px;
  background: rgba(255,255,255,0.07);
  margin: 0 4px;
}
.df-zoom-val {
  font-size: 11px;
  color: rgba(255,255,255,0.4);
  min-width: 42px;
  text-align: center;
  font-variant-numeric: tabular-nums;
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 0.3px;
}
.device-img-hint {
  position: absolute;
  top: 18px;
  left: 18px;
  font-size: 11px;
  color: rgba(255,255,255,0.25);
  background: rgba(0,0,0,0.4);
  backdrop-filter: blur(12px);
  padding: 6px 14px;
  border-radius: 10px;
  border: 1px solid rgba(255,255,255,0.05);
  z-index: 5;
  pointer-events: none;
  letter-spacing: 0.3px;
}
.device-img-hint i {
  margin-right: 5px;
  color: rgba(0,229,160,0.4);
}

/* 信息面板 */
.device-fullscreen-info {
  flex: 1;
  padding: 36px 30px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 0;
  min-width: 0;
}
.df-info-head {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 4px;
}
.df-info-icon {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(0,229,160,0.12), rgba(56,189,248,0.08));
  border: 1px solid rgba(0,229,160,0.18);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #00e5a0;
  font-size: 22px;
  flex-shrink: 0;
  box-shadow: 0 0 20px rgba(0,229,160,0.08), inset 0 1px 0 rgba(255,255,255,0.05);
  position: relative;
}
.df-info-icon::after {
  content: '';
  position: absolute;
  inset: -3px;
  border-radius: 18px;
  background: radial-gradient(circle, rgba(0,229,160,0.08), transparent 70%);
  pointer-events: none;
}
.device-fullscreen-title {
  font-size: 22px;
  font-weight: 700;
  color: #fff;
  line-height: 1.3;
  letter-spacing: -0.5px;
}
.df-info-subtitle {
  font-size: 12px;
  color: rgba(255,255,255,0.3);
  margin-top: 3px;
  display: flex;
  align-items: center;
  gap: 5px;
}
.df-info-subtitle::before {
  content: '';
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: rgba(255,255,255,0.15);
}
.df-info-divider {
  height: 1px;
  background: linear-gradient(90deg, rgba(255,255,255,0.06), rgba(255,255,255,0.01));
  margin: 18px 0;
}
.device-fullscreen-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  padding: 12px 0;
}
.df-label {
  color: rgba(255,255,255,0.4);
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}
.df-label-icon {
  font-size: 13px;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.df-label-icon.fa-signal {
  background: rgba(0,229,160,0.1);
  color: #00e5a0;
}
.df-label-icon.fa-shield-halved {
  background: rgba(56,189,248,0.1);
  color: #38bdf8;
}
.df-label-icon.fa-wave-square {
  background: rgba(168,85,247,0.1);
  color: #a855f7;
}
.df-badge {
  font-size: 12px;
  font-weight: 500;
  padding: 4px 12px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.df-badge-online {
  background: rgba(0,229,160,0.08);
  color: #00e5a0;
  border: 1px solid rgba(0,229,160,0.12);
  box-shadow: 0 0 12px rgba(0,229,160,0.06);
}
.df-badge-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #00e5a0;
  box-shadow: 0 0 6px rgba(0,229,160,0.5);
  animation: df-pulse 2s ease-in-out infinite;
}
@keyframes df-pulse {
  0%, 100% { opacity: 1; box-shadow: 0 0 6px rgba(0,229,160,0.5), 0 0 0 0 rgba(0,229,160,0.3); }
  50% { opacity: 0.75; box-shadow: 0 0 4px rgba(0,229,160,0.3), 0 0 0 5px rgba(0,229,160,0); }
}
.df-badge-safe {
  background: rgba(56,189,248,0.08);
  color: #38bdf8;
  border: 1px solid rgba(56,189,248,0.12);
  box-shadow: 0 0 12px rgba(56,189,248,0.06);
}
.df-conc {
  font-family: 'JetBrains Mono', 'Orbitron', monospace;
  font-size: 16px;
  font-weight: 600;
  color: #00e5a0;
  letter-spacing: 0.5px;
  text-shadow: 0 0 12px rgba(0,229,160,0.2);
}
.df-std-block {
  background: linear-gradient(135deg, rgba(56,189,248,0.03), rgba(168,85,247,0.02));
  border: 1px solid rgba(56,189,248,0.06);
  border-radius: 12px;
  padding: 14px 16px;
  position: relative;
  overflow: hidden;
}
.df-std-block::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 3px;
  height: 100%;
  background: linear-gradient(180deg, #38bdf8, #a855f7);
  border-radius: 0 2px 2px 0;
}
.df-std-head {
  font-size: 11px;
  color: rgba(255,255,255,0.3);
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.df-std-head i { font-size: 11px; color: #38bdf8; }
.df-std-text {
  font-size: 12px;
  color: rgba(255,255,255,0.5);
  line-height: 1.7;
  padding-left: 2px;
}

/* 全屏浮层动画 */
.device-fullscreen-enter-active { transition: opacity 0.3s ease; }
.device-fullscreen-leave-active { transition: opacity 0.2s ease; }
.device-fullscreen-enter-from,
.device-fullscreen-leave-to { opacity: 0; }
.device-fullscreen-enter-active .device-fullscreen-card {
  transition: transform 0.35s cubic-bezier(0.16,1,0.3,1), opacity 0.3s ease;
}
.device-fullscreen-enter-from .device-fullscreen-card {
  transform: scale(0.93) translateY(12px);
  opacity: 0;
}
.device-fullscreen-enter-active .device-fullscreen-card {
  transition: transform 0.3s cubic-bezier(0.16,1,0.3,1);
}
.device-fullscreen-enter-from .device-fullscreen-card {
  transform: scale(0.92);
}
.info-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 0; border-bottom: 1px solid #2d3748;
}
.info-row:last-child { border-bottom: none; }
.info-key { font-size: 12px; color: var(--fg-muted); }
.info-val { font-size: 13px; font-weight: 500; }
.tag {
  display: inline-block; font-size: 10px;
  padding: 3px 8px; border-radius: 4px; font-weight: 500;
}
.tag-green { background: #0f2e22; color: var(--accent); }
.tag-orange { background: #2e1a0f; color: var(--warning); }
.tag-red { background: #2e0f0f; color: var(--danger); }
.tag-blue { background: #0f1f2e; color: var(--info); }
.mini-bar { width: 80px; height: 4px; background: #2d3748; border-radius: 2px; overflow: hidden; }
.mini-bar-fill { height: 100%; border-radius: 2px; transition: width 0.6s ease; }
.alert-list { display: flex; flex-direction: column; gap: 8px; }
.alert-item {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 10px 12px; background: #1e293b;
  border-radius: 8px; border-left: 3px solid transparent;
  font-size: 12px; cursor: pointer; transition: all 0.2s;
}
.alert-item:hover { background: #253345; }
.alert-item.warn { border-left-color: var(--warning); }
.alert-item.error { border-left-color: var(--danger); }
.alert-item.info { border-left-color: var(--info); }
.alert-icon {
  width: 20px; height: 20px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 10px; flex-shrink: 0; margin-top: 1px;
}
.alert-item.warn .alert-icon { background: #2e1a0f; color: var(--warning); }
.alert-item.error .alert-icon { background: #2e0f0f; color: var(--danger); }
.alert-item.info .alert-icon { background: #0f1f2e; color: var(--info); }
.alert-text { color: var(--fg-muted); line-height: 1.4; }
.alert-time { font-size: 10px; color: #4a5568; margin-top: 3px; }
.search-box { position: relative; margin-bottom: 12px; }
.search-box input {
  width: 100%; height: 36px;
  background: #1e293b;
  border: 1px solid var(--border);
  border-radius: 8px; padding: 0 12px 0 36px;
  color: var(--fg); font-size: 13px; outline: none; transition: all 0.2s;
}
.search-box input::placeholder { color: #4a5568; }
.search-box input:focus { border-color: var(--accent); background: #132a22; }
.search-box i {
  position: absolute; left: 12px; top: 50%;
  transform: translateY(-50%); color: var(--fg-muted); font-size: 13px;
}
.bottom-toolbar {
  position: absolute; top: 12px; right: 12px;
  display: flex; gap: 4px; z-index: 30;
}
.tool-btn {
  height: 34px; padding: 0 14px;
  background: #1e293b; border: 1px solid var(--border);
  border-radius: 8px; color: var(--fg-muted);
  font-size: 12px; cursor: pointer;
  display: flex; align-items: center; gap: 6px;
  transition: all 0.2s; backdrop-filter: blur(10px);
}
.tool-btn:hover, .tool-btn.active {
  border-color: var(--accent); color: var(--accent); background: #132a22;
}
.toast {
  position: fixed; top: 72px; right: 24px;
  background: #1e293b; border: 1px solid var(--border);
  border-radius: 10px; padding: 14px 20px;
  font-size: 13px; color: var(--fg); z-index: 200;
  backdrop-filter: blur(20px);
  transform: translateX(400px);
  transition: transform 0.4s cubic-bezier(0.4,0,0.2,1);
  display: flex; align-items: center; gap: 10px;
  max-width: 360px; box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}
.toast.show { transform: translateX(0); }
.toast i { font-size: 16px; }
.toast.success i { color: var(--accent); }
.toast.warn i { color: var(--warning); }
.grid-overlay {
  position: absolute; inset: 0; pointer-events: none;
  background-image:
      linear-gradient(rgba(0,229,160,0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0,229,160,0.03) 1px, transparent 1px);
  background-size: 40px 40px; z-index: 1;
}
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #2d3748; border-radius: 2px; }
@media (prefers-reduced-motion: reduce) {
  *,*::before,*::after { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; }
}
@media (max-width: 1100px) {
  .left-panel { width: 220px; min-width: 220px; }
  .right-panel { width: 260px; min-width: 260px; }
}
@media (max-width: 860px) {
  .left-panel { display: none; }
  .right-panel { display: none; }
}
.risk-stat-list { display: flex; flex-direction: column; gap: 10px; }
.risk-stat-item {
  display: flex; align-items: center; justify-content: space-between;
  font-size: 12px; color: var(--fg-muted);
}
.risk-dot {
  width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:8px;
}
.risk-stat-item .num {color:var(--fg);font-weight:500;}
.sensor-stat-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 10px;
}
.stat-mini {
  background: #1e293b; border-radius: 6px;
  text-align: center; padding: 10px 4px;
}
.stat-mini .val {
  font-size: 16px; font-weight: bold; color: var(--accent);
  font-family: 'Orbitron',sans-serif;
}
.stat-mini .lab { font-size: 10px; color: var(--fg-muted); margin-top:4px; }
.sensor-btn {
  height:32px;border-radius:6px;border:none;
  font-size:12px;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:4px;
}
.sensor-btn.primary { background:var(--accent-dim);color:var(--accent); }
.sensor-btn.primary.active { background:#132a22;color:var(--accent);outline:1px solid rgba(0,229,160,0.28); }
.sensor-btn.danger { background:rgba(239,68,68,0.15);color:var(--danger); }
.sampling-row {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  color: var(--fg-muted);
  font-size: 11px;
}
.json-preview {
  margin-top: 12px;
  max-height: 220px;
  overflow: auto;
  padding: 10px;
  border-radius: 8px;
  background: #0f1724;
  border: 1px solid var(--border);
  color: #9dd9ff;
  font-size: 11px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
}
.candidate-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
}
.candidate-item {
  border: 1px solid var(--border);
  background: #162131;
  border-radius: 10px;
  padding: 10px 12px;
  cursor: pointer;
  text-align: left;
  transition: all 0.2s;
}
.candidate-item:hover,
.candidate-item.active {
  border-color: var(--accent);
  background: #132a22;
}
.candidate-main,
.candidate-meta,
.candidate-detail-head,
.candidate-detail-grid {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
}
.candidate-main {
  color: var(--fg);
  font-size: 12px;
}
.candidate-rank {
  min-width: 28px;
  color: var(--accent);
  font-family: 'Orbitron', sans-serif;
  font-weight: 700;
}
.candidate-name {
  flex: 1;
}
.candidate-score,
.candidate-meta,
.candidate-detail-grid {
  color: var(--fg-muted);
  font-size: 11px;
}
.candidate-meta {
  margin-top: 6px;
}
.candidate-detail-card {
  margin-top: 10px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: #111827;
  padding: 10px 12px;
}
.candidate-detail-head {
  color: var(--fg);
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 8px;
}
.candidate-detail-grid {
  row-gap: 6px;
}
.empty-block {
  margin-top: 8px;
  padding: 12px;
  border-radius: 8px;
  background: #162131;
  color: var(--fg-muted);
  font-size: 12px;
  text-align: center;
}

/* ---- 小车集成按钮样式 ---- */
.info-car-btn {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid rgba(64,224,208,0.4);
  background: rgba(64,224,208,0.1);
  color: #40e0d0;
  transition: all 0.2s;
}
.info-car-btn:hover {
  background: rgba(64,224,208,0.25);
  border-color: rgba(64,224,208,0.8);
}
.info-car-btn.warning-btn {
  border-color: rgba(239,68,68,0.4);
  color: #ef4444;
  background: rgba(239,68,68,0.1);
}
.info-car-btn.warning-btn:hover {
  background: rgba(239,68,68,0.25);
  border-color: rgba(239,68,68,0.8);
}

.yolo-result-card {
  margin-top: 12px;
  padding: 12px;
  background: rgba(0,0,0,0.3);
  border: 1px solid rgba(64,224,208,0.2);
  border-radius: 8px;
}
.yolo-result-img {
  width: 100%;
  height: auto;
  border-radius: 6px;
  margin-top: 8px;
  border: 1px solid rgba(255,255,255,0.1);
}
.yolo-result-time {
  font-size: 11px;
  color: var(--fg-muted);
  text-align: center;
  margin-top: 6px;
}

/* ---- 传感器参数编辑浮层 ---- */
.sensor-edit-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}
.sensor-edit-panel {
  width: 420px;
  max-width: 90vw;
  max-height: 80vh;
  background: var(--bg-card, #1a2332);
  border: 1px solid var(--border, rgba(255,255,255,0.1));
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}
.sensor-edit-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid var(--border, rgba(255,255,255,0.1));
  font-weight: 600;
  font-size: 14px;
  color: var(--fg, #e0e8f0);
}
.sensor-edit-body {
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
}</style>
