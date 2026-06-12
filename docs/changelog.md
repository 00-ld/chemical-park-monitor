# 化工园区智能监测系统 — 开发改造总结

## 一、项目概述

化工园区智能安防监测系统，集成环境监控、分级预警、泄漏溯源、三维可视化、智能小车调度五大联动模块。前后端分离架构：Vue3 前端 + Spring Boot 后端 + Python FastAPI 算法服务。

---

## 二、代码规范化改造

### 2.1 Python 算法代码规范化（21 个文件）

| 操作 | 详情 |
|------|------|
| 修复编码 | `requirements.txt` 字符间距错乱问题 |
| Google docstring | 所有模块添加模块级和函数级 Google 风格文档注释 |
| 导入排序 | 标准库 → 第三方库 → 本地模块，每组按字母序 |
| 类型注解 | 补全所有函数参数和返回值类型注解 |
| 修复 Bug | `task_router.py` 相对导入 `from ..diffusion` → `from diffusion` |

### 2.2 Python API 统一响应格式

- 创建 `algorithm/response_utils.py`：`success_response()` / `error_response()`
- 统一格式：`{"success": bool, "data": ... | null, "error": str | null, "code": int}`
- 全局异常处理器 `@app.exception_handler(Exception)`
- 涉及：`api_server.py`、`engine/task_router.py`

### 2.3 Java 后端规范化（backend/）

| 操作 | 详情 |
|------|------|
| 响应统一 | 所有 Controller 改用 `ResponseEntity<Result<T>>`，增强 `Result.java` |
| 全局异常 | 创建 `GlobalExceptionHandler.java`（`@RestControllerAdvice`） |
| 参数校验 | 添加 `@Valid` / `@NotBlank` 注解 + `spring-boot-starter-validation` |
| 日志 | 所有 Controller/Service 添加 `@Slf4j` + `log.info/warn/error` |
| 清理 | 删除 22 个 JVM 崩溃日志文件（`hs_err_pid*`、`replay_pid*`） |
| 端口变更 | 8080 → 8081（被 WeChat Server Manager 占用） |

### 2.4 Vue3 前端规范化（frontend/src/）

| 操作 | 详情 |
|------|------|
| 组件规范 | 修复 4 个文件缺失 `lang="ts"`，合并双 `<script>` 为 `defineOptions` |
| 类型安全 | 消除 `: any`，新增 `CarItem`、`DetectionLog` 等接口定义 |
| UI 改进 | `alert()` → `ElMessage` 全局替换 |
| 死代码 | 删除孤立路由、空函数、注释代码 |
| 清理 | 删除 `__pycache__`、空目录 |

### 2.5 移除前端嵌入式算法代码

**核心改造：前端不再含有算法逻辑，全部通过 API 调用后端 Python 服务。**

| 删除内容 | 文件数 | 说明 |
|----------|--------|------|
| Python 代码副本 | 15 | `gas_zero_backend_system/algorithm/` |
| Pyodide Worker | 3 | 浏览器内运行 Python 的 Worker |
| JS 算法实现 | 9 | diffusion, pinn, evacuation 等 |
| 类型声明 | 1 | `*.py?raw` 声明 |

**新增内容：**

| 文件 | 说明 |
|------|------|
| `src/api/algorithm.ts` | 算法 API 函数（扩散、溯源、规划、引擎） |
| `src/api/algorithmClient.ts` | 独立 axios 实例，指向 Python 算法服务器 |
| `src/data/phase1Config.ts` | 气体配置常量 + 浓度查询工具函数 |
| `src/data/parkAssets.js` | 园区资产静态数据（从旧目录迁移） |
| `src/data/coordinate.js` | 坐标转换工具 |
| `src/data/gasSourceCatalog.js` | 气体源配置数据 |
| `src/data/carPatrolRoutes.js` | 小车巡逻路径数据 |

**配置更新：**

| 文件 | 变更 |
|------|------|
| `vite.config.ts` | 新增 `/algorithm-api` 代理到 `localhost:8000` |
| `.env.development` | 新增 `VITE_ALGORITHM_BASE_API/SERVE`，`VITE_SERVE` 改为 8081 |
| `.env.production` | 同上 |

### 2.6 项目配置文档

| 文件 | 说明 |
|------|------|
| `README.md` | 项目简介、技术栈、目录结构、启动指南 |
| `.gitignore` | 排除 target, dist, node_modules, venv, log 等 |
| `pyproject.toml` | ruff 格式/检查配置 |

---

## 三、Bug 修复

### 3.1 登录/注册双重 `/api` 路径

```
问题: request.ts baseURL = /api,  API路径 = /api/user/login
结果: 实际请求 /api/api/user/login → 404
修复: 去掉 API 枚举中的 /api 前缀
```

### 3.2 后端端口冲突

```
问题: 端口 8080 被 WeServerManager.exe (微信服务) 占用
结果: 后端新代码未生效，旧代码返回错误响应
修复: 后端改为 8081 端口
```

### 3.3 `message` 与 `error` 字段不匹配

```
问题: Java Result 返回 error 字段，前端用 message 获取
修复: 改为 res.error || res.message || '默认错误信息'
```

---

## 四、规范文档

| 文档 | 路径 | 内容 |
|------|------|------|
| 系统架构 | `docs/architecture.md` | 整体架构图、五大模块、算法说明、数据流转 |
| API 接口 | `docs/api-reference.md` | 全部 API 端点、请求/响应格式、状态码 |
| 编码规范 | `docs/coding-standards.md` | Google 风格、Vue3/Java/Python 各自规范 |
| 开发指南 | `docs/development-guide.md` | 环境要求、启动步骤、开发工作流、Git 规范 |
| 本改造总结 | `docs/changelog.md` | 本次所有改造内容 |

---

## 六、第二次修复（扩散动画 & 算法服务）

### 6.1 扩散模拟与 PINN 算法修复

| 问题 | 原因 | 修复 |
|------|------|------|
| **扩散模拟失败** | `phase1_diffusion.py` 缺少 `clamp` 导入 | 添加 `from diffusion.cfd_calibrator import clamp` |
| **FastAPI 启动失败** | FastAPI 0.115.0 与 starlette 0.36.3 不兼容 | 降级至 FastAPI 0.109.2 |
| **扩散无动画** | 前端 payload 字段名与后端不匹配（8 处） | 统一字段名：`sourcePoint→sourceMapPoint`, `windAngle→windDirection`, `stability→stabilityClass` 等 |
| **Python 缓存导致旧代码运行** | `__pycache__` 缓存未编译的 `.pyc` | 清除所有 `__pycache__` 目录 |
| **端口 8000 被旧进程占用** | 旧 Python 进程顽固占用 | 用 PowerShell `Stop-Process -Force` 强杀后重启 |

### 6.2 其他修复

| 问题 | 修复 |
|------|------|
| **`evacuationSummary` 空值报错** | computed 在无规划路线时返回默认值对象而非 `null` |
| **后端端口 8080→8081 未同步** | 7 个前端文件硬编码 `localhost:8080` 全部修复 |
| **算法 API 路径缺少 `/api/`** | `algorithm.ts` 路径添加 `/api/` 前缀 |

---

## 七、服务启动配置

### 启动命令

### 启动命令

```bash
# 1. Python 算法服务（端口 8000）
cd algorithm
python -m uvicorn api_server:app --host 127.0.0.1 --port 8000 --reload

# 2. Java 后端（端口 8081）
cd backend
mvn spring-boot:run

# 3. 前端（端口 5173）
cd frontend
npm run dev
```

### 访问地址

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:5173 |
| Python API 文档 | http://localhost:8000/docs |
| Java 后端 | http://localhost:8081 |

### 测试账号

| 用户名 | 密码 |
|--------|------|
| admin | 123456 |

### 端口对照

| 服务 | 端口 | 说明 |
|------|------|------|
| Java 后端 | 8081 | 原 8080 被微信服务占用 |
| Python 算法 | 8000 | FastAPI 算法服务 |
| 前端开发 | 5173 | Vite 开发服务器 |
