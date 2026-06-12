/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

// 环境变量类型声明。
interface ImportMetaEnv {
  readonly VITE_APP_BASE_API: string
  readonly VITE_SERVE: string
  readonly VITE_ALGORITHM_BASE_API: string
  readonly VITE_ALGORITHM_SERVE: string
  readonly VITE_IPORTAL_DASHBOARD_URL: string
  readonly VITE_QWEATHER_KEY: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
