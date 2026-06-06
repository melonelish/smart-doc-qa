<template>
  <div class="chat-container">
    <div class="chat-header">
      <div class="chat-header-info">
        <span class="chat-header-title">{{ headerTitle }}</span>
        <span v-if="headerSub" class="chat-header-sub">{{ headerSub }}</span>
      </div>
    </div>
    <div class="chat-body">
      <!-- Search bar (only when there are messages) -->
      <div v-if="convStore.messages.length" class="chat-search-bar">
        <span class="chat-search-icon">🔍</span>
        <input
          v-model="searchQuery"
          class="chat-search-input"
          type="text"
          placeholder="搜索当前对话内容..."
        />
        <button
          v-if="searchQuery"
          class="chat-search-clear"
          @click="searchQuery = ''"
        >✕</button>
        <span v-if="searchQuery && filteredMessages.length" class="chat-search-count">
          找到 {{ filteredMessages.length }} 条
        </span>
        <span v-else-if="searchQuery && !filteredMessages.length" class="chat-search-count no-match">
          无匹配
        </span>
      </div>
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
        :messages="filteredMessages"
        :streaming="convStore.streaming"
        :highlight="searchQuery"
      />
    </div>
    <!-- Toolbar: docs + actions -->
    <div class="chat-toolbar">
      <div class="chat-toolbar-left">
        <DocumentSelector
          v-if="kbStore.currentKbId"
          :items="docStore.items"
          :loading="docStore.loading"
          :processing="docStore.processingStatus"
          :kb-id="kbStore.currentKbId"
          @delete-doc="handleDeleteDoc"
          @process-doc="handleProcessDoc"
          @preview-doc="handlePreviewDoc"
          @upload-complete="handleUploadComplete"
        />
      </div>
      <div class="chat-toolbar-right">
        <n-button size="tiny" secondary :disabled="!convStore.messages.length" @click="convStore.clear()">
          🗑️ 清空
        </n-button>
        <n-button size="tiny" secondary @click="ui.toggleHistoryPanel()">
          📜 历史
        </n-button>
      </div>
    </div>
    <div class="chat-input-wrapper">
      <MessageInput
        :disabled="!kbStore.currentKbId || convStore.streaming"
        @send="handleSend"
      />
    </div>
  </div>

  <!-- Document Preview Modal -->
  <DocumentPreview
    v-if="previewDoc"
    :doc-id="previewDoc.id"
    :filename="previewDoc.filename"
    :file-type="previewDoc.file_type"
    :file-size="previewDoc.file_size"
    v-model:show="previewVisible"
  />

  <!-- Processing Modal -->
  <ProcessingModal
    v-if="processingModal.show"
    v-model:show="processingModal.show"
    :doc-id="processingModal.docId"
    :filename="processingModal.filename"
    @complete="handleProcessingComplete"
  />
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { NSpace, NButton } from 'naive-ui'
import { useUiStore } from '../../stores/ui'
import { useKnowledgeBaseStore } from '../../stores/knowledgeBase'
import { useDocumentStore } from '../../stores/document'
import { useConversationStore } from '../../stores/conversation'
import { useDomainStore } from '../../stores/domain'
import MessageList from './MessageList.vue'
import MessageInput from './MessageInput.vue'
import DocumentSelector from '../document/DocumentSelector.vue'
import DocumentPreview from '../document/DocumentPreview.vue'
import ProcessingModal from '../document/ProcessingModal.vue'
import type { Document } from '../../api/types'

const ui = useUiStore()
const kbStore = useKnowledgeBaseStore()
const docStore = useDocumentStore()
const convStore = useConversationStore()
const domainStore = useDomainStore()
const domain = domainStore.currentDomain

const searchQuery = ref('')
const previewDoc = ref<Document | null>(null)
const previewVisible = ref(false)
const processingModal = reactive({
  show: false,
  docId: '',
  filename: '',
})

const filteredMessages = computed(() => {
  if (!searchQuery.value) return convStore.messages
  const q = searchQuery.value.toLowerCase().trim()
  return convStore.messages.filter((m) =>
    m.content.toLowerCase().includes(q),
  )
})

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

async function handleDeleteDoc(docId: string) {
  await docStore.remove(docId)
}

async function handleProcessDoc(docId: string) {
  try {
    const res = await fetch(`/api/v1/documents/${docId}/process`, { method: 'POST' })
    if (res.ok) window.$message?.success?.('处理完成')
    else window.$message?.error?.('处理失败')
  } catch (e) {
    window.$message?.error?.('处理异常')
  }
}

function handlePreviewDoc(doc: Document) {
  previewDoc.value = doc
  previewVisible.value = true
}

function handleUploadComplete(payload: { docId: string; filename: string }) {
  processingModal.show = true
  processingModal.docId = payload.docId
  processingModal.filename = payload.filename
}

function handleProcessingComplete() {
  if (kbStore.currentKbId) {
    docStore.fetchByKb(kbStore.currentKbId)
  }
}

// Listen for doc-uploaded event to refresh doc list
function onDocUploaded() {
  if (kbStore.currentKbId) docStore.fetchByKb(kbStore.currentKbId)
}
onMounted(() => window.addEventListener('doc-uploaded', onDocUploaded))
onBeforeUnmount(() => window.removeEventListener('doc-uploaded', onDocUploaded))
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
.chat-input-wrapper {
  flex-shrink: 0;
  background: var(--bg-card);
  border-top: 1px solid var(--border);
  box-shadow: 0 -4px 12px rgba(0,0,0,0.06);
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
.chat-search-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  border-bottom: 1px solid var(--border);
  background: var(--bg-card);
  flex-shrink: 0;
}
.chat-search-icon {
  font-size: 13px;
  flex-shrink: 0;
}
.chat-search-input {
  flex: 1;
  background: var(--bg-input);
  border: 1px solid var(--border);
  outline: none;
  color: var(--text-primary);
  font-size: 13px;
  padding: 6px 10px;
  border-radius: 6px;
  transition: border-color 0.2s;
}
.chat-search-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.12);
}
.chat-search-input::placeholder {
  color: var(--text-muted);
  font-size: 13px;
}
.chat-search-clear {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-muted);
  font-size: 11px;
  padding: 2px 4px;
  border-radius: 3px;
}
.chat-search-clear:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
.chat-search-count {
  font-size: 11px;
  color: var(--accent-light);
  white-space: nowrap;
  font-weight: 600;
}
.chat-search-count.no-match {
  color: var(--warning);
}
.chat-toolbar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  border-top: 1px solid var(--border);
  background: var(--bg-card);
}
.chat-toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.chat-toolbar-right {
  display: flex;
  align-items: center;
  gap: 6px;
}
</style>