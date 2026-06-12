# 化工园区危险气体扩散与溯源系统

本项目围绕化工园区危险气体扩散模拟、泄漏源溯源、传感器监控点位、小车巡检、逃生路径规划和 SuperMap iPortal 数字大屏展示构建。

当前仓库已按规范目录命名：前端在 `frontend/`，Java 后端在 `backend/`，Python 算法服务在 `algorithm/`，数据库台账在 `db/`，部署配置在 `deploy/`。

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
| 三维/数字孪生 | `frontend/src/views/screen/` | SuperMap iPortal 数字大屏 URL 嵌入 |
| 数据库 | `db/`、`deploy/mysql/` | MySQL 8、utf8mb4 |
| 部署 | `deploy/` | Docker Compose、Nginx、MySQL、前后端服务 |

## 目录说明

```text
.
  backend/              Java Spring Boot 后端
  frontend/            Vue 3 前端管理系统
  algorithm/            Python 算法服务与扩散/溯源/路径规划算法
  tests/                气体模型可复现测试数据与验证脚本
  db/                数据库目录台账、脚本索引和维护规则
  deploy/            Docker、Nginx、MySQL 初始化和部署配置
  docs/              项目总体要求、接口文档、数据集来源、架构说明
  docs/references/   政策、算法、设备等参考资料
  tools/             审计、校验、数据整理等辅助工具脚本
  assets/               项目图片资源
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
