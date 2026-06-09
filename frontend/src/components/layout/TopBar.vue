<template>
  <n-layout-header bordered class="top-bar">
    <div class="flex items-center gap-3">
      <span class="top-bar-title">{{ domainStore.currentDomain.icon }} {{ domainStore.currentDomain.name }}</span>
      <n-tag size="small" type="success" :bordered="false">v2.7</n-tag>
    </div>
    <div class="top-bar-right">
      <n-tag v-if="kbStore.currentKb?.name" size="small" type="info" :bordered="false">
        {{ kbStore.currentKb.name }}
      </n-tag>
      <n-button
        :quaternary="true"
        size="small"
        @click="ui.toggleTheme"
        :title="ui.theme === 'dark' ? '切换亮色' : '切换暗色'"
      >
        {{ ui.theme === 'dark' ? '☀️' : '🌙' }}
      </n-button>
      <n-button quaternary size="small" @click="$router.push('/settings')" title="设置">
        ⚙️
      </n-button>
      <span class="user-name" v-if="auth.username">{{ auth.username }}</span>
      <n-button quaternary size="small" @click="handleLogout" title="退出登录">
        退出
      </n-button>
    </div>
  </n-layout-header>
</template>

<script setup lang="ts">
import { NLayoutHeader, NButton, NTag } from 'naive-ui'
import { useRouter } from 'vue-router'
import { useUiStore } from '../../stores/ui'
import { useDomainStore } from '../../stores/domain'
import { useKnowledgeBaseStore } from '../../stores/knowledgeBase'
import { useAuthStore } from '../../stores/auth'

const ui = useUiStore()
const domainStore = useDomainStore()
const kbStore = useKnowledgeBaseStore()
const auth = useAuthStore()
const router = useRouter()

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.top-bar {
  height: 56px;
  min-height: 56px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}
.top-bar-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
}
.top-bar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
.flex { display: flex; }
.items-center { align-items: center; }
.gap-3 { gap: 10px; }
</style>