<template>
  <div class="chat-messages" ref="scrollRef">
    <div v-if="!messages.length" class="chat-empty">
      <div class="empty-icon">💬</div>
      <h3>开始提问</h3>
      <p>选择知识库后，在下方输入问题，AI 将基于文档内容回答</p>
    </div>
    <MessageItem
      v-for="msg in messages"
      :key="msg.id"
      :message="msg"
      :highlight="highlight"
    />
    <div ref="bottomRef"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import type { Message } from '../../stores/conversation'
import MessageItem from './MessageItem.vue'

const props = defineProps<{
  messages: Message[]
  streaming: boolean
  highlight?: string
}>()

const bottomRef = ref<HTMLElement | null>(null)

// Auto-scroll on new messages (not when filtered/search)
watch(
  () => props.messages.length,
  async (newLen, oldLen) => {
    if (newLen > oldLen) {
      await nextTick()
      bottomRef.value?.scrollIntoView({ behavior: 'smooth' })
    }
  },
)

// Also scroll when streaming content updates
watch(
  () => props.messages[props.messages.length - 1]?.content,
  async () => {
    if (props.streaming) {
      await nextTick()
      bottomRef.value?.scrollIntoView({ behavior: 'smooth' })
    }
  },
)
</script>

<style scoped>
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px 0;
  min-height: 0;
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
