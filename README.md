# 化工园区危险气体扩散与溯源系统

本项目围绕化工园区危险气体扩散模拟、泄漏源溯源、传感器监控点位、小车巡检、逃生路径规划和 SuperMap iPortal 数字大屏展示构建。

当前仓库已按规范目录组织：前端在 `frontend/`，Java 后端在 `backend/`，Python 算法服务在 `algorithm/`，三维数字孪生接入在 `twin/` 与前端三维页面中维护，数据库台账在 `db/`，部署配置在 `deploy/`。

## 核心能力

- 气体扩散模拟：高斯烟羽、烟团、风速风向、稳定度、气体物性参数。
- 泄漏源溯源：基于多点浓度数据进行候选泄漏点估计。
- 逃生路径规划：结合危险浓度区域和道路拓扑进行动态路径规划。
- 传感器点位：固定气体传感器和阿克曼巡检小车作为静态/动态监控点位。
- 视觉识别：YOLO11m 用于识别小车摄像头上传图像中的人员位置。
- 三维展示：优先接入 SuperMap iPortal 已建设数字大屏，后续可扩展 Three.js 或 SuperMap 三维能力。

## 技术栈

| 模块 | 目录 | 技术 |
| --- | --- | --- |
| 前端 | `frontend/` | Vue 3、TypeScript、Vite、Element Plus、Pinia、ECharts、Canvas |
| 后端 | `backend/` | Spring Boot 3.4、JDK 21、MyBatis、MySQL、JWT |
| 算法服务 | `algorithm/` | FastAPI、NumPy、SciPy、PyTorch、Ultralytics YOLO11 |
| 三维/数字孪生 | `twin/`、`frontend/src/views/screen/` | SuperMap iPortal 数字大屏优先，Three.js/SuperMap 原生能力预留 |
| 数据库 | `db/`、`deploy/mysql/` | MySQL 8、utf8mb4 |
| 部署 | `deploy/` | Docker Compose、Nginx、MySQL、前后端服务 |

## 技术路线

系统技术路线按“数据采集 -> 扩散模拟 -> 异常识别 -> 泄漏源溯源 -> 逃生路径规划 -> 二维/三维展示 -> 安全联动”组织：

1. 固定气体传感器和阿克曼巡检小车采集 CO、O2、NH3、CH4 浓度数据。
2. Python 算法服务基于扩散模型生成浓度场，并通过测试集和校准流程验证模型行为。
3. Java 后端统一接收传感器、小车、算法任务和用户管理数据，按统一 JSON 响应协议对外提供接口。
4. 前端用 ECharts 展示统计趋势，用 Canvas 展示二维浓度分布、监控点位和 D* Lite 逃生路线。
5. 三维展示阶段优先嵌入已有 SuperMap iPortal 数字大屏，后续再扩展 Three.js/SuperMap 原生三维场景。
6. 事故处置建议、逃生规范建议等大模型能力只作为辅助参考，不替代扩散模型、溯源模型和现场负责人决策。

## 目录说明

```text
.
  frontend/          Vue 3 前端管理系统
  backend/           Java Spring Boot 后端
  algorithm/         Python 算法服务与扩散/溯源/路径规划算法
  twin/              SuperMap iPortal、Three.js 和三维坐标映射资料
  db/                数据库目录台账、脚本索引和维护规则
  datasets/          权威数据集来源、清单和小型可复现实验样本
  models/            模型清单、版本说明和轻量配置，不提交大模型权重
  docs/              项目总体要求、接口文档、数据集来源、架构说明
  tests/             气体模型可复现测试数据与验证脚本
  tools/             审计、校验、数据整理等辅助工具脚本
  scripts/           开发、构建、数据处理和发布辅助脚本
  docker/            共享容器构建资料
  deploy/            Docker Compose、Nginx、MySQL 初始化和服务器部署配置
  config/            配置模板，不存放真实密钥
  uploads/           本地上传占位目录，真实上传文件不提交
  logs/              本地日志占位目录，真实运行日志不提交
  assets/            项目图片、图标、地图和轻量三维静态资源
  .github/           CI、检查规则和 GitHub 仓库配置
```

## 统一接口协议

Java 后端和 Python 算法服务应返回统一 JSON 外壳：

```json
{
  "code": 200,
  "message": "成功",
  "data": {},
  "ok": true,
  "timestamp": 1781234567890,
  "requestId": "uuid"
}
```

Python 算法服务暂时保留 `success` 和 `error` 字段兼容旧前端调用。详细说明见 [docs/api-reference.md](docs/api-reference.md)。

## 环境变量与安全

真实密钥不得提交到 GitHub。以下内容必须通过环境变量、部署平台密钥或本地未提交 `.env` 注入：

- `MYSQL_ROOT_PASSWORD`
- `SPRING_DATASOURCE_PASSWORD`
- `JWT_SECRET`
- `ALGORITHM_API_KEY`
- 第三方 API Key

部署变量模板见 [deploy/.env.example](deploy/.env.example)。模板中的占位值不能用于生产环境。

## 本地开发

### 1. 数据库

开发和部署 SQL 入口见：

- [db/manifest.json](db/manifest.json)
- [deploy/mysql/init.sql](deploy/mysql/init.sql)

数据库使用 MySQL 8，字符集统一为 `utf8mb4`。不要在 SQL 或文档中写入真实数据库密码。

### 2. Java 后端

```bash
cd backend
mvn clean package -DskipTests
mvn spring-boot:run
```

后端数据库密码从环境变量读取。启动前请配置本地数据库连接和 `JWT_SECRET`。

### 3. Python 算法服务

```bash
cd algorithm
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn api_server:app --host 127.0.0.1 --port 8000 --reload
```

生产环境应配置 `ALGORITHM_API_KEY` 和 `ALGORITHM_REQUIRE_AUTH=true`。

### 4. 前端

```bash
cd frontend
npm install
npm run dev
```

SuperMap iPortal 数字大屏地址通过 `VITE_IPORTAL_DASHBOARD_URL` 配置。

## 服务器部署

生产部署目标域名为 `www.cip.lab6119.xyz`，部署入口在 `deploy/`。推荐使用 Docker Compose 统一运行 Nginx、Java 后端、Python 算法服务和 MySQL。

### 1. 服务器准备

推荐环境：

| 项 | 建议 |
| --- | --- |
| 操作系统 | Ubuntu 22.04 / Debian 12 |
| 配置 | 2 核 4 GB 起步，40 GB 磁盘起步 |
| 运行环境 | Docker、Docker Compose |
| 开放端口 | `80`、`443`、`22` |
| 域名 | `www.cip.lab6119.xyz` 解析到服务器公网 IP |

安装 Docker：

```bash
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker
docker --version
docker compose version
```

MySQL、Java 后端和 Python 算法服务不应直接暴露公网，应由 Nginx 统一代理。

### 2. 获取代码

在服务器上拉取代码：

```bash
cd /opt
git clone https://github.com/00-ld/chemical-park-monitor.git chemical-park
cd /opt/chemical-park
```

如果服务器上已经存在项目：

```bash
cd /opt/chemical-park
git pull origin main
```

### 3. 配置生产环境变量

真实密钥只允许保存在服务器本地 `.env` 文件中，不得提交到 GitHub：

```bash
cd /opt/chemical-park/deploy
cp .env.example .env
nano .env
```

至少需要替换以下变量：

```env
MYSQL_ROOT_PASSWORD=replace_with_strong_mysql_root_password
JWT_SECRET=replace_with_random_32_char_min_secret
ALGORITHM_API_KEY=replace_with_random_algorithm_key
CORS_ALLOWED_ORIGINS=http://www.cip.lab6119.xyz,https://www.cip.lab6119.xyz
ALGORITHM_CORS_ORIGINS=http://www.cip.lab6119.xyz,https://www.cip.lab6119.xyz
```

如果后续部署 YOLO/人员识别独立服务，再配置：

```env
ANALYSIS_SERVICE_URL=http://analysis-service:8100
```

### 4. 构建前端和后端

在服务器或本地构建均可。服务器构建示例：

```bash
cd /opt/chemical-park/frontend
npm install
npm run build:pro

cd ../backend
mvn clean package -DskipTests
cp target/chemical-backend-1.0.0.jar ../deploy/backend/chemical-backend-1.0.0.jar
```

构建完成后应存在：

```text
frontend/dist/
deploy/backend/chemical-backend-1.0.0.jar
```

这些构建产物用于服务器运行，但不要提交到 GitHub。

### 5. 启动 Docker 服务

```bash
cd /opt/chemical-park/deploy
docker compose --env-file .env config
docker compose --env-file .env up -d --build
docker compose ps
```

查看日志：

```bash
docker compose logs -f nginx
docker compose logs -f backend
docker compose logs -f algorithm
docker compose logs -f mysql
```

### 6. 验证访问

服务器本机验证：

```bash
curl http://127.0.0.1/
curl http://127.0.0.1/algorithm-api/api/health
```

域名验证：

```bash
curl http://www.cip.lab6119.xyz/
curl http://www.cip.lab6119.xyz/algorithm-api/api/health
```

浏览器访问：

```text
http://www.cip.lab6119.xyz
```

如果 SuperMap iPortal 数字大屏无法加载，检查 `frontend/.env.production` 中的 `VITE_IPORTAL_DASHBOARD_URL`，并确认 iPortal 服务、Nginx 代理和浏览器 iframe 策略允许访问。

### 7. HTTPS 建议

生产环境建议启用 HTTPS：

1. 确认 `www.cip.lab6119.xyz` 已解析到服务器公网 IP。
2. 使用 Certbot、云厂商证书或反向代理平台申请 TLS 证书。
3. 在 `deploy/nginx/default.conf` 中增加 443 配置。
4. HTTPS 验证正常后，再考虑启用 HSTS。

### 8. 更新与回滚

更新到最新版：

```bash
cd /opt/chemical-park
git pull origin main

cd frontend
npm install
npm run build:pro

cd ../backend
mvn clean package -DskipTests
cp target/chemical-backend-1.0.0.jar ../deploy/backend/chemical-backend-1.0.0.jar

cd ../deploy
docker compose --env-file .env up -d --build
```

回滚到指定提交：

```bash
cd /opt/chemical-park
git log --oneline
git checkout <commit>
```

回滚后重新构建并启动 Docker 服务即可。

### 9. 部署禁止事项

- 不要把真实 `.env`、数据库密码、JWT 密钥、算法 API Key、证书私钥提交到 GitHub。
- 不要提交 `frontend/dist/`、`backend/target/`、`.venv/`、`node_modules/`、`__pycache__/`、`.npy`、模型权重或生产数据库备份。
- 不要在前端代码中写死生产密钥、数据库连接、服务器绝对路径或第三方 API Key。
- 不要让 MySQL、算法服务、模型推理服务直接暴露到公网。

详细部署路线见 [docs/technical-route-to-deployment.md](docs/technical-route-to-deployment.md) 和 [deploy/README.md](deploy/README.md)。

## 测试与验证

常用验证命令：

```bash
cd backend
mvn -q -DskipTests compile

cd ../frontend
npm.cmd exec tsc -- -p tsconfig.json --noEmit --pretty false

cd ../algorithm
python -m diffusion.test_physical_invariants
python -m diffusion.test_improved_formula
python -m diffusion.test_gaussian_validation

cd ..
python tools/audit_repository.py
python tests/test_forward_model.py
```

`tests/` 当前数据是合成解析数据，用于回归验证，不得写成现场实测数据。真实/权威数据来源台账见 [docs/dataset-sources.md](docs/dataset-sources.md)。

## 代码硬性规则

死规则：严禁为了图方便写入无效、重复、无意义或无法验证的代码、变量、函数、接口、文档和数据文件。任何新增内容都必须能说明用途、调用路径、输入输出、验证方式和失败边界；经不起代码审查、搜索去重、测试运行或业务流程验证的内容不得提交。

具体要求：

- 不得复制粘贴已有函数后改名凑功能；应复用现有函数，或说明新函数不可复用的原因。
- 不得新增同义重复变量、重复状态、重复 API 封装、重复模型入口或重复页面入口。
- 不得保留未调用、无业务意义、无数据来源、无验证命令的代码和文件。
- 不得为了“看起来完整”提交占位实现、假接口、假数据、无效注释或不可维护的大段生成内容。
- 新增核心逻辑必须能被类型检查、单元测试、接口测试、算法验证或人工复现步骤中的至少一种方式验证。
- 如果某段代码暂时不能验证，必须在文档或 TODO 中明确原因、风险、后续验证方法和负责人，且不得伪装成已完成能力。

## GitHub 提交约束

禁止提交：

- 真实 `.env` 文件、数据库密码、用户密码、API Key、token 密钥、私钥或证书。
- `node_modules/`、`.venv/`、`__pycache__/`、`.pytest_cache/`、`dist/`、`target/` 等依赖、缓存和构建产物。
- 大体积模型权重、`.npy` 体数据、生产数据库备份、未脱敏真实数据。
- 重复文档、乱码文档、临时文件、个人笔记、旧目录和无维护价值文件。

每次按子目录改动时应单独提交，便于回滚和审查。提交前建议运行 `python tools/audit_repository.py`，确认禁止提交内容没有进入 Git 跟踪。

## 关键文档

- [docs/项目总体要求.md](docs/项目总体要求.md)
- [docs/technical-route-to-deployment.md](docs/technical-route-to-deployment.md)
- [docs/api-reference.md](docs/api-reference.md)
- [docs/dataset-sources.md](docs/dataset-sources.md)
- [docs/sensor-placement-guide.md](docs/sensor-placement-guide.md)
- [db/README.md](db/README.md)
- [tests/README.md](tests/README.md)

## License

MIT
