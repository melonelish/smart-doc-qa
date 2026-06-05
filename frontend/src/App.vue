<template>
  <n-config-provider :theme="naiveTheme.theme" :theme-overrides="naiveTheme.themeOverrides">
    <n-message-provider>
      <n-dialog-provider>
        <n-notification-provider>
          <div class="app-container">
            <SideNav />
            <div class="main-panel">
              <TopBar />
              <div class="content-area">
                <router-view />
              </div>
            </div>
            <KBCreateModal v-if="ui.createKBModalOpen" />
          </div>
          <HistoryPanel v-if="ui.historyPanelOpen" />
        </n-notification-provider>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { NConfigProvider, NMessageProvider, NDialogProvider, NNotificationProvider } from 'naive-ui'
import { useUiStore } from './stores/ui'
import { getNaiveTheme } from './styles/naive-theme'
import SideNav from './components/layout/SideNav.vue'
import TopBar from './components/layout/TopBar.vue'
import KBCreateModal from './components/knowledge/KBCreateModal.vue'
import HistoryPanel from './components/history/HistoryPanel.vue'

const ui = useUiStore()

const naiveTheme = computed(() => getNaiveTheme(ui.theme))

onMounted(() => ui.initTheme())
</script>

<style scoped>
.app-container {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: var(--bg-primary);
  color: var(--text-primary);
}
.main-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}
.content-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}
</style>