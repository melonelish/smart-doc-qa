import { onMounted } from 'vue'
import { useUiStore } from '../stores/ui'

export function useTheme() {
  const ui = useUiStore()

  onMounted(() => {
    ui.initTheme()
  })

  return {
    theme: ui.theme,
    toggleTheme: ui.toggleTheme,
  }
}
