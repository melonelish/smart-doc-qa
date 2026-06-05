<template>
  <n-empty :description="text" v-bind="$attrs">
    <template v-if="icon || $slots.icon" #icon>
      <slot name="icon">
        <span style="font-size: 40px; opacity: 0.4">{{ icon }}</span>
      </slot>
    </template>
    <slot />
  </n-empty>
</template>

<script setup lang="ts">
import { NEmpty } from 'naive-ui'

defineProps<{
  icon?: string
  text?: string
}>()
</script>