<template>
  <div class="history-item">
    <div class="history-item-main" @click="$emit('restore', conversation.conversation_id)">
      <div class="history-preview">{{ previewText }}</div>
      <div class="history-meta">
        <span class="history-time">{{ formatTime(conversation.last_activity_at) }}</span>
        <span class="history-count">{{ conversation.message_count }} 条</span>
      </div>
    </div>
    <n-popconfirm @positive-click="$emit('delete', conversation.conversation_id)">
      <template #trigger>
        <n-button quaternary size="tiny" circle class="history-del-btn">
          <template #icon><span style="font-size: 11px">🗑️</span></template>
        </n-button>
      </template>
      确定删除此对话？
    </n-popconfirm>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NButton, NPopconfirm } from 'naive-ui'
import type { ConversationSummary } from '../../api/types'

const props = defineProps<{ conversation: ConversationSummary }>()
defineEmits<{
  restore: [id: string]
  delete: [id: string]
}>()

const previewText = computed(() => {
  // 优先显示最新的问题
  const question = props.conversation.last_question || props.conversation.first_question
  if (question) {
    return question.length > 60
      ? question.slice(0, 60) + '...'
      : question
  }
  return props.conversation.conversation_id.slice(0, 16) + '...'
})

function formatTime(dateStr: string) {
  if (!dateStr) return ''
  // 后端返回 UTC 时间（如 2026-06-05T12:28:46+00:00），转换为本地时间
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return ''
  const h = String(d.getHours()).padStart(2, '0')
  const m = String(d.getMinutes()).padStart(2, '0')
  return `${h}:${m}`
}
</script>

<style scoped>
.history-item {
  display: flex;
  align-items: stretch;
  border-radius: var(--radius-sm);
  transition: var(--transition);
  margin-bottom: 4px;
  border: 1px solid transparent;
  overflow: hidden;
}
.history-item:hover {
  border-color: var(--border-light);
}
.history-item-main {
  flex: 1;
  padding: 8px 12px;
  cursor: pointer;
}
.history-item-main:hover {
  background: var(--bg-card-hover);
}
.history-preview {
  font-size: 12px;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 300px;
}
.history-meta {
  font-size: 10px;
  color: var(--text-muted);
  margin-top: 2px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.history-time {
  color: var(--text-secondary);
}
.history-count {
  color: var(--text-muted);
}
.history-del-btn {
  flex-shrink: 0;
  opacity: 0;
  transition: var(--transition);
}
.history-item:hover .history-del-btn {
  opacity: 1;
}
</style>
