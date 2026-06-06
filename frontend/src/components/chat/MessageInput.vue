<template>
  <div class="chat-input-area">
    <n-input
      ref="inputRef"
      v-model:value="text"
      type="textarea"
      :placeholder="disabled ? '请先选择知识库' : '输入你的问题，AI 将从文档中智能检索答案...'"
      :disabled="disabled"
      :autosize="{ minRows: 1, maxRows: 4 }"
      @keydown="onKeyDown"
    />
    <n-button
      type="primary"
      :disabled="disabled || !text.trim()"
      @click="send"
      style="flex-shrink: 0"
    >
      ➤
    </n-button>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { NInput, NButton } from 'naive-ui'

const props = defineProps<{
  disabled: boolean
}>()

const emit = defineEmits<{
  send: [question: string]
}>()

const text = ref('')

function onKeyDown(e: KeyboardEvent) {
  if (e.key === 'Enter') {
    if (e.ctrlKey || e.metaKey) {
      // Ctrl/Cmd+Enter → 手动插入换行（Naive UI 已阻止默认行为）
      e.preventDefault()
      const target = e.target as HTMLTextAreaElement
      const start = target.selectionStart
      const end = target.selectionEnd
      text.value = text.value.substring(0, start) + '\n' + text.value.substring(end)
      // 下一 tick 恢复光标位置
      nextTick(() => {
        target.selectionStart = target.selectionEnd = start + 1
      })
      return
    }
    if (e.shiftKey) {
      // Shift+Enter → 也允许换行
      return
    }
    // 单独 Enter → 发送
    e.preventDefault()
    send()
  }
}

function send() {
  const q = text.value.trim()
  if (!q || props.disabled) return
  emit('send', q)
  text.value = ''
}
</script>

<style scoped>
.chat-input-area {
  padding: 14px 20px;
  border-top: 1px solid var(--border);
  display: flex;
  gap: 8px;
  align-items: flex-end;
}
</style>