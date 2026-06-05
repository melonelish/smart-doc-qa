<template>
  <n-input
    :value="modelValue"
    @update:value="$emit('update:modelValue', $event)"
    placeholder="🔍 搜索对话..."
    size="small"
    clearable
  />
</template>

<script setup lang="ts">
import { NInput } from 'naive-ui'

defineProps<{ modelValue: string }>()
defineEmits<{ 'update:modelValue': [value: string] }>()
</script>