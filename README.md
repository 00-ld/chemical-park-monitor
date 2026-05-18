# 化工园区智能监测系统

化工园区危险气体智能检测与溯源系统，集成**气体扩散模拟**、**泄漏源溯源**、**智能路径规划**、**YOLO 视觉检测**等多种算法，实现化工园区的全方位智能监测与安全预警。

---

## 技术栈

### 前端 — `Manage/`

| 技术 | 用途 |
|------|------|
| **Vue 3** + **TypeScript** + **Vite 5** | SPA 框架与构建工具 |
| **Element Plus** | UI 组件库 |
| **Pinia** | 状态管理 |
| **Vue Router** | 前端路由（hash 模式） |
| **ECharts** + **vue-echarts** | 数据可视化图表 |
| **SuperMap iClient** / **MapboxGL** / **MapLibreGL** | 地图可视化 |
| **Three.js** | 3D 场景渲染 |
| **Canvas 2D API** | 园区平面地图自渲染 |

### 后端 — `Back/`

| 技术 | 用途 |
|------|------|
| **Spring Boot 3.4** + **JDK 21** | RESTful API 框架 |
| **MyBatis** + **MySQL 8** | 数据持久层 |
| **JWT** (jjwt 0.11.5) | 身份认证 |
| **WebSocket** | 实时通信 |
| **Maven** | 构建管理 |

### Python 算法服务 — `python/`

| 技术 | 用途 |
|------|------|
| **FastAPI** + **Uvicorn** | 算法服务 HTTP 接口 |
| **PyTorch 2.10** + **Ultralytics YOLO11** | 深度学习与目标检测 |
| **SciPy** + **NumPy** | 科学计算 |
| **Matplotlib** | 数据可视化 |
| **Scikit-learn** | 机器学习 |

### 核心算法

| 算法 | 用途 | 位置 |
|------|------|------|
| **高斯烟羽模型** (Gaussian Plume) | 气体扩散浓度场模拟 | `python/diffusion/` |
| **物理信息神经网络** (PINN) | 泄漏源溯源与参数反演 | `python/inversion/` |
| **D-Star Lite** | 动态路径规划与避障 | `python/planning/` |
| **CFD 校准** | 计算流体力学模型验证 | `python/diffusion/cfd_calibrator.py` |
| **YOLO11** | 实时视觉目标检测 | `python/` (模型文件) |

---

## 目录结构

```
.
├── Back/                                # Spring Boot 后端
│   ├── src/main/java/com/at/
│   │   ├── ChemicalApplication.java     # 启动入口
│   │   ├── controller/                  # REST API 控制器层
│   │   │   ├── CarController.java       #   巡检小车 CRUD
│   │   │   ├── ImageAnalysisController.java  # YOLO 图像分析
│   │   │   ├── LoginAndRegisterController.java # 登录/注册
│   │   │   ├── RegisterController.java  # 注册（备用）
│   │   │   └── WarningHistoryController.java # 预警历史
│   │   ├── service/                     # 业务逻辑层
│   │   ├── mapper/                      # MyBatis 数据访问接口
│   │   ├── pojo/                        # 数据模型（POJO）
│   │   │   ├── Car.java                 #   小车实体
│   │   │   ├── Result.java              #   统一响应格式
│   │   │   ├── WarningHistory.java      #   预警历史记录
│   │   │   ├── login_register/          #   登录/注册 DTO
│   │   │   └── query/PageResult.java    #   分页结果
│   │   ├── interceptor/                 # JWT 拦截器
│   │   ├── exception/                   # 全局异常处理
│   │   │   └── GlobalExceptionHandler.java  # @RestControllerAdvice
│   │   └── utils/                       # 工具类
│   │       └── JwtUtils.java            #   JWT 生成与验证
│   ├── src/main/resources/
│   │   ├── mapper/                      # MyBatis XML 映射文件
│   │   └── application.yml              # 数据库/服务器配置
│   └── pom.xml                          # Maven 依赖
│
├── Manage/                              # Vue 3 前端管理面板
│   ├── src/
│   │   ├── api/                         # API 接口层
│   │   │   ├── algorithm.ts             #   算法服务 API（扩散/溯源/规划）
│   │   │   ├── algorithmClient.ts       #   算法服务 axios 实例
│   │   │   └── user/                    #   用户认证 API
│   │   ├── data/                        # 静态数据（前移的算法配置文件）
│   │   │   ├── parkAssets.js            #   园区设施/道路/传感器静态数据
│   │   │   ├── phase1Config.ts          #   气体配置与浓度查询
│   │   │   ├── gasSourceCatalog.js      #   气体源合法区域配置
│   │   │   ├── carPatrolRoutes.js       #   小车巡逻路径
│   │   │   └── coordinate.js            #   坐标系转换工具
│   │   ├── views/                       # 页面组件
│   │   │   ├── home/index.vue           #   首页仪表盘
│   │   │   ├── login/index.vue          #   登录页
│   │   │   ├── register/index.vue       #   注册页
│   │   │   ├── map_test/map_test.vue    #   智慧地图（核心页面）
│   │   │   ├── screen/index.vue         #   数字园区大屏
│   │   │   ├── Car/                     #   巡检小车管理
│   │   │   ├── YOLO/Home.vue            #   YOLO 实时监测
│   │   │   ├── thing/monitor_history/   #   实时预警监控
│   │   │   ├── acl/                     #   人员/权限管理
│   │   │   ├── emergency/index.vue      #   应急管理
│   │   │   └── 404/index.vue            #   404 页面
│   │   ├── store/                       # Pinia 状态管理
│   │   │   └── carStore.ts              #   小车数据仓库
│   │   ├── router/                      # Vue Router 路由配置
│   │   ├── layout/                      # 布局组件（导航栏/侧边栏）
│   │   ├── components/                  # 全局通用组件
│   │   ├── styles/                      # 全局样式
│   │   ├── utils/                       # 工具函数
│   │   └── assets/                      # 静态资源
│   ├── public/                          # 公共静态资源
│   ├── index.html                       # HTML 入口
│   ├── package.json                     # npm 依赖
│   └── vite.config.ts                   # Vite 构建配置
│
├── python/                              # Python 算法模块
│   ├── api_server.py                    # FastAPI 主服务入口
│   ├── response_utils.py                # 统一响应格式工具
│   ├── gasDiffusionAstar.py             # 气体扩散 + A* 路径规划（旧版）
│   ├── map.py                           # 园区地图模型
│   ├── diffusion/                       # 气体扩散模型
│   │   ├── phase1_diffusion.py          #   高斯烟羽扩散模拟
│   │   ├── diffusion_runner.py          #   扩散运行器
│   │   └── cfd_calibrator.py            #   CFD 校准器
│   ├── inversion/                       # 泄漏源反演（PINN）
│   │   ├── source_inversion.py          #   泄漏源反演主逻辑
│   │   ├── pinn_model.py                #   PINN 神经网络模型
│   │   ├── pinn_coarse_search.py        #   PINN 粗搜索
│   │   ├── pinn_dataset.py              #   PINN 数据集
│   │   ├── pinn_losses.py               #   PINN 损失函数
│   │   └── inversion_runner.py          #   反演运行器
│   ├── planning/                        # 路径规划
│   │   ├── evacuation_runner.py         #   疏散路径规划
│   │   └── dstar_lite.py                #   D* Lite 算法
│   ├── engine/                          # 算法引擎
│   │   ├── task_router.py               #   任务路由分发
│   │   └── entrypoint.py                #   算法入口
│   └── requirements.txt                 # Python 依赖
│
├── docs/                                # 项目文档
│   ├── architecture.md                  # 系统架构文档
│   ├── api-reference.md                 # API 接口文档
│   ├── coding-standards.md              # 编码规范
│   ├── development-guide.md             # 开发指南
│   └── changelog.md                     # 修改日志
│
├── img/                                 # 图片资源
├── pyproject.toml                       # Python 项目配置（ruff）
├── .gitignore                           # Git 忽略规则
└── README.md                            # 本文件
```

---

## 启动指南

### 前置要求

| 组件 | 版本 |
|------|------|
| JDK | >= 21 |
| Node.js | >= 18 |
| npm | >= 9 |
| Python | >= 3.11 |
| MySQL | >= 8.0 |
| Maven | >= 3.8 |

### 1. 数据库

确保 MySQL 运行在 `localhost:3306`，数据库 `chemical` 已创建。

默认配置见 `Back/src/main/resources/application.yml`：
- 用户名: `root`
- 密码: `123456`

### 2. Python 算法服务（端口 8000）

```bash
cd python

# 创建虚拟环境（首次）
python -m venv .venv
source .venv/bin/activate      # Linux/Mac
# .venv\Scripts\activate       # Windows

# 安装依赖（首次）
pip install -r requirements.txt

# 启动服务
python -m uvicorn api_server:app --host 127.0.0.1 --port 8000 --reload
```

验证：`curl http://localhost:8000/api/health` → `{"status":"ok"}`

### 3. Java 后端（端口 8081）

```bash
cd Back
mvn clean package -DskipTests   # 编译打包（首次或依赖变更后）
mvn spring-boot:run             # 启动服务
```

验证：`curl -X POST http://localhost:8081/api/user/login -H "Content-Type: application/json" -d '{"username":"admin","password":"123456"}'`

### 4. 前端（端口 5173）

```bash
cd Manage
npm install                      # 安装依赖（首次）
npm run dev                      # 启动开发服务器
```

访问：`http://localhost:5173`

> **注意**：前端通过 Vite 代理转发 `/api/*` → Java 后端 `:8081`，`/algorithm-api/*` → Python 算法 `:8000`。开发时三个服务都必须同时运行。

### 测试账号

| 用户名 | 密码 |
|--------|------|
| admin | 123456 |

---

## 本次改造与 Bug 修复

### Bug 修复

| 问题 | 原因 | 修复 |
|------|------|------|
| **智慧地图白屏** | `evacuationSummary` computed 在无规划时返回 `null`，模板直接访问 `.statusText` 报错 | 返回默认值而非 null |
| **算法 API 404** | `algorithm.ts` 请求 `/diffusion/simulate`，FastAPI 端点是 `/api/diffusion/simulate` | 所有路径添加 `/api/` 前缀 |
| **登录/注册 404** | `request.ts` baseURL 含 `/api`，API 枚举也以 `/api` 开头导致双重路径 | 去掉 API 枚举中的 `/api` 前缀 |
| **后端端口冲突** | 8080 端口被 WeChat Server Manager 占用 | 后端改为 8081 端口 |
| **小车数据加载失败** | `carStore.ts` 硬编码 `localhost:8080`，后端实际运行在 8081 | 改为 `localhost:8081` |
| **多个页面 API 调用失败** | `CarHome.vue`、`CarDetail.vue`、`YOLO/Home.vue`、`home/index.vue`、`monitor_history/index.vue` 硬编码 8080 | 全部改为 8081 |
| **`message` 与 `error` 字段不匹配** | Java `Result` 返回 `error` 字段，前端用 `message` 获取 | 改为 `res.error \|\| res.message \|\| '默认信息'` |

### 架构改进

| 改进 | 说明 |
|------|------|
| **移除前端算法代码** | 删除 `gas_zero_backend_system/` 目录（15 个 Python 文件 + 3 个 Worker + 9 个 JS 算法文件），前端不再包含算法逻辑 |
| **创建算法 API 层** | `src/api/algorithm.ts` + `algorithmClient.ts`，所有算法调用走 HTTP 接口 |
| **静态数据前移** | 园区资产、气体配置、坐标转换等静态数据移至 `src/data/`，通过 API 查询而非本地计算 |
| **统一响应格式** | Python 算法服务输出统一为 `{success, data, error, code}` 格式 |
| **Java 全局异常处理** | 创建 `GlobalExceptionHandler.java`（`@RestControllerAdvice`） |
| **端口标准化** | Java 后端 8081，Python 算法 8000，前端 5173 |

---

## License

MIT
