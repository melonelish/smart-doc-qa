<template>
  <div class="doc-item" :class="{ selected: false }">
    <div class="doc-icon" :class="iconClass" @click="$emit('preview', doc)" style="cursor: pointer">{{ iconText }}</div>
    <div class="doc-info" @click="$emit('preview', doc)" style="cursor: pointer">
      <div class="doc-name" :title="doc.filename">{{ doc.filename }}</div>
      <div class="doc-meta">
        <DocStatusTag :status="doc.status" />
        <span class="ml-2">{{ formatSize(doc.file_size) }}</span>
        <span v-if="doc.created_at" class="ml-2">{{ formatDate(doc.created_at) }}</span>
        <span v-if="processing" class="ml-2">
          {{ processing.stage }} {{ processing.percent }}%
        </span>
      </div>
      <div v-if="doc.status === 'failed' && doc.error_message" class="doc-error">
        ❌ {{ doc.error_message.slice(0, 50) }}{{ doc.error_message.length > 50 ? '...' : '' }}
      </div>
    </div>
    <div class="doc-actions">
      <n-button v-if="doc.status === 'uploaded' || doc.status === 'failed'" quaternary size="tiny" circle @click="$emit('process')">
        <template #icon><span style="font-size: 12px">⚡</span></template>
      </n-button>
      <n-popconfirm @positive-click="$emit('delete')">
        <template #trigger>
          <n-button quaternary size="tiny" circle>
            <template #icon><span style="font-size: 12px">🗑️</span></template>
          </n-button>
        </template>
        确定删除此文档？
      </n-popconfirm>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NButton, NPopconfirm } from 'naive-ui'
import type { Document } from '../../api/types'
import DocStatusTag from './DocStatusTag.vue'

const props = defineProps<{
  doc: Document
  processing?: { stage: string; percent: number }
}>()

defineEmits<{ delete: []; process: []; preview: [doc: Document] }>()

const ext = computed(() => props.doc.file_type.toLowerCase())
const iconClass = computed(() => {
  if (ext.value === '.pdf') return 'pdf'
  if (ext.value === '.txt') return 'txt'
  if (ext.value === '.csv') return 'csv'
  if (ext.value === '.md') return 'md'
  return 'default'
})
const iconText = computed(() => {
  if (ext.value === '.pdf') return 'PDF'
  if (ext.value === '.txt') return 'TXT'
  if (ext.value === '.csv') return 'CSV'
  if (ext.value === '.md') return 'MD'
  if (ext.value === '.docx') return 'DOC'
  return '📄'
})

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + 'B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + 'KB'
  return (bytes / (1024 * 1024)).toFixed(1) + 'MB'
}

function formatDate(dateStr: string) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}
</script>

<style scoped>
.doc-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: var(--bg-input);
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  transition: var(--transition);
  cursor: default;
}
.doc-item:hover {
  border-color: var(--border-light);
  background: var(--bg-card-hover);
}
.doc-icon {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  flex-shrink: 0;
}
.doc-icon.pdf { background: rgba(239, 68, 68, 0.15); color: #ef4444; }
.doc-icon.txt { background: rgba(59, 130, 246, 0.15); color: #3b82f6; }
.doc-icon.csv { background: rgba(16, 185, 129, 0.15); color: #10b981; }
.doc-icon.md { background: rgba(139, 92, 246, 0.15); color: #8b5cf6; }
.doc-icon.default { background: rgba(148, 163, 184, 0.15); color: #94a3b8; }
.doc-info {
  flex: 1;
  min-width: 0;
}
.doc-name {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.doc-meta {
  font-size: 10px;
  color: var(--text-muted);
  margin-top: 2px;
  display: flex;
  align-items: center;
  gap: 4px;
}
.doc-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}
.doc-error {
  font-size: 10px;
  color: #ef4444;
  margin-top: 2px;
  line-height: 1.3;
}
.ml-2 {
  margin-left: 4px;
}
</style>