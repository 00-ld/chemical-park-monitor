# API 接口文档

## Java 后端 API (端口 8080)

### 认证
需要 JWT Token，在请求头中携带 `token` 字段。

### 小车管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/car/getAllCars` | 查询所有小车最新状态 |
| POST | `/api/car/setWarning` | 手动预警小车 |
| POST | `/api/car/resetStatus` | 重置小车状态 |

### 预警历史

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/warning/list` | 获取预警历史列表 |
| POST | `/api/warning/save` | 保存预警记录 |

### 用户认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/user/login` | 用户登录 |
| POST | `/api/user/register` | 用户注册 |

### 图像分析

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/image/analysis` | 图像分析识别 |

---

## Python 算法 API (端口 8000)

### 统一响应格式

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "code": 200
}
```

### 算法引擎

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/engine/run` | 算法引擎统一入口 |

请求格式：
```json
{
  "task_type": "run_diffusion_simulation",
  "payload": { ... }
}
```

### 气体扩散

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/diffusion/simulate` | 运行扩散模拟 |
| GET | `/api/gas-types` | 获取气体类型信息 |
| POST | `/api/gas-path` | 气体扩散 + 路径规划 |
| POST | `/api/time-series` | 时序扩散模拟 |

### 泄漏溯源

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/inversion/coarse-search` | PINN 粗搜索 |
| POST | `/api/inversion/solve` | PINN 反演求解 |

### 路径规划

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/planning/evacuation` | 疏散路径规划 |

### 健康检查

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 服务健康状态 |

### 响应码说明

| code | 说明 |
|------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 401 | 身份验证失败 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
