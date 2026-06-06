<template>
  <div class="history-panel">
    <div class="history-panel-header">
      <span class="history-panel-title">
        📜 问答历史
        <span v-if="kbStore.currentKb" class="history-panel-subtitle">· {{ kbStore.currentKb.name }}</span>
      </span>
      <n-button quaternary size="tiny" @click="ui.toggleHistoryPanel()">✕</n-button>
    </div>
    <div class="history-panel-body">
      <history-search v-model="searchQuery" />
      <div class="history-stats">
        <template v-if="searchQuery">
          找到 {{ filtered.length }} 个匹配
        </template>
        <template v-else>
          共 {{ convStore.history.length }} 个对话, {{ totalMessages }} 条消息
        </template>
      </div>
      <n-spin v-if="convStore.loadingHistory" size="small" />
      <!-- Skeleton while loading history -->
      <div v-if="convStore.loadingHistory" class="history-skeleton-list">
        <div v-for="i in 5" :key="i" class="history-skeleton-item">
          <n-skeleton height="14px" width="60%" style="margin-bottom: 6px" :sharp="false" />
          <n-skeleton height="12px" width="40%" :sharp="false" />
        </div>
      </div>
      <template v-else-if="!filtered.length">
        <n-empty :description="searchQuery ? '无匹配结果' : '暂无问答记录'" />
      </template>
      <template v-else>
        <div v-for="group in grouped" :key="group.label" class="history-group">
          <div class="history-group-label">{{ group.label }}</div>
          <history-item
            v-for="conv in group.items"
            :key="conv.conversation_id"
            :conversation="conv"
            :highlight="searchQuery"
            @restore="handleRestore"
            @delete="handleDelete"
          />
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { NButton, NSpin, NEmpty } from 'naive-ui'
import { useUiStore } from '../../stores/ui'
import { useConversationStore } from '../../stores/conversation'
import { useKnowledgeBaseStore } from '../../stores/knowledgeBase'
import HistorySearch from './HistorySearch.vue'
import HistoryItem from './HistoryItem.vue'

const ui = useUiStore()
const convStore = useConversationStore()
const kbStore = useKnowledgeBaseStore()
const searchQuery = ref('')

const totalMessages = computed(() => convStore.history.reduce((sum, h) => sum + h.message_count, 0))

const filtered = computed(() => {
  if (!searchQuery.value) return convStore.history
  const q = searchQuery.value.toLowerCase().trim()
  return convStore.history.filter((h) => {
    // 搜索实际显示的文本（与 UI 显示逻辑一致：last_question 优先）
    const displayText = (h.last_question || h.first_question || '').toLowerCase()
    return displayText.includes(q)
  })
})

// 按日期分组
const grouped = computed(() => {
  const groups: Record<string, typeof convStore.history> = {}
  for (const conv of filtered.value) {
    const dateKey = getLocalDateKey(conv.last_activity_at)
    if (!groups[dateKey]) groups[dateKey] = []
    groups[dateKey].push(conv)
  }
  // 按日期倒序排列
  return Object.entries(groups)
    .sort(([a], [b]) => b.localeCompare(a))
    .map(([dateKey, items]) => ({
      label: formatDateLabel(dateKey),
      items,
    }))
})

function getLocalDateKey(dateStr: string): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return ''
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function formatDateLabel(dateKey: string): string {
  if (!dateKey) return '未知日期'
  const today = new Date()
  const todayKey = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
  
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)
  const yesterdayKey = `${yesterday.getFullYear()}-${String(yesterday.getMonth() + 1).padStart(2, '0')}-${String(yesterday.getDate()).padStart(2, '0')}`
  
  if (dateKey === todayKey) return '今天'
  if (dateKey === yesterdayKey) return '昨天'
  
  const [y, m, d] = dateKey.split('-')
  return `${Number(m)}月${Number(d)}日`
}

async function handleRestore(convId: string) {
  const conv = convStore.history.find((h) => h.conversation_id === convId)
  if (!conv) return
  await convStore.restoreConversation(convId, conv.document_id)
  window.$message?.success?.(`已恢复 ${conv.message_count} 条消息`)
  ui.historyPanelOpen = false
}

async function handleDelete(convId: string) {
  await convStore.removeConversation(convId)
}

onMounted(() => {
  convStore.loadHistory(kbStore.currentKbId || undefined)
})

// 当切换知识库时，如果历史面板打开，刷新历史记录
watch(() => kbStore.currentKbId, (newId) => {
  if (newId && ui.historyPanelOpen) {
    convStore.loadHistory(newId)
  }
})
</script>

<style scoped>
.history-panel {
  position: fixed;
  top: 0;
  right: 0;
  width: 380px;
  height: 100vh;
  background: var(--bg-card);
  border-left: 1px solid var(--border);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-lg);
  animation: slideIn 0.3s ease;
  overflow: hidden;
}
@keyframes slideIn {
  from { transform: translateX(100%); }
  to { transform: translateX(0); }
}
.history-panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}
.history-panel-title {
  font-size: 14px;
  font-weight: 600;
}
.history-panel-subtitle {
  font-size: 12px;
  font-weight: 400;
  color: var(--text-muted);
  margin-left: 4px;
}
.history-panel-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 12px 16px;
}
/* 显式滚动条 */
.history-panel-body::-webkit-scrollbar {
  width: 5px;
}
.history-panel-body::-webkit-scrollbar-track {
  background: transparent;
}
.history-panel-body::-webkit-scrollbar-thumb {
  background: var(--text-muted);
  border-radius: 3px;
}
.history-panel-body::-webkit-scrollbar-thumb:hover {
  background: var(--text-secondary);
}
.history-stats {
  font-size: 11px;
  color: var(--text-muted);
  padding: 4px 0 8px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 8px;
}
.history-group {
  margin-bottom: 12px;
}
.history-group-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
  padding: 4px 0;
  margin-bottom: 4px;
}
</style>
