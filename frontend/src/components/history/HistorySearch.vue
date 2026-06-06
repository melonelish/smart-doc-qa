<template>
  <n-input
    :value="modelValue"
    @update:value="$emit('update:modelValue', $event)"
    placeholder="🔍 搜索对话..."
    size="small"
    clearable
    class="history-search-input"
  />
</template>

<script setup lang="ts">
import { NInput } from 'naive-ui'

defineProps<{ modelValue: string }>()
defineEmits<{ 'update:modelValue': [value: string] }>()
</script>

<style scoped>
.history-search-input {
  margin-bottom: 8px;
}
.history-search-input :deep(.n-input__input-el) {
  font-size: 13px !important;
}
</style>