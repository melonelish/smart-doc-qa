<template>
  <n-space vertical :size="0" class="chat-messages" ref="scrollRef">
    <div v-if="!messages.length" class="chat-empty">
      <div class="empty-icon">💬</div>
      <h3>开始提问</h3>
      <p>选择知识库后，在下方输入问题，AI 将基于文档内容回答</p>
    </div>
    <MessageItem
      v-for="msg in messages"
      :key="msg.id"
      :message="msg"
    />
    <div ref="bottomRef"></div>
  </n-space>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { NSpace } from 'naive-ui'
import type { Message } from '../../stores/conversation'
import MessageItem from './MessageItem.vue'

const props = defineProps<{
  messages: Message[]
  streaming: boolean
}>()

const bottomRef = ref<HTMLElement | null>(null)

// Auto-scroll on new messages
watch(
  () => props.messages.length,
  async () => {
    await nextTick()
    bottomRef.value?.scrollIntoView({ behavior: 'smooth' })
  },
)
</script>

<style scoped>
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}
.chat-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  padding: 40px;
  text-align: center;
}
.chat-empty .empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.3;
}
.chat-empty h3 {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 6px;
}
.chat-empty p {
  font-size: 12px;
  line-height: 1.6;
  max-width: 320px;
}
</style>