<template>
  <div class="kb-view">
    <!-- Left: Documents -->
    <div class="kb-left-panel">
      <n-card size="small" :bordered="true" class="doc-card">
        <template #header>
          <div class="doc-header">
            <span class="doc-title">📋 文档</span>
            <n-tag v-if="kbStore.currentKb" type="primary" size="small" :bordered="false" round>
              {{ kbStore.currentKb.name }}
            </n-tag>
          </div>
        </template>
        <template #header-extra>
          <n-space :size="6">
            <n-button size="tiny" type="primary" @click="ui.createKBModalOpen = true">
              ＋ 新建
            </n-button>
            <n-button size="tiny" type="info" @click="triggerUpload" :disabled="!kbStore.currentKbId">
              上传
            </n-button>
          </n-space>
        </template>

        <input type="file" ref="fileInputRef" class="hidden" multiple :accept="acceptStr" @change="handleFileChange" />

        <!-- Upload progress -->
        <div v-if="uploadProgress.active" class="upload-progress">
          <span class="upload-filename">{{ uploadProgress.filename }}</span>
          <div class="upload-bar">
            <div class="upload-fill" :style="{ width: uploadProgress.percent + '%' }" />
          </div>
          <span class="upload-percent">{{ uploadProgress.percent }}%</span>
        </div>

        <!-- Drop zone hint -->
        <div v-if="isDragOver" class="drop-hint">
          📂 松开以上传文件到知识库
        </div>

        <DocList
          :items="docStore.items"
          :loading="docStore.loading"
          :processing="docStore.processingStatus"
          @delete-doc="handleDeleteDoc"
          @process-doc="handleProcessDoc"
          @preview-doc="handlePreviewDoc"
        />
      </n-card>
    </div>

    <!-- Right: Domain Intro + Chat -->
    <div class="kb-right-panel">
      <ChatPanel />
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
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NCard, NButton, NSpace } from 'naive-ui'
import { useUiStore } from '../stores/ui'
import { useKnowledgeBaseStore } from '../stores/knowledgeBase'
import { useDocumentStore } from '../stores/document'
import { useDomainStore } from '../stores/domain'
import { useConversationStore } from '../stores/conversation'
import type { Document } from '../api/types'
import DocList from '../components/document/DocList.vue'
import ChatPanel from '../components/chat/ChatPanel.vue'
import DocumentPreview from '../components/document/DocumentPreview.vue'
import ProcessingModal from '../components/document/ProcessingModal.vue'

const ui = useUiStore()
const kbStore = useKnowledgeBaseStore()
const docStore = useDocumentStore()
const domainStore = useDomainStore()
const convStore = useConversationStore()
const route = useRoute()
const router = useRouter()
const fileInputRef = ref<HTMLInputElement | null>(null)
const acceptStr = '.pdf,.txt,.md,.csv,.docx'

// Drag & Drop state
const isDragOver = ref(false)

// Upload progress state
const uploadProgress = reactive({
  active: false,
  filename: '',
  percent: 0,
})

// Document preview state
const previewDoc = ref<Document | null>(null)
const previewVisible = ref(false)

// Processing modal state
const processingModal = reactive({
  show: false,
  docId: '',
  filename: '',
})

// Auto-refresh timer for documents in processing state
let refreshTimer: ReturnType<typeof setInterval> | null = null

function startRefreshTimer() {
  stopRefreshTimer()
  refreshTimer = setInterval(async () => {
    const hasProcessing = docStore.items.some(d => d.status === 'processing' || d.status === 'uploaded')
    if (hasProcessing && kbStore.currentKbId) {
      await docStore.fetchByKb(kbStore.currentKbId)
    } else {
      stopRefreshTimer()
    }
  }, 3000)
}

function stopRefreshTimer() {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// Watch doc items: start polling when any doc is processing
watch(() => docStore.items, (items) => {
  const hasProcessing = items.some(d => d.status === 'processing' || d.status === 'uploaded')
  if (hasProcessing && !refreshTimer) {
    startRefreshTimer()
  } else if (!hasProcessing && refreshTimer) {
    stopRefreshTimer()
  }
}, { deep: true })

onBeforeUnmount(() => {
  stopRefreshTimer()
})

// Sync route param → store on mount
onMounted(async () => {
  await kbStore.fetchList(domainStore.current)
  const kbId = route.params.kbId as string
  if (kbId && kbStore.list.some((kb) => kb.id === kbId)) {
    kbStore.currentKbId = kbId
  }
})

// Watch KB selection → load docs + save/load conversation
watch(() => kbStore.currentKbId, async (kbId, oldKbId) => {
  // Save current conversation before switching
  if (oldKbId && oldKbId !== kbId) {
    convStore.save()
  }

  if (kbId) {
    await docStore.fetchByKb(kbId)
    // Load this KB's conversation from storage
    const loaded = convStore.loadFromStorage(kbId)
    if (!loaded) {
      convStore.clear()
    }
    router.replace(`/kb/${kbId}`)
  } else {
    docStore.items = []
    convStore.clear()
  }
})

// Watch domain changes → reload KB list
watch(() => domainStore.current, async () => {
  await kbStore.fetchList(domainStore.current)
  if (!kbStore.currentKbId || !kbStore.list.some((kb) => kb.id === kbStore.currentKbId)) {
    kbStore.currentKbId = null
  }
})

async function loadDocs() {
  if (kbStore.currentKbId) {
    await docStore.fetchByKb(kbStore.currentKbId)
  }
}

function triggerUpload() {
  fileInputRef.value?.click()
}

function resetUploadProgress() {
  uploadProgress.active = false
  uploadProgress.filename = ''
  uploadProgress.percent = 0
}

async function handleFileChange(e: Event) {
  const files = (e.target as HTMLInputElement).files
  if (!files?.length || !kbStore.currentKbId) return
  
  const allowedExts = ['.pdf', '.txt', '.md', '.csv', '.docx']
  const maxSize = 10 * 1024 * 1024 // 10MB
  
  for (const file of Array.from(files)) {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase()
    if (!allowedExts.includes(ext)) {
      window.$message?.error?.(`不支持的文件类型: ${ext}`)
      continue
    }
    if (file.size === 0) {
      window.$message?.error?.(`空文件不允许上传: ${file.name}`)
      continue
    }
    if (file.size > maxSize) {
      window.$message?.error?.(`文件超过10MB限制: ${file.name}`)
      continue
    }
    try {
      await uploadFileWithProgress(file, kbStore.currentKbId)
    } catch (err: any) {
      console.error('Upload failed:', err)
    }
  }
  // Reset file input
  if (fileInputRef.value) fileInputRef.value.value = ''
  await loadDocs()
}

async function uploadFileWithProgress(file: File, kbId: string): Promise<{ id: string; filename: string } | null> {
  uploadProgress.active = true
  uploadProgress.filename = file.name
  uploadProgress.percent = 0

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('POST', `/api/v1/knowledge-bases/${kbId}/upload`)

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        uploadProgress.percent = Math.round((e.loaded / e.total) * 100)
      }
    }

    xhr.onload = () => {
      resetUploadProgress()
      if (xhr.status === 200) {
        try {
          const data = JSON.parse(xhr.responseText)
          window.$message?.success?.(`已上传: ${file.name}`)
          // Open processing modal to track auto-processing progress
          processingModal.show = true
          processingModal.docId = data.id
          processingModal.filename = data.filename
          resolve({ id: data.id, filename: data.filename })
        } catch (e) {
          resolve(null)
        }
      } else {
        let detail = '上传失败'
        try { detail = JSON.parse(xhr.responseText).detail || '上传失败' } catch(e) {}
        window.$message?.error?.(`上传失败: ${detail}`)
        reject(new Error(detail))
      }
    }

    xhr.onerror = () => {
      resetUploadProgress()
      window.$message?.error?.('网络错误')
      reject(new Error('Network error'))
    }

    const formData = new FormData()
    formData.append('file', file)
    xhr.send(formData)
  })
}

// ─── Drag & Drop ───
function handleDragOver(e: DragEvent) {
  e.preventDefault()
  isDragOver.value = true
}

function handleDragLeave() {
  isDragOver.value = false
}

async function handleDrop(e: DragEvent) {
  e.preventDefault()
  isDragOver.value = false

  if (!kbStore.currentKbId) {
    window.$message?.warning?.('请先选择知识库')
    return
  }

  const files = e.dataTransfer?.files
  if (!files?.length) return

  const allowedExts = ['.pdf', '.txt', '.md', '.csv', '.docx']
  const maxSize = 10 * 1024 * 1024

  for (const file of Array.from(files)) {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase()
    if (!allowedExts.includes(ext)) {
      window.$message?.error?.(`不支持的文件类型: ${ext}`)
      continue
    }
    if (file.size === 0) {
      window.$message?.error?.(`空文件不允许上传: ${file.name}`)
      continue
    }
    if (file.size > maxSize) {
      window.$message?.error?.(`文件超过10MB限制: ${file.name}`)
      continue
    }
    try {
      await uploadFileWithProgress(file, kbStore.currentKbId)
    } catch (err: any) {
      console.error('Upload failed:', err)
    }
  }
  await loadDocs()
}

// Setup drag & drop on the doc card element
onMounted(() => {
  // After Vue mounts, find the .doc-card element and attach drag listeners
  const card = document.querySelector('.doc-card .n-card__content') as HTMLElement
  if (card) {
    card.addEventListener('dragover', handleDragOver)
    card.addEventListener('dragleave', handleDragLeave)
    card.addEventListener('drop', handleDrop)
  }
})

onBeforeUnmount(() => {
  const card = document.querySelector('.doc-card .n-card__content') as HTMLElement
  if (card) {
    card.removeEventListener('dragover', handleDragOver)
    card.removeEventListener('dragleave', handleDragLeave)
    card.removeEventListener('drop', handleDrop)
  }
})

// ─── Document Preview ───
function handlePreviewDoc(doc: Document) {
  previewDoc.value = doc
  previewVisible.value = true
}

// ─── Processing ───
async function handleProcessDoc(docId: string) {
  const doc = docStore.items.find(d => d.id === docId)
  if (!doc) return

  processingModal.show = true
  processingModal.docId = docId
  processingModal.filename = doc.filename

  try {
    const resp = await fetch(`/api/v1/documents/${docId}/process`, { method: 'POST' })
    if (resp.ok) {
      const data = await resp.json()
      // If WS didn't complete yet, handle manually
      if (!processingModal.show) {
        window.$message?.success?.(`✅ 处理完成 (${data.chunk_count} 个分块)`)
        await loadDocs()
      }
    } else {
      processingModal.show = false
      const err = await resp.json()
      window.$message?.error?.(`处理失败: ${err.detail || '未知错误'}`)
      await loadDocs()
    }
  } catch (e: any) {
    processingModal.show = false
    window.$message?.error?.('处理异常: ' + e.message)
    await loadDocs()
  }
}

function handleProcessingComplete(payload: { chunk_count: number }) {
  window.$message?.success?.(`✅ 处理完成 (${payload.chunk_count} 个分块)`)
  loadDocs()
}

async function handleDeleteDoc(docId: string) {
  await docStore.remove(docId)
}
</script>

<style scoped>
.kb-view {
  display: flex;
  flex-direction: row;
  height: 100%;
  gap: 16px;
}
.kb-left-panel {
  width: 300px;
  min-width: 260px;
  display: flex;
  flex-direction: column;
  height: 100%;
}
.kb-left-panel :deep(.n-card) {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.kb-left-panel :deep(.n-card__content) {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  min-height: 0;
}
.kb-right-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  height: 100%;
}
.hidden {
  display: none;
}
.upload-progress {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  margin-bottom: 8px;
  background: var(--bg-input);
  border-radius: var(--radius-sm);
}
.upload-filename {
  font-size: 12px;
  color: var(--text-primary);
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.upload-bar {
  width: 120px;
  height: 4px;
  background: var(--border-light);
  border-radius: 2px;
  overflow: hidden;
}
.upload-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), var(--accent-light));
  border-radius: 2px;
  transition: width 0.3s ease;
}
.upload-percent {
  font-size: 11px;
  color: var(--text-muted);
  min-width: 32px;
  text-align: right;
}
.drop-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  margin-bottom: 8px;
  border: 2px dashed var(--accent);
  border-radius: var(--radius-sm);
  background: var(--info-bg);
  font-size: 14px;
  color: var(--accent);
}
.doc-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.doc-title {
  font-weight: 600;
  font-size: 14px;
}
</style>
