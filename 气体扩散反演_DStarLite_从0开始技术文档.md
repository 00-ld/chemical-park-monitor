# 气体扩散反演 + D* Lite 逃生路径规划系统技术文档

## 1. 文档目的

本文档用于指导 AI 从 0 开始重新搭建一套新的园区气体扩散反演与逃生路径规划系统，并最终集成到：

- `e:\xm\localhost\Manage\src\views\map_test\map_test.vue`

注意事项：

- 这是全新系统，不是在旧逻辑上打补丁。
- 允许复用现有页面中的园区底图、设施坐标、道路坐标、经纬度换算思路。
- 不允许继续沿用旧的扩散逻辑、旧的 A* 逻辑、旧的右侧统计逻辑作为核心实现。
- 算法和模型必须重新放到一个新的目录中，并且该目录内以 Python 实现。
- 尽量不引入传统后端服务，优先采用“前端 + Web Worker + Pyodide 执行 Python”的零后端方案。
- 一切以“可视化可展示、交互完整、动画顺畅、最终能在前端页面里演示”为最高优先级。

---

## 2. 总体目标

需要实现三大能力，并且三者可以组合使用：

1. 改进高斯烟羽扩散模拟 + CFD 校正
2. 基于多传感器监测数据的 PINN 气体溯源反演
3. 基于扩散危险场的 D* Lite 人群逃生路径规划

最终在 `map_test.vue` 中实现以下效果：

1. 用户可以点击按钮构建泄漏场景，选择泄漏点、气体类型、环境参数、气体参数。
2. 系统用改进高斯模型先模拟扩散，再叠加 CFD 校正，使扩散结果更接近真实情况。
3. 扩散结果以动画形式展示，支持播放、暂停、拖拽进度条、逐帧查看。
4. 传感器点位可以来自已有 RL 监控点，也可以手动添加。
5. PINN 溯源支持两种数据来源：
   - 来自扩散模型自动生成的传感器浓度时序
   - 用户手动录入的浓度与环境参数
6. PINN 溯源的可视化效果是“污染团逐步收缩并定位到泄漏源点”。
7. 扩散完成后，系统根据各时刻的有毒气体浓度判断道路是否可通行。
8. 所有带出入口的建筑物都要自动规划逃生路径，起点为建筑出入口，终点为园区出入口。
9. 路径规划必须严格沿道路网络进行，不能穿建筑、不能穿障碍、不能穿越超标危险区。
10. 页面支持选择某一个建筑物，查看该建筑物在当前时刻或当前帧下的逃生路径。
11. 扩散模型可以单独使用。
12. PINN 溯源模型可以单独使用。
13. 扩散模型可以和路径规划一起使用。
14. 扩散模型和溯源模型一起使用时，初始泄漏点和最终反演点应基本重合。
15. 每种气体都必须绑定其园区生产或存储区域，若用户输入的泄漏点不在允许范围附近，则提示无效。

---

## 3. 参考论文的落地原则

参考论文：

- `e:\xm\localhost\基于物理信息神经网络的实际气体状态方程预测模型_李起锋.pdf`
- `e:\xm\localhost\基于CFD验证的高斯烟羽模型参数修正及扩散特性研究_罗晋宇.pdf`

落地原则如下：

### 3.1 CFD 论文的使用方式

借鉴论文中的核心思想：

- 先用高斯烟羽模型快速生成扩散场
- 再利用 CFD 仿真结果对高斯模型参数进行修正
- 修正内容主要落在扩散宽度、主扩散方向、浓度衰减速度、障碍物遮挡影响上

工程化实现时，不要求在浏览器里实时做完整 CFD 求解，因为这会严重拖慢前端。

本系统采用：

- “改进高斯主模型 + 离线/参数化 CFD 修正器”的方案

即：

- 前端交互时实时运行的是改进高斯模型
- CFD 部分通过参数修正器、修正系数表、局部风场扰动模型来近似真实 CFD 结果
- 不做浏览器内 Navier-Stokes 全量求解

### 3.2 PINN 论文的使用方式

借鉴论文中的核心思想：

- 用物理信息神经网络将物理约束与数据观测共同纳入损失函数
- 使用物理方程约束神经网络输出，减少纯数据拟合的不稳定性

由于原论文更偏向物理约束建模思路，而本项目目标是“泄漏源反演”，因此本系统做如下扩展：

- 使用 PINN 思想来做“气体源位置 + 泄漏强度 + 局部扩散参数”的反问题求解
- 把传感器观测浓度、风速风向、时间序列、扩散 PDE 残差一起放进损失函数
- 最终输出源点估计和溯源收缩动画

结论：

- 本项目不是机械复刻论文内容
- 而是以两篇论文的建模思想为依据，做适用于园区可视化系统的工程化重构

---

## 4. 总体技术路线

系统采用“前端主导、Python 算法内嵌、零传统后端”的架构。

### 4.1 推荐架构

- 前端：Vue 3 + TypeScript
- 地图展示：沿用 `map_test.vue` 的 `canvas` 绘制方式
- Python 执行容器：Pyodide + Web Worker
- 数据交换：JSON
- 动画组织：前端统一时间轴控制
- 算法目录：新建独立目录，不污染旧代码

### 4.2 为什么用 Pyodide

用户要求：

- 算法和模型用 Python 重写
- 尽量不涉及后端

因此最佳折中方案是：

- 前端页面负责交互和可视化
- Python 模型在浏览器 Worker 中运行
- 主线程不阻塞
- 不需要单独起 Flask/FastAPI/Java 服务

### 4.3 核心数据流

1. 用户在页面上构建泄漏场景
2. 前端把场景参数发给 Python Worker
3. Python Worker 先运行改进高斯扩散，再做 CFD 校正
4. 输出每个时刻的扩散帧、浓度网格、传感器采样值
5. 若用户启动溯源，则使用传感器数据运行 PINN 反演
6. 输出源点估计、候选区域、收缩动画帧
7. 若用户启动逃生规划，则把每一帧浓度网格映射到道路图
8. D* Lite 根据危险变化做动态重规划
9. 前端统一渲染扩散层、溯源层、路径层和时间轴

---

## 5. 必须新建的目录结构

必须新建一个全新目录，建议直接放在 `Manage/src` 下，便于前端集成与构建：

```text
e:\xm\localhost\Manage\src\gas_zero_backend_system\
  README.md
  python\
    __init__.py
    config\
      gas_catalog.py
      national_thresholds.py
      park_assets.py
      visualization_config.py
    common\
      geometry.py
      coordinate.py
      interpolation.py
      serializers.py
    diffusion\
      gaussian_improved.py
      cfd_calibrator.py
      diffusion_field.py
      diffusion_runner.py
    sensors\
      sensor_layout.py
      sensor_sampler.py
      sensor_manual_input.py
    inversion\
      pinn_dataset.py
      pinn_model.py
      pinn_losses.py
      source_inversion.py
      inversion_runner.py
    planning\
      road_graph.py
      hazard_mapper.py
      dstar_lite.py
      evacuation_runner.py
    engine\
      entrypoint.py
      task_router.py
  worker\
    pyodideWorker.ts
    workerProtocol.ts
  composables\
    useGasSimulation.ts
    usePinnInversion.ts
    useEvacuationPlanner.ts
    useTimelinePlayer.ts
  store\
    gasSystemStore.ts
  types\
    gas-system.ts
  layers\
    diffusionLayer.ts
    inversionLayer.ts
    evacuationLayer.ts
    sensorLayer.ts
  mock\
    demoScenarios.ts
```

原则：

- 所有核心算法必须放在 `python` 目录下。
- `worker` 负责桥接前端和 Python。
- `layers` 负责画图，不包含算法。
- `composables` 负责页面状态和调用流程。
- 不要把算法直接写进 `map_test.vue`。
- `map_test.vue` 只做页面编排和交互入口。

---

## 6. 页面集成原则

最终仍然集成到：

- `e:\xm\localhost\Manage\src\views\map_test\map_test.vue`

但要求将其改造为“平台壳”，核心逻辑外置。

### 6.1 `map_test.vue` 只负责

- 顶层布局
- 左侧控制面板
- 中央地图画布
- 右侧结果面板
- 底部时间轴
- 顶部模式切换
- 调用 composables 和 worker

### 6.2 `map_test.vue` 不负责

- 不直接实现扩散公式
- 不直接实现 PINN 训练
- 不直接实现 D* Lite 算法
- 不直接维护复杂的浓度网格计算

---

## 7. 功能模块设计

## 7.1 模块 A：气体扩散模型

### 7.1.1 用户交互要求

页面上新增“气体扩散模型”控制区，包含：

- 按钮：`构建气体模型`
- 泄漏点选取方式：
  - 地图点击选点
  - 手动输入经纬度
- 气体类型选择
- 泄漏参数输入：
  - 泄漏速率
  - 泄漏持续时间
  - 初始温度
  - 初始压力
  - 泄漏高度
- 环境参数输入：
  - 风速
  - 风向
  - 温度
  - 湿度
  - 稳定度等级
  - 地表粗糙度
  - 障碍影响开关
- 按钮：`搭建模型`
- 按钮：`扩散模拟`

### 7.1.2 泄漏点合法性约束

每种气体必须绑定园区中的允许泄漏区域：

- 甲烷：甲烷储配库、甲烷相关管线附近
- 液氨：氨气储罐附近
- 硫化氢：硫化氢储罐、脱硫塔相关区域附近
- 一氧化碳：钢瓶库、相关工艺区附近
- 甲苯：溶剂储罐附近
- 其他气体：必须在其配置的生产/储存点附近

校验规则：

- 用户点击或输入的经纬度先转换到园区局部坐标
- 再计算与该气体允许泄漏点集合的最近距离
- 若距离大于配置阈值，例如 20m 到 50m，则直接提示：
  - `当前泄漏点不在该气体允许的生产/存储区域附近，输入无效`

### 7.1.3 改进高斯烟羽模型

基础采用二维近地扩散可视化模型，输出浓度场：

```text
C_gauss(x, y, t)
= Q_eff / (2 * pi * u * sigma_y * sigma_z)
  * exp(-(y_eff^2) / (2 * sigma_y^2))
  * exp(-(z_eff^2) / (2 * sigma_z^2))
  * F_time(t)
  * F_density(gas)
  * F_decay(env)
```

工程落地时改进项必须包含：

1. 风向平流
2. 时间相关扩散半径
3. 气体密度影响
4. 稳定度影响
5. 地表粗糙度影响
6. 建筑遮挡影响
7. 浓度衰减项

建议实现参数：

- `sigma_y = sigma_y_base * k_stability_y * k_terrain * k_cfd_y`
- `sigma_z = sigma_z_base * k_stability_z * k_terrain * k_cfd_z`
- `u_eff = u * k_building_wake * k_local_wind`
- `C_corrected = C_gauss * k_cfd_conc + b_cfd`

### 7.1.4 CFD 校正模块

注意：

- 这里不是做实时全 CFD 求解
- 而是做“CFD 结果驱动的参数修正器”

校正器要做三件事：

1. 校正扩散边界
2. 校正主扩散方向
3. 校正近障碍区域浓度

推荐实现：

- 用配置文件或离线样本表保存不同条件下的修正系数：
  - 风速
  - 风向
  - 稳定度
  - 气体种类
  - 周边建筑密度
- 运行时通过插值获得：
  - `k_cfd_y`
  - `k_cfd_z`
  - `k_cfd_conc`
  - `k_wake`

还可以增加一个局部扰动场：

```text
W_local(x, y) = W_global + W_building_block(x, y) + W_channel(x, y)
```

用于在塔器区、罐区、建筑群之间生成更真实的拉伸和偏转效果。

### 7.1.5 扩散输出结果

扩散模块必须输出：

- 每一帧的浓度网格 `concentrationGrid`
- 每一帧的等值面/等值线 `isopleths`
- 每一帧的扩散边界多边形
- 每一帧的最大浓度
- 每一帧的超标区域掩码
- 每一帧的传感器采样值

### 7.1.6 扩散可视化要求

地图上要显示：

- 泄漏源点
- 扩散云团
- 颜色深浅表示浓度高低
- 动画随时间扩散

表现形式建议：

- 低浓度：浅蓝/浅绿半透明
- 中浓度：橙色半透明
- 高浓度：红色高亮半透明

动画控制必须支持：

- 播放
- 暂停
- 上一帧
- 下一帧
- 拖动进度条
- 切换播放速度
- 循环播放

---

## 7.2 模块 B：RL 传感器监控点位

这里把页面上的监控点统一命名为“RL 传感器点位”，但本次重点是点位管理与数据采样，不强制实现强化学习训练。

### 7.2.1 初始状态

- 页面初始可以保留 25 个默认点位作为演示数据
- 但必须支持用户手动新增、删除、编辑点位
- 点位数量不能被写死

### 7.2.2 点位字段

每个传感器至少包含：

- `id`
- `name`
- `x`
- `y`
- `longitude`
- `latitude`
- `height`
- `gasType`
- `samplingRadius`
- `status`
- `dataSource`
- `manualData`
- `autoSampleSeries`

### 7.2.3 数据来源模式

每个传感器要支持两种模式：

1. 自动采样模式
   - 从扩散浓度场中读取该点位在每一帧的浓度
   - 自动生成时间序列数据
2. 手动输入模式
   - 用户手工填写浓度、温度、风速等参数
   - 可用于单独做 PINN 反演

### 7.2.4 页面要求

新增传感器管理面板，支持：

- 手动添加点位
- 地图点击添加
- 编辑点位参数
- 删除点位
- 批量清空
- 导入模拟数据
- 切换自动/手动数据源

---

## 7.3 模块 C：PINN 气体溯源模型

### 7.3.1 目标

根据多个传感器在多个时刻的浓度值以及环境参数，反演泄漏源的大致位置范围，并最终定位为一个点。

### 7.3.2 反演输入

PINN 输入必须支持：

- 传感器坐标
- 传感器高度
- 时间序列
- 浓度序列
- 风速
- 风向
- 温度
- 稳定度
- 气体类型
- 已知或待估计的泄漏强度范围

### 7.3.3 物理约束

采用二维时间相关对流扩散方程作为物理约束：

```text
∂C/∂t + u * ∂C/∂x + v * ∂C/∂y
- Dx * ∂²C/∂x² - Dy * ∂²C/∂y²
+ λ * C
= S(x, y, t)
```

其中：

- `C` 为浓度
- `u, v` 为风场分量
- `Dx, Dy` 为有效扩散系数
- `λ` 为衰减项
- `S` 为泄漏源项

### 7.3.4 PINN 损失函数

```text
L_total
= λ_obs * L_obs
+ λ_pde * L_pde
+ λ_bc  * L_bc
+ λ_ic  * L_ic
+ λ_src * L_src
+ λ_reg * L_reg
```

其中：

- `L_obs`：传感器观测误差
- `L_pde`：PDE 残差
- `L_bc`：边界条件损失
- `L_ic`：初始条件损失
- `L_src`：源点稀疏约束/位置约束
- `L_reg`：正则项

### 7.3.5 反演求解策略

为保证前端演示速度，必须采用“两阶段反演”：

#### 阶段 1：粗搜

- 在地图上生成候选源点网格
- 用传感器浓度误差先做快速评分
- 选出 top-k 候选区域

#### 阶段 2：PINN 精修

- 在 top-k 候选区域内启动 PINN
- 联合优化：
  - 源点位置 `(xs, ys)`
  - 泄漏强度 `Q`
  - 局部扩散参数
- 输出最终源点坐标和可信区域

这样做的原因：

- 直接全图 PINN 训练太慢
- 两阶段方案更适合零后端和前端展示

### 7.3.6 PINN 输出

必须输出：

- 最终反演源点
- 反演误差
- 候选区域范围
- 每轮迭代的收缩边界
- 反演动画帧

### 7.3.7 溯源动画要求

可视化效果要求：

- 初始是一团较大的候选污染区域
- 随着反演迭代逐步收缩
- 最终收缩为一个点
- 最终点位显示为“预测泄漏源”

### 7.3.8 扩散 + 反演联合校验

当启用“扩散 + PINN 联合模式”时，需要增加一致性校验：

- 初始泄漏点与 PINN 最终反演点距离要足够小
- 默认验收阈值建议：
  - `source_match_error <= 15m`

前端结果面板显示：

- `源点匹配误差`
- `是否匹配`

---

## 7.4 模块 D：D* Lite 逃生路径规划

### 7.4.1 目标

基于气体扩散结果，在每一个时刻判断哪些道路节点和边可通行，然后用 D* Lite 做动态重规划。

### 7.4.2 关键约束

必须满足：

1. 只能在园区道路网络上规划
2. 建筑物不可穿越
3. 固定障碍物不可穿越
4. 浓度超标区域不可穿越
5. 从建筑出入口出发，到园区出入口结束

### 7.4.3 为什么用 D* Lite

因为危险区会随着扩散帧动态变化，路径需要反复重规划。

D* Lite 适合：

- 图上已有初始路径
- 代价随时间改变
- 只更新局部受影响节点和边
- 比每一帧重新全量跑普通 A* 更适合动态场景

### 7.4.4 路网建模

必须从当前园区道路中提取道路中心线图：

- 节点：道路交叉口、道路端点、建筑出入口接入点、园区出入口
- 边：道路段

每条边保存：

- `edgeId`
- `fromNode`
- `toNode`
- `length`
- `roadType`
- `baseCost`
- `blocked`
- `hazardScore`

### 7.4.5 危险区映射到路网

对于每一帧扩散结果：

- 先得到浓度网格
- 再将道路边按固定采样点离散化
- 若边上任一点浓度超过阻断阈值，则该边标记为不可通行
- 若节点浓度超过阻断阈值，则该节点不可通行

### 7.4.6 阻断阈值

必须配置两类阈值：

1. 预警阈值
2. 逃生阻断阈值

逃生阻断阈值定义为：

- `blocked_threshold = max(国家标准阻断阈值, 气体逃生阻断阈值配置)`

如果没有明确国家标准分级值，则至少提供可配置字段：

- `warningThreshold`
- `dangerThreshold`
- `blockingThreshold`

### 7.4.7 D* Lite 核心实现要求

必须真正实现 D* Lite，而不是把 A* 换个名字。

至少包含：

- `g`
- `rhs`
- `priority queue U`
- `km`
- `update_vertex`
- `compute_shortest_path`
- `replan_when_cost_changed`

建议键值函数：

```text
key(s) = [
  min(g(s), rhs(s)) + h(start, s) + km,
  min(g(s), rhs(s))
]
```

### 7.4.8 路径规划对象

需要对所有有出入口的建筑进行规划：

- 行政办公楼
- 研发中心
- 食堂
- 消防站
- 各生产车间
- 公用工程建筑
- 仓储建筑
- 污水处理建筑

每个建筑至少一个出入口作为起点。

目标终点为园区出入口集合：

- 西侧主入口
- 北侧行政入口
- 东侧物流入口
- 南侧工程入口

### 7.4.9 路径输出

系统要输出：

- 每个建筑的最优逃生路径
- 路径长度
- 目标园区出口
- 安全性状态
- 对应时间帧

### 7.4.10 页面要求

新增路径规划控制区：

- 按钮：`生成逃生路径`
- 建筑选择框
- 时间帧选择或绑定到全局时间轴
- 是否显示全部建筑路径
- 是否只显示当前建筑路径

用户选择某个建筑时：

- 地图高亮该建筑出入口
- 只显示该建筑当前最优路径

### 7.4.11 路径动画要求

路径层必须支持：

- 静态路径显示
- 随时间切换的动态重规划显示
- 拖拽时间轴时同步刷新路径

可选增强：

- 在路径上显示移动箭头
- 显示“当前已阻断路段”

---

## 8. 四类核心可视化图层

页面最终至少包含四个图层：

1. 底图图层
2. 扩散图层
3. 传感器图层
4. 路径图层

若启用反演，则再叠加：

5. 溯源图层

### 8.1 扩散图层

- 浓度热力色块
- 等值线
- 扩散边界

### 8.2 传感器图层

- 传感器圆点
- 探测半径
- 传感器标签
- 当前帧浓度 tooltip

### 8.3 溯源图层

- 候选源区域
- 收缩动画
- 最终源点

### 8.4 路径图层

- 建筑路径线
- 起点与终点标记
- 阻断路段高亮

### 8.5 时间轴联动

扩散、溯源、路径三个模块都要挂在统一时间轴上。

统一规则：

- 扩散帧切换时，路径和传感器采样同步切换
- 若当前启用了反演动画，则允许单独回放反演序列
- 需要支持“扩散时间轴”和“PINN 训练迭代轴”两种模式切换

---

## 9. 前端页面布局改造要求

建议把 `map_test.vue` 分成五个区域：

1. 顶部模式栏
2. 左侧参数面板
3. 中央地图画布
4. 右侧结果面板
5. 底部时间轴和播放条

### 9.1 顶部模式栏

包含按钮：

- `扩散模型`
- `PINN溯源`
- `逃生路径`
- `联合模式`

### 9.2 左侧参数面板

按 Tab 分为：

- 泄漏参数
- 环境参数
- 传感器管理
- 反演参数
- 路径规划参数

### 9.3 右侧结果面板

显示：

- 当前气体信息
- 当前帧最大浓度
- 超标面积
- 传感器数
- PINN 反演点
- 源点误差
- 当前建筑路径长度
- 当前路径是否安全

### 9.4 底部时间轴

必须包含：

- 播放
- 暂停
- 停止
- 拖动帧
- 当前时间
- 总时长

---

## 10. 数据结构定义

## 10.1 气体配置

```ts
type GasConfig = {
  gasId: string
  name: string
  color: string
  molecularWeight: number
  densityRatio: number
  diffusionCoefficient: number
  warningThreshold: number
  dangerThreshold: number
  blockingThreshold: number
  allowedSourceFacilityIds: string[]
  validRadiusMeters: number
}
```

## 10.2 泄漏场景

```ts
type LeakScenario = {
  sourceId: string
  gasId: string
  mapPoint: { x: number; y: number }
  geoPoint: { longitude: number; latitude: number }
  sourceRate: number
  releaseDuration: number
  releaseHeight: number
  temperature: number
  pressure: number
  windSpeed: number
  windDirection: number
  humidity: number
  stabilityClass: number
  terrainRoughness: number
}
```

## 10.3 扩散帧

```ts
type DiffusionFrame = {
  frameIndex: number
  timeSec: number
  concentrationGrid: number[][]
  isoPolygons: Array<Array<[number, number]>>
  blockedMask: boolean[][]
  maxConcentration: number
  affectedArea: number
}
```

## 10.4 传感器

```ts
type SensorPoint = {
  id: string
  name: string
  x: number
  y: number
  mode: 'auto' | 'manual'
  gasId: string
  manualSeries?: Array<{ timeSec: number; concentration: number }>
  sampledSeries?: Array<{ timeSec: number; concentration: number }>
}
```

## 10.5 反演结果

```ts
type InversionResult = {
  estimatedSource: { x: number; y: number }
  confidenceRadius: number
  lossHistory: number[]
  shrinkFrames: Array<Array<[number, number]>>
  sourceMatchError?: number
}
```

## 10.6 路径结果

```ts
type EvacuationRoute = {
  buildingId: string
  buildingName: string
  startEntrance: [number, number]
  targetExit: [number, number]
  path: Array<[number, number]>
  distance: number
  status: 'success' | 'blocked'
  riskScore: number
  frameIndex: number
}
```

---

## 11. Python Worker 接口设计

前端和 Python Worker 的协议必须清晰，统一走消息通信。

## 11.1 必须提供的方法

### 11.1.1 构建扩散场景

```text
build_diffusion_scenario(payload) -> scenarioMeta
```

### 11.1.2 生成扩散帧

```text
run_diffusion_simulation(payload) -> {
  frames,
  sensorSeries,
  stats
}
```

### 11.1.3 运行 PINN 反演

```text
run_pinn_inversion(payload) -> {
  estimatedSource,
  shrinkFrames,
  lossHistory,
  errorMetrics
}
```

### 11.1.4 生成逃生路径

```text
run_evacuation_planning(payload) -> {
  routesByBuilding,
  dynamicRoutes,
  blockedRoadStats
}
```

### 11.1.5 统一联合求解

```text
run_joint_pipeline(payload) -> {
  diffusion,
  inversion,
  evacuation
}
```

---

## 12. 重点实现细节

## 12.1 坐标系统

建议使用双坐标：

- 页面计算坐标：`x, y`
- 页面显示坐标：`longitude, latitude`

原则：

- 所有算法都在局部平面坐标系中计算
- 经纬度只用于输入输出和界面展示

### 12.2 地图设施数据

允许复用 `map_test.vue` 现有数据源中的：

- `facilities`
- `roads`
- `buildingEntrances`
- `parkEntrances`
- `worldToGeo()`

但必须把这些数据迁移到新的配置文件中统一管理，不要继续散落在页面内。

### 12.3 扩散网格分辨率

建议：

- 园区计算网格分辨率：`100 x 65` 或 `120 x 80`

可视化时：

- 网格计算结果再映射成更细的渲染插值层

### 12.4 性能策略

必须优先保证可展示：

1. Python 计算放进 Worker
2. 大计算分帧执行
3. PINN 训练限制 epoch
4. 扩散帧默认不超过 120 帧
5. 拖动时间轴时优先使用缓存帧

### 12.5 缓存策略

以下结果必须缓存：

- 扩散帧缓存
- 传感器自动采样缓存
- PINN 反演结果缓存
- 路径规划结果缓存

缓存 key 由以下信息组成：

- 泄漏点
- 气体类型
- 环境参数
- 传感器配置
- 路径规划模式

---

## 13. 开发优先级

## P0：必须先完成

1. 新目录与 Worker 架构搭好
2. `map_test.vue` 改造成新系统入口
3. 改进高斯扩散动画可跑通
4. 时间轴联动可用
5. 泄漏点合法性校验可用

## P1：第二阶段

1. CFD 修正器接入
2. 传感器自动采样
3. 手动添加/编辑传感器
4. 扩散结果统计面板

## P2：第三阶段

1. PINN 两阶段反演
2. 溯源收缩动画
3. 扩散 + 反演联合误差显示

## P3：第四阶段

1. D* Lite 动态路径规划
2. 全建筑路径生成
3. 建筑选择框与路径高亮
4. 路径随帧联动

## P4：收尾优化

1. UI 细节优化
2. 播放性能优化
3. 默认演示场景
4. 错误提示和空状态

---

## 14. 验收标准

以下全部满足才算完成：

### 14.1 扩散模型

- 能选择泄漏点
- 能选择气体
- 能输入环境参数
- 能生成按时间推进的扩散动画
- 能显示浓度深浅
- 能做泄漏点合法性校验
- 能体现 CFD 校正效果

### 14.2 传感器与反演

- 能保留默认传感器
- 能手动添加传感器
- 能在自动模式下采样扩散场数据
- 能在手动模式下输入数据
- 能运行 PINN 反演
- 能显示收缩动画
- 能显示最终反演点

### 14.3 路径规划

- 能对所有有出入口建筑进行规划
- 路径必须沿道路
- 遇建筑和障碍绕开
- 遇浓度超标区域绕开
- 某建筑无安全路径时明确显示阻断
- 能按建筑选择显示对应路径

### 14.4 联合模式

- 扩散、反演、路径可以单独运行
- 扩散 + 反演能联合运行
- 扩散 + 路径能联合运行
- 联合模式下初始泄漏点与反演点误差小
- 时间轴能统一控制三类结果

---

## 15. 对 AI 编码的硬性要求

后续让 AI 写代码时，必须遵守以下要求：

1. 从 0 新建 `gas_zero_backend_system` 目录，不要继续在旧逻辑上修补。
2. 算法必须用 Python 写在新目录中。
3. 前端通过 Web Worker + Pyodide 调用 Python，不新增传统后端接口。
4. `map_test.vue` 只做页面集成，不写复杂算法。
5. 扩散模型必须是“改进高斯 + CFD 参数校正”。
6. PINN 必须是“粗搜 + PINN 精修”的两阶段方案。
7. 路径规划必须是真正的 D* Lite，而不是简单 A*。
8. 路径必须严格限制在道路网络上。
9. 每种气体必须校验泄漏点是否在对应设施附近。
10. 页面必须提供动画播放和时间轴拖动。
11. 可视化优先，先保证演示效果，再做参数精细化。

---

## 16. 最终交付物清单

最终 AI 生成代码后，应至少包含以下交付物：

1. 新建目录 `Manage/src/gas_zero_backend_system/`
2. Python 扩散模型代码
3. Python CFD 校正代码
4. Python PINN 反演代码
5. Python D* Lite 代码
6. Pyodide Worker 桥接代码
7. `map_test.vue` 改造后的页面
8. 扩散图层、溯源图层、路径图层
9. 默认演示场景
10. 可直接运行的前端可视化结果

---

## 17. 一句话实现目标

要做的是一套“从 0 开始的新系统”：

- 用改进高斯模型做园区气体扩散
- 用 CFD 校正让扩散更接近真实
- 用 RL 传感器点位采样浓度
- 用 PINN 做气体泄漏源反演
- 用 D* Lite 在危险动态变化下做建筑到园区出口的逃生路径规划
- 最终全部集成到 `map_test.vue` 中，以前端动画可视化为第一优先级完成展示

