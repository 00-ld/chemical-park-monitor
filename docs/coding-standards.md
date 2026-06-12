# 编码规范

本文档定义了化工园区智能监测项目的代码规范，所有开发人员应严格遵守。

## 通用规范

### 命名规范（Google Style）

| 类型 | 规范 | 示例 |
|------|------|------|
| 类/接口 | PascalCase | `CarController`, `UserService` |
| 方法/函数 | camelCase | `getAllCars()`, `formatGeoCoord()` |
| 常量 | UPPER_SNAKE | `MAX_RETRY_COUNT` |
| 变量 | camelCase | `carList`, `userStore` |
| 包名 | lowercase | `com.at.controller` |
| Python 模块 | snake_case | `diffusion_runner.py` |
| Python 类 | PascalCase | `AStarPathPlanner` |

### 目录命名规范

- 一级目录统一使用小写英文领域名，当前规范目录为 `frontend/`、`backend/`、`algorithm/`、`tests/`、`db/`、`deploy/`、`docs/`、`tools/`、`assets/`。
- 禁止提交中文目录名、空格目录名、大小写混用目录名、个人临时目录名和旧工程目录名。
- 历史目录名必须归并到规范目录：`Manage/` 归并到 `frontend/`，`Back/` 归并到 `backend/`，`algorithm_tests/` 归并到 `tests/`，`python/` 归并到 `algorithm/`。
- 二级目录按技术栈约定命名：Python 使用 `snake_case`，Java 包路径使用小写英文，Vue 组件目录使用清晰英文语义。

### 文件结构

```
frontend/
  views/        → 页面级组件
  components/   → 可复用组件
  api/          → API 接口封装
  store/        → 状态管理
  utils/        → 工具函数
  data/         → 静态数据

backend/
  controller/   → 请求处理层
  service/      → 业务逻辑层
  mapper/       → 数据访问层
  pojo/         → 数据模型
  utils/        → 工具类

algorithm/
  diffusion/    → 扩散模型
  inversion/    → 溯源反演
  planning/     → 路径规划
  engine/       → 引擎路由
```

---

## 前端规范 (Vue3 + TypeScript)

### 组件规范
- 统一使用 `<script setup lang="ts">` Composition API
- 组件名多词 PascalCase，避免与 HTML 元素冲突
- 使用 `defineOptions({ name: 'ComponentName' })` 定义组件名

### 类型安全
- 禁止使用 `: any`，必须定义具体接口
- API 响应需定义返回类型
- props 使用 `defineProps<Type>()` 带类型参数

### 导入顺序
```
// 1. Vue 框架
import { ref, computed } from 'vue'
// 2. 第三方库
import { ElMessage } from 'element-plus'
// 3. 本地模块
import request from '@/utils/request'
```

### 状态管理
- 使用 Pinia，模块化拆分 store
- 组件内使用 `storeToRefs()` 解构

---

## 后端规范 (Java / Spring Boot)

### API 响应
- 统一使用 `ResponseEntity<Result<T>>`
- 不手动构建 `Map<String, Object>` 响应

### 异常处理
- 业务异常抛出特定异常类型
- `@RestControllerAdvice` 全局统一处理

### 日志
- 使用 `@Slf4j` 注解
- 关键操作记录 `log.info()`，异常记录 `log.error()`

### 校验
- Controller 参数使用 `@Valid` 注解校验
- 实体字段使用 `@NotBlank`、`@Min` 等校验注解

---

## 算法规范 (Python)

### 文档字符串
使用 Google 风格 docstring：

```python
def function_name(param1: str, param2: int) -> bool:
    """简短描述功能。

    Args:
        param1: 参数1描述。
        param2: 参数2描述。

    Returns:
        返回值描述。

    Raises:
        ValueError: 异常条件描述。
    """
```

### 导入顺序
每组按字母序排列，组间空一行：
```
# 标准库
import math
from typing import Dict

# 第三方库
import numpy as np
from fastapi import FastAPI

# 本地模块
from diffusion.diffusion_runner import run_simulation
```

### API 统一返回
所有接口返回 `{"success": bool, "data": ..., "error": str|null, "code": int}`
