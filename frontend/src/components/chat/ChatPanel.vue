<template>
  <div class="chat-container">
    <div class="chat-header">
      <div class="chat-header-info">
        <span class="chat-header-title">{{ headerTitle }}</span>
        <span v-if="headerSub" class="chat-header-sub">{{ headerSub }}</span>
      </div>
      <n-space :size="6">
        <n-button size="tiny" secondary :disabled="!convStore.messages.length" @click="convStore.clear()">
          🗑️ 清空
        </n-button>
        <n-button size="tiny" secondary @click="ui.toggleHistoryPanel()">
          📜 历史
        </n-button>
      </n-space>
    </div>
    <div class="chat-body">
      <!-- Domain Intro when no messages -->
      <div v-if="!convStore.messages.length" class="domain-intro-embedded">
        <div class="domain-intro-header">
          <div class="welcome-icon">{{ domain.icon }}</div>
          <h1 class="welcome-title">{{ domain.name }}</h1>
          <p class="welcome-subtitle">{{ domain.description }}</p>
        </div>
        <div class="domain-section-label">常见问题示例</div>
        <div class="domain-features">
          <div v-for="(f, i) in domain.features" :key="i" class="domain-feature">
            <span class="domain-feature-q">{{ f.q }}</span>
            <span class="domain-feature-a">{{ f.a }}</span>
          </div>
        </div>
        <div class="domain-section-label">支持文档类型</div>
        <div class="domain-doc-types">
          <div v-for="(dt, i) in domain.docTypes" :key="i" class="domain-doc-type">
            <div class="domain-doc-type-icon">{{ dt.icon }}</div>
            <div class="domain-doc-type-name">{{ dt.name }}</div>
            <div class="domain-doc-type-desc">{{ dt.desc }}</div>
          </div>
        </div>
        <div class="domain-section-label">核心能力</div>
        <div class="domain-capabilities">
          <div v-for="(c, i) in domain.capabilities" :key="i" class="domain-capability">
            <div class="domain-capability-icon">{{ c.icon }}</div>
            <div class="domain-capability-body">
              <div class="domain-capability-label">{{ c.label }}</div>
              <div class="domain-capability-desc">{{ c.desc }}</div>
            </div>
          </div>
        </div>
        <div class="domain-intro-footer">
          <p class="welcome-hint">支持 PDF / TXT / Markdown / CSV / Word</p>
        </div>
      </div>
      <MessageList
        v-else
        :messages="convStore.messages"
        :streaming="convStore.streaming"
      />
    </div>
    <MessageInput
      :disabled="!kbStore.currentKbId || convStore.streaming"
      @send="handleSend"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NSpace, NButton } from 'naive-ui'
import { useUiStore } from '../../stores/ui'
import { useKnowledgeBaseStore } from '../../stores/knowledgeBase'
import { useConversationStore } from '../../stores/conversation'
import { useDomainStore } from '../../stores/domain'
import MessageList from './MessageList.vue'
import MessageInput from './MessageInput.vue'

const ui = useUiStore()
const kbStore = useKnowledgeBaseStore()
const convStore = useConversationStore()
const domainStore = useDomainStore()
const domain = domainStore.currentDomain

const headerTitle = computed(() => kbStore.currentKb?.name || '选择知识库开始对话')
const headerSub = computed(() => {
  if (!kbStore.currentKbId) return '请先选择或创建一个知识库'
  const count = convStore.messages.length
  return count ? `${count} 条消息` : ''
})

async function handleSend(question: string) {
  if (!kbStore.currentKbId) return
  await convStore.sendQuestion({
    kb_id: kbStore.currentKbId,
    question,
  })
}
</script>

<style scoped>
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  height: 100%;
}
.chat-header {
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}
.chat-header-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.chat-header-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}
.chat-header-sub {
  font-size: 11px;
  color: var(--text-muted);
}
.chat-body {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.domain-intro-embedded {
  max-width: 540px;
  margin: 0 auto;
  padding: 20px 16px;
}
.domain-intro-header {
  margin-bottom: 20px;
  text-align: center;
}
.domain-intro-embedded .welcome-icon { font-size: 40px; margin-bottom: 8px; }
.domain-intro-embedded .welcome-title {
  font-size: 22px;
  font-weight: 800;
  background: linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 4px;
}
.domain-intro-embedded .welcome-subtitle {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}
.domain-section-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.8px;
  margin: 16px 0 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--border);
}
.domain-features {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.domain-feature {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 7px 10px;
  background: var(--bg-input);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
}
.domain-feature-q {
  font-weight: 600;
  color: var(--accent-light);
  font-size: 12px;
  white-space: nowrap;
  flex-shrink: 0;
}
.domain-feature-a {
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.5;
}
.domain-doc-types {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 6px;
}
.domain-doc-type {
  padding: 8px 10px;
  background: var(--bg-input);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  text-align: center;
}
.domain-doc-type-icon { font-size: 18px; margin-bottom: 3px; }
.domain-doc-type-name { font-size: 11px; font-weight: 600; color: var(--text-primary); margin-bottom: 2px; }
.domain-doc-type-desc { font-size: 10px; color: var(--text-muted); line-height: 1.3; }
.domain-capabilities {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 5px;
}
.domain-capability {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 9px;
  background: var(--bg-card);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  transition: border-color 0.2s;
}
.domain-capability:hover { border-color: var(--accent); }
.domain-capability-icon {
  font-size: 14px;
  flex-shrink: 0;
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-input);
  border-radius: 6px;
}
.domain-capability-label { font-size: 11px; font-weight: 600; color: var(--text-primary); }
.domain-capability-desc { font-size: 10px; color: var(--text-muted); line-height: 1.3; }
.domain-intro-footer {
  text-align: center;
  padding: 12px 0 4px;
  border-top: 1px solid var(--border);
  margin-top: 12px;
}
.welcome-hint { font-size: 11px; color: var(--text-muted); }
</style>