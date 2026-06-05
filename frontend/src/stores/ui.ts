import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUiStore = defineStore('ui', () => {
  const theme = ref<'dark' | 'light'>(
    (localStorage.getItem('theme') as 'dark' | 'light') || 'dark',
  )
  const historyPanelOpen = ref(false)
  const createKBModalOpen = ref(false)
  const previewModalOpen = ref(false)
  const previewDocId = ref<string | null>(null)
  const processingModalOpen = ref(false)

  function toggleTheme() {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
    localStorage.setItem('theme', theme.value)
    document.documentElement.setAttribute('data-theme', theme.value)
  }

  function initTheme() {
    document.documentElement.setAttribute('data-theme', theme.value)
  }

  function toggleHistoryPanel() {
    historyPanelOpen.value = !historyPanelOpen.value
  }

  return {
    theme, historyPanelOpen, createKBModalOpen,
    previewModalOpen, previewDocId, processingModalOpen,
    toggleTheme, initTheme, toggleHistoryPanel,
  }
})
