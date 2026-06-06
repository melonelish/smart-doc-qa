<template>
  <div
    class="kb-view"
    @dragover.prevent="onDragOver"
    @dragleave.prevent="onDragLeave"
    @drop.prevent="onDrop"
  >
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
import { NButton } from 'naive-ui'
import { useUiStore } from '../stores/ui'
import { useKnowledgeBaseStore } from '../stores/knowledgeBase'
import { useDocumentStore } from '../stores/document'
import { useDomainStore } from '../stores/domain'
import { useConversationStore } from '../stores/conversation'
import type { Document } from '../api/types'
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
    // Load history for this KB
    convStore.loadHistory(kbId)
    router.replace(`/kb/${kbId}`)
  } else {
    docStore.items = []
    convStore.clear()
    convStore.history = []
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
function onDragOver(e: DragEvent) {
  if (e.dataTransfer?.types.includes('Files')) {
    isDragOver.value = true
  }
}

function onDragLeave(e: DragEvent) {
  // Only hide if leaving the panel boundary
  const related = e.relatedTarget as Node | null
  const panel = document.querySelector('.kb-left-panel')
  if (panel && related && !panel.contains(related)) {
    isDragOver.value = false
  }
}

async function onDrop(e: DragEvent) {
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

// Remove old manual DOM event listeners
// (now using Vue template @dragover/@dragleave/@drop instead)

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
.drop-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(99, 102, 241, 0.08);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}
.drop-overlay-content {
  background: var(--bg-card);
  border: 2px dashed var(--accent);
  border-radius: 16px;
  padding: 40px 60px;
  text-align: center;
  box-shadow: 0 8px 32px rgba(0,0,0,0.12);
}
.drop-overlay-icon { font-size: 48px; margin-bottom: 12px; }
.drop-overlay-text { font-size: 18px; color: var(--accent); font-weight: 600; }
.floating-progress {
  position: fixed;
  bottom: 20px;
  right: 20px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 10px 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
  z-index: 999;
  min-width: 200px;
}
.fp-filename { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--text-primary); }
.fp-bar { width: 80px; height: 4px; background: var(--border-light); border-radius: 2px; overflow: hidden; }
.fp-fill { height: 100%; background: linear-gradient(90deg, var(--accent), var(--accent-light)); border-radius: 2px; transition: width 0.3s; }
.fp-percent { min-width: 28px; text-align: right; color: var(--text-muted); }
</style>
