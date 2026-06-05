<template>
  <n-tag :type="tagType" size="tiny" :bordered="false">{{ label }}</n-tag>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NTag } from 'naive-ui'
import type { DocumentStatus } from '../../api/types'

const props = defineProps<{ status: DocumentStatus }>()

const map: Record<string, { type: 'success' | 'warning' | 'info' | 'error'; label: string }> = {
  ready: { type: 'success', label: '就绪' },
  processing: { type: 'warning', label: '处理中' },
  uploaded: { type: 'info', label: '已上传' },
  failed: { type: 'error', label: '失败' },
}

const tagType = computed(() => map[props.status]?.type ?? 'default')
const label = computed(() => map[props.status]?.label ?? props.status)
</script>