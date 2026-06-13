# API 接口文档

本文档记录当前项目接口约定。Java 后端与前端管理系统已统一使用标准 JSON 响应外壳；Python 算法服务应逐步对齐同一结构，或由网关/后端适配为同一结构后再返回前端。

## 统一认证

- 登录、注册接口不需要 token。
- 其他管理接口需要在请求头携带 `token`。
- 算法内部调用使用 `X-API-Key`，密钥只能来自环境变量或部署配置，不得写入代码。

## 统一响应结构

当前兼容协议如下：

```json
{
  "code": 200,
  "message": "成功",
  "data": {},
  "ok": true,
  "timestamp": 1781234567890,
  "requestId": "2f0b4b6d-0f40-44f2-b13c-2d8fd7d8d8c4"
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `code` | number | 是 | 业务状态码。当前前端兼容逻辑依赖 `200` 表示成功。 |
| `message` | string | 是 | 简短提示信息，失败时用于前端展示。 |
| `data` | object/array/string/null | 是 | 业务数据主体。 |
| `ok` | boolean | 是 | 成功标记，`code === 200` 时为 `true`。 |
| `timestamp` | number | 是 | 服务端响应时间，Unix 毫秒时间戳。 |
| `requestId` | string | 是 | 单次响应追踪 ID，用于日志定位和联动排查。 |

失败示例：

```json
{
  "code": 401,
  "message": "未登录",
  "data": null,
  "ok": false,
  "timestamp": 1781234567890,
  "requestId": "b4c0e0ba-65f2-48ef-a5fd-4a32a37c5a31"
}
```

## Java 后端 API

默认开发端口：`8081` 或部署配置指定端口。

### 用户认证

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/user/login` | 用户登录，成功后 `data` 返回 token。 |
| POST | `/api/user/register` | 用户注册。 |

### 小车管理

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/car/getAllCars` | 查询所有小车最新状态。 |
| POST | `/api/car/setWarning` | 手动设置小车预警状态。 |
| POST | `/api/car/resetStatus` | 重置小车状态。 |

### 图像分析

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/analysis/person` | 上传 JPG/PNG 图片，调用 YOLO11m 人员识别。 |
| GET | `/api/analysis/list` | 查询巡检识别记录。 |
| DELETE | `/api/analysis/delete/{id}` | 删除巡检识别记录。 |

`/api/analysis/person` 的 `data` 示例：

```json
{
  "status": "success",
  "count": 3,
  "image_base64": "..."
}
```

### 传感器与气体数据

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/sensor/list` | 查询传感器列表。 |
| POST | `/api/sensor/add` | 新增传感器。 |
| POST | `/api/sensor/update` | 更新传感器。 |
| POST | `/api/sensor/delete` | 删除传感器。 |
| GET | `/api/gas/list` | 查询气体类型。 |
| POST | `/api/gas/add` | 新增气体类型。 |
| POST | `/api/gas/update` | 更新气体类型。 |
| POST | `/api/gas/delete` | 删除气体类型。 |

### 监控点位布局

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/sensor-layout/list` | 查询布局方案列表。 |
| GET | `/api/sensor-layout/{id}` | 查询布局方案详情。 |
| POST | `/api/sensor-layout/save` | 保存布局方案。 |
| DELETE | `/api/sensor-layout/{id}` | 删除布局方案。 |

### 预警历史

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/warning/list` | 获取预警历史列表。 |
| POST | `/api/warning/save` | 保存预警记录。 |
| POST | `/api/warning/delete` | 删除预警记录。 |

## Python 算法 API

默认开发端口：`8000`。算法服务应接收 `X-API-Key`，并避免在日志中输出密钥。

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 服务健康检查。 |
| GET | `/api/gas-types` | 获取气体类型信息。 |
| POST | `/api/engine/run` | 算法引擎统一入口。 |
| POST | `/api/diffusion/simulate` | 运行气体扩散模拟。 |
| POST | `/api/gas-path` | 气体扩散与逃生路径联合计算。 |
| POST | `/api/time-series` | 时序扩散模拟。 |
| POST | `/api/inversion/coarse-search` | 泄漏源粗搜索。 |
| POST | `/api/inversion/solve` | 泄漏源反演求解。 |
| POST | `/api/inversion/particle-filter` | 粒子滤波泄漏源反演，输出位置、释放强度、置信区间和诊断指标。 |
| POST | `/api/planning/evacuation` | D* Lite 疏散路径规划。 |

## 响应码说明

| code | 说明 |
| --- | --- |
| 200 | 请求成功。 |
| 400 | 请求参数错误。 |
| 401 | 未登录、token 缺失或 token 无效。 |
| 403 | 已登录但权限不足。 |
| 404 | 资源不存在。 |
| 413 | 上传文件超过限制。 |
| 429 | 请求过于频繁。 |
| 500 | 服务端内部错误或算法服务异常。 |

## 维护约束

- 新增接口必须返回统一响应结构。
- 页面组件不得散落硬编码服务地址，确需直连时必须使用环境变量前缀。
- 新增字段、错误码或鉴权方式时，需要同步更新本文档。
- 不得提交真实 API Key、数据库密码、用户密码、token 密钥或真实 `.env` 文件。
