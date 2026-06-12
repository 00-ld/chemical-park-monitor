# Algorithm Service

本目录存放 Python 算法服务与核心算法实现，包括危险气体扩散、泄漏源溯源、D* Lite 逃生路径规划和 YOLO 人员识别服务。

## 标准入口

- `api_server.py`：统一 FastAPI 算法服务入口，提供扩散、溯源、路径规划和健康检查接口。
- `polo.py`：YOLO11m 人员识别服务入口，用于小车摄像头图片识别，通常由 Java 后端通过 `ANALYSIS_SERVICE_URL` 内网调用。
- `response_utils.py`：统一 JSON 响应封装工具。
- `gas_diffusion_astar.py`：扩散模拟与路径规划组合能力，保留现有接口名以兼容算法服务调用。

旧入口 `apiServer.py` 和 PyInstaller `.spec` 文件已删除。后续不得新增大小写混杂、职责重复的入口文件；服务入口统一使用蛇形命名。

## 子目录

```text
algorithm/
  diffusion/      气体扩散模型、公式基准、真实数据样本验证和物理不变量测试
  inversion/      泄漏源反演、EKI/PINN 相关实现
  planning/       D* Lite 逃生路径规划实现
  engine/         算法任务路由与统一调度入口
```

## 本地运行

```bash
python -m uvicorn api_server:app --host 127.0.0.1 --port 8000 --reload
python -m uvicorn polo:app --host 127.0.0.1 --port 8001 --reload
```

生产环境应通过 Docker/Nginx 内网访问算法服务，不应将算法端口直接暴露到公网。

## 模型与密钥

- `yolo11m.pt` 等模型权重不得提交到 GitHub。
- `ALGORITHM_API_KEY`、数据库密码、第三方 API Key 必须通过环境变量或部署平台密钥注入。
- 生产环境建议设置 `ALGORITHM_REQUIRE_AUTH=true`。

## 验证命令

从 `algorithm/` 目录运行：

```bash
python -m py_compile api_server.py response_utils.py polo.py
python -m diffusion.test_physical_invariants
python -m diffusion.test_improved_formula
python -m diffusion.test_calibration
python -m diffusion.test_gaussian_validation
python -m diffusion.test_real_prairie_grass
python test_path_hazard_avoidance.py
```

真实数据样本验证使用 `datasets/samples/prairie_grass/PGrassOBSAnalysis.txt`，来源和边界见 `docs/dataset-sources.md`。该测试只验证横风向扩散宽度 `Sy (m)`，不得把它扩大解释为绝对浓度或完整事故级模型验证。

## 提交边界

涉及真实数据集或大体积生成数据时，应只提交来源说明、元数据、小型可复现实验样本和必要验证脚本，不提交 `.npy`、模型权重、未脱敏数据或生产日志。
