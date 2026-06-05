/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

interface Window {
  $message?: {
    success?: (msg: string) => void
    error?: (msg: string) => void
    info?: (msg: string) => void
    warning?: (msg: string) => void
  }
}
