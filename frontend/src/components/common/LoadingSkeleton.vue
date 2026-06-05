<template>
  <div class="skeleton" :style="{ width, height }"></div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  width?: string
  height?: string
}>(), {
  width: '100%',
  height: '16px',
})
</script>

<style scoped>
.skeleton {
  background: linear-gradient(90deg, var(--bg-input) 25%, var(--bg-card-hover) 50%, var(--bg-input) 75%);
  background-size: 200% 100%;
  border-radius: var(--radius-sm);
  animation: shimmer 1.5s infinite;
}
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
