<template>
  <div class="doc-selector" ref="selectorRef">
    <!-- Trigger button + inline progress -->
    <div class="doc-trigger-row">
      <n-button size="tiny" secondary @click="open = !open" class="doc-trigger">
        <template #icon><span>📄</span></template>
        文档
        <span class="doc-count" v-if="items.length">({{ items.length }})</span>
      </n-button>
      <!-- Inline progress bar -->
      <div v-if="uploadProgress.active" class="inline-progress">
        <span class="inline-progress-text">{{ uploadProgress.filename }}</span>
        <div class="inline-progress-bar"><div class="inline-progress-fill" :style="{ width: uploadProgress.percent + '%' }" /></div>
        <span class="inline-progress-pct">{{ uploadProgress.percent }}%</span>
      </div>
    </div>

    <!-- Dropdown panel -->
    <Transition name="fade">
      <div v-if="open" class="doc-dropdown">
        <!-- Upload progress -->
        <div v-if="uploadProgress.active" class="dd-upload-progress">
          <span class="dd-upload-filename">{{ uploadProgress.filename }}</span>
          <div class="dd-upload-bar"><div class="dd-upload-fill" :style="{ width: uploadProgress.percent + '%' }" /></div>
          <span class="dd-upload-percent">{{ uploadProgress.percent }}%</span>
        </div>

        <!-- Drop zone hint -->
        <div v-if="isDragOver" class="dd-drop-hint">📂 松开以上传文件</div>

        <!-- Doc list -->
        <div class="dd-list">
          <DocItem
            v-for="doc in items"
            :key="doc.id"
            :doc="doc"
            :processing="processing[doc.id]"
            @delete="$emit('delete-doc', doc.id)"
            @process="$emit('process-doc', doc.id)"
            @preview="$emit('preview-doc', $event)"
          />
          <n-empty v-if="!items.length && !loading" description="暂无文档" class="dd-empty" />
          <div v-if="loading" class="dd-loading"><n-spin size="small" /></div>
        </div>

        <!-- Bottom action: import -->
        <div class="dd-footer">
          <n-button size="tiny" quaternary @click="triggerUpload">
            <template #icon><span>📤</span></template>
            导入文档
          </n-button>
        </div>
      </div>
    </Transition>

    <!-- Hidden file input (always in DOM) -->
    <input type="file" ref="fileInputRef" class="hidden" multiple accept=".pdf,.txt,.md,.csv,.docx" @change="handleFileChange" />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { NButton, NSpin, NEmpty, useMessage } from 'naive-ui'
import type { Document } from '../../api/types'
import DocItem from '../document/DocItem.vue'

const message = useMessage()

const props = defineProps<{
  items: Document[]
  loading: boolean
  processing: Record<string, { stage: string; percent: number }>
  kbId: string | null
}>()

const emit = defineEmits<{
  'delete-doc': [id: string]
  'process-doc': [id: string]
  'preview-doc': [doc: Document]
  'upload-complete': [payload: { docId: string; filename: string }]
}>()

const open = ref(false)
const selectorRef = ref<HTMLElement | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)
const isDragOver = ref(false)

const uploadProgress = reactive({ active: false, filename: '', percent: 0 })

// Close dropdown when clicking outside
watch(open, (val) => {
  if (val) {
    setTimeout(() => {
      const handler = (e: MouseEvent) => {
        if (selectorRef.value && !selectorRef.value.contains(e.target as Node)) {
          open.value = false
          document.removeEventListener('click', handler)
        }
      }
      document.addEventListener('click', handler)
    }, 0)
  }
})

function triggerUpload() {
  fileInputRef.value?.click()
}

function handleFileChange(e: Event) {
  const files = (e.target as HTMLInputElement).files
  if (files?.length) {
    uploadFiles(Array.from(files))
  }
  if (fileInputRef.value) fileInputRef.value.value = ''
}

async function uploadFiles(fileList: File[]) {
  if (!props.kbId) return
  for (const file of fileList) {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase()
    if (!['.pdf', '.txt', '.md', '.csv', '.docx'].includes(ext)) {
      message.error(`不支持: ${ext}`)
      continue
    }
    if (file.size > 10 * 1024 * 1024) {
      message.error(`超过10MB: ${file.name}`)
      continue
    }

    // Duplicate filename check
    const exists = props.items.some((doc) => doc.filename.toLowerCase() === file.name.toLowerCase())
    if (exists) {
      message.warning(`⚠️ "${file.name}" 已存在，请勿重复上传`)
      continue
    }

    uploadProgress.active = true
    uploadProgress.filename = file.name
    uploadProgress.percent = 0

    await new Promise<void>((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      xhr.open('POST', `/api/v1/knowledge-bases/${props.kbId}/upload`)

      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
          uploadProgress.percent = Math.round((e.loaded / e.total) * 100)
        }
      }

      xhr.onload = () => {
        if (xhr.status === 200) {
          message.success(`已上传: ${file.name}`)
          uploadProgress.active = false
          try {
            const data = JSON.parse(xhr.responseText)
            if (data.id) {
              emit('upload-complete', { docId: data.id, filename: data.filename || file.name })
            }
          } catch {}
          resolve()
        } else {
          message.error(`上传失败: ${file.name}`)
          uploadProgress.active = false
          reject()
        }
      }

      xhr.onerror = () => {
        message.error('网络错误')
        uploadProgress.active = false
        reject()
      }

      const formData = new FormData()
      formData.append('file', file)
      xhr.send(formData)
    })
  }
  uploadProgress.active = false
  // Refresh the doc list - parent should watch and refetch
  window.dispatchEvent(new CustomEvent('doc-uploaded'))
}
</script>

<style scoped>
.doc-selector {
  position: relative;
}
.doc-trigger-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.doc-trigger {
  font-size: 12px;
}
.doc-count {
  font-size: 11px;
  color: var(--accent-light);
  font-weight: 600;
  margin-left: 2px;
}
.doc-dropdown {
  position: absolute;
  bottom: calc(100% + 6px);
  left: 0;
  width: 320px;
  max-height: 400px;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
  z-index: 1000;
  overflow: hidden;
}
.dd-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  min-height: 60px;
}
.dd-empty {
  padding: 20px 0;
}
.dd-loading {
  display: flex;
  justify-content: center;
  padding: 20px;
}
.dd-footer {
  flex-shrink: 0;
  padding: 8px;
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: center;
}
.dd-upload-progress {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: var(--bg-input);
  border-bottom: 1px solid var(--border);
  font-size: 11px;
}
.dd-upload-filename {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-primary);
}
.dd-upload-bar {
  width: 80px;
  height: 4px;
  background: var(--border-light);
  border-radius: 2px;
  overflow: hidden;
}
.dd-upload-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), var(--accent-light));
  border-radius: 2px;
  transition: width 0.3s;
}
.dd-upload-percent {
  min-width: 28px;
  text-align: right;
  color: var(--text-muted);
}
.dd-drop-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  border-bottom: 1px dashed var(--accent);
  background: var(--info-bg);
  font-size: 13px;
  color: var(--accent);
}
.hidden { display: none; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.15s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.inline-progress {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--text-secondary);
  flex: 1;
  min-width: 0;
}
.inline-progress-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100px;
}
.inline-progress-bar {
  width: 60px;
  height: 4px;
  background: var(--border-light);
  border-radius: 2px;
  overflow: hidden;
  flex-shrink: 0;
}
.inline-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), var(--accent-light));
  border-radius: 2px;
  transition: width 0.3s;
}
.inline-progress-pct {
  min-width: 28px;
  text-align: right;
  color: var(--text-muted);
}
</style>
