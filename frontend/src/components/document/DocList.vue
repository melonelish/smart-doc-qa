<template>
  <div class="doc-list">
    <!-- Skeleton while loading -->
    <div v-if="loading" class="doc-skeleton-list">
      <div v-for="i in 4" :key="i" class="doc-skeleton-card">
          <n-skeleton height="32px" width="32px" :sharp="false" />
          <div class="doc-skeleton-body">
            <n-skeleton height="14px" width="70%" />
            <n-skeleton height="12px" width="40%" style="margin-top: 6px" />
          </div>
          <n-skeleton height="22px" width="22px" :sharp="false" />
        </div>
    </div>
    <template v-else-if="!items.length">
      <n-empty description="暂无文档" />
    </template>
    <DocItem
      v-for="doc in items"
      :key="doc.id"
      :doc="doc"
      :processing="processing[doc.id]"
      @delete="$emit('delete-doc', doc.id)"
      @process="$emit('process-doc', doc.id)"
      @preview="$emit('preview-doc', $event)"
    />
  </div>
</template>

<script setup lang="ts">
import { NSpin, NEmpty, NSkeleton } from 'naive-ui'
import type { Document } from '../../api/types'
import DocItem from './DocItem.vue'

defineProps<{
  items: Document[]
  loading: boolean
  processing: Record<string, { stage: string; percent: number }>
}>()

defineEmits<{
  'delete-doc': [id: string]
  'process-doc': [id: string]
  'preview-doc': [doc: Document]
}>()
</script>

<style scoped>
.doc-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: calc(100vh - 360px);
  overflow-y: auto;
}
.doc-skeleton-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.doc-skeleton-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: var(--bg-input);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
}
.doc-skeleton-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
</style>