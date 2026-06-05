<template>
  <div class="kb-selector-wrapper">
    <n-select
      :value="modelValue"
      :options="options"
      placeholder="请选择知识库"
      :clearable="true"
      :filterable="true"
      size="small"
      @update:value="(val: string | null) => $emit('update:modelValue', val)"
    >
      <template #action>
        <n-button size="tiny" quaternary block @click="$emit('create-kb')">
          ＋ 新建知识库
        </n-button>
      </template>
    </n-select>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NSelect, NButton } from 'naive-ui'
import type { KnowledgeBase } from '../../api/types'

const props = defineProps<{
  modelValue: string | null
  list: KnowledgeBase[]
}>()

defineEmits<{
  'update:modelValue': [id: string | null]
  'delete-kb': [id: string]
  'create-kb': []
}>()

const options = computed(() =>
  props.list.map((kb) => ({
    label: `${kb.name} (${kb.document_count || 0} 个文档)`,
    value: kb.id,
  })),
)
</script>

<style scoped>
.kb-selector-wrapper {
  min-width: 0;
}
</style>