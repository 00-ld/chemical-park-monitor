# Frontend Application

本目录存放 Vue 3 前端管理系统，负责主页态势展示、三维园区入口、扩散与溯源、小车管理、监控数据管理、人员管理和 404 页面。

## 技术栈

- Vue 3
- TypeScript
- Vite
- Element Plus
- Pinia
- ECharts
- Canvas
- SuperMap iPortal 数字大屏嵌入

## 页面与目录

```text
frontend/
  src/views/home/             主页态势展示
  src/views/screen/           SuperMap iPortal 数字大屏入口
  src/views/map_test/         园区二维/三维实验视图
  src/views/Car/              小车管理
  src/views/YOLO/             小车图片识别页面
  src/views/thing/            监控数据管理
  src/views/acl/              人员、角色、权限管理
  src/views/404/              统一 404 页面
  src/api/                    API 请求封装
  src/data/                   前端静态业务数据
  public/                     前端静态资源
```

## 运行命令

安装依赖：

```bash
npm ci
```

本地开发：

```bash
npm run dev
```

类型检查：

```bash
npm run typecheck
```

生产构建：

```bash
npm run build:pro
```

当前生产构建在 `vite.config.ts` 中关闭 minify，以避开 Windows + Node 25 + esbuild 0.18 的原生压缩崩溃；升级构建链路并验证后可重新评估压缩策略。

## 维护规则

- 页面风格必须与现有深色工业监控风格保持一致，不得随意改成营销页或完全不同的视觉体系。
- 新增接口调用必须放入 `src/api/` 或统一请求封装，不得在页面中散落硬编码 URL。
- 三维展示优先接入已建设的 SuperMap iPortal 数字大屏；Three.js/SuperMap 三维扩展应保持与 iPortal 数据接口兼容。
- Canvas 和 ECharts 相关高频渲染逻辑应避免在组件中重复定义同义变量和重复函数。
- `dist/`、`node_modules/`、临时截图、未压缩大文件和真实密钥不得提交到 GitHub。
- 图片、视频和模型资源应先确认用途；无法说明来源、用途或授权的资源不得新增提交。

## 环境变量

生产环境配置位于 `.env.production`，本地开发配置位于 `.env.development`。真实密钥不得写入前端环境文件；前端只能保存公开可见配置，例如 API 相对路径和 iPortal 大屏 URL。

常用变量：

- `VITE_APP_BASE_API`
- `VITE_ALGORITHM_BASE_API`
- `VITE_IPORTAL_DASHBOARD_URL`

## 提交检查

Husky hook 位于 `frontend/.husky/`。本项目使用 npm 和 `package-lock.json`，不得新增 pnpm/yarn 锁文件。

提交前至少执行：

```bash
npm run typecheck
```
