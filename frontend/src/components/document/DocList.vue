<template>
  <div class="doc-list">
    <n-spin v-if="loading" size="small" />
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
import { NSpin, NEmpty } from 'naive-ui'
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
</style>