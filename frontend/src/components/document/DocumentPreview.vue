<template>
  <n-modal
    v-model:show="modalShow"
    preset="card"
    :title="filename"
    style="width: 85vw; max-width: 1100px;"
    :segmented="{ content: 'soft' }"
    @update:show="onClose"
  >
    <template #header-extra>
      <n-button
        text
        size="medium"
        @click="handleDownload"
        class="download-btn"
      >
        <template #icon><span style="font-size: 16px">⬇️</span></template>
        下载
      </n-button>
    </template>

    <n-spin :show="loading">
      <!-- Markdown preview -->
      <div v-if="isMd && contentText" class="markdown-preview" v-html="renderedMarkdown"></div>

      <!-- Text preview -->
      <pre v-else-if="isText && contentText" class="text-preview">{{ contentText }}</pre>

      <!-- CSV preview -->
      <div v-else-if="isCsv && csvRows.length" class="csv-preview">
        <table class="csv-table">
          <thead>
            <tr>
              <th v-for="(header, idx) in csvRows[0]" :key="idx">{{ header }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, rIdx) in csvRows.slice(1)" :key="rIdx">
              <td v-for="(cell, cIdx) in row" :key="cIdx">{{ cell }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- PDF preview -->
      <iframe
        v-else-if="isPdf"
        :src="pdfUrl"
        class="pdf-preview"
      ></iframe>

      <!-- Empty state while loading or after load with no content -->
      <div v-else-if="!loading" class="unsupported-preview">
        <p v-if="!isMd && !isText && !isCsv && !isPdf">此格式暂不支持在线预览</p>
        <p v-else-if="loadError">内容加载失败</p>
        <p v-else>加载中…</p>
      </div>
    </n-spin>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { NModal, NButton, NSpin } from 'naive-ui'
import { marked } from 'marked'

const props = defineProps<{
  docId: string
  filename: string
  fileType: string
  fileSize: number
  show: boolean
}>()

const emit = defineEmits<{
  'update:show': [value: boolean]
}>()

const loading = ref(false)
const contentText = ref('')
const csvRows = ref<string[][]>([])
const loadError = ref(false)

const modalShow = computed({
  get: () => props.show,
  set: (val: boolean) => emit('update:show', val)
})

const renderedMarkdown = computed(() => {
  if (!contentText.value) return ''
  const text = contentText.value.length > 50000
    ? contentText.value.slice(0, 50000) + '\n\n…（内容过长，已截断）'
    : contentText.value
  return String(marked.parse(text))
})

const pdfUrl = computed(() => `/api/v1/documents/${props.docId}/file`)

// Normalize fileType: backend may store '.md' or 'md'
const normalizedType = computed(() => {
  const t = props.fileType || ''
  return t.startsWith('.') ? t : `.${t}`
})
const isMd = computed(() => normalizedType.value === '.md')
const isText = computed(() => normalizedType.value === '.txt')
const isCsv = computed(() => normalizedType.value === '.csv')
const isPdf = computed(() => normalizedType.value === '.pdf')

function onClose(val: boolean) {
  if (!val) {
    emit('update:show', false)
  }
}

function parseCSV(text: string): string[][] {
  const rows: string[][] = []
  const lines = text.split(/\r?\n/)
  for (const line of lines) {
    if (!line.trim()) continue
    const cells: string[] = []
    let current = ''
    let inQuotes = false
    for (let i = 0; i < line.length; i++) {
      const ch = line[i]
      if (ch === '"') {
        if (inQuotes && line[i + 1] === '"') {
          current += '"'
          i++
        } else {
          inQuotes = !inQuotes
        }
      } else if (ch === ',' && !inQuotes) {
        cells.push(current.trim())
        current = ''
      } else {
        current += ch
      }
    }
    cells.push(current.trim())
    rows.push(cells)
    if (rows.length >= 200) break
  }
  return rows
}

async function fetchData() {
  if (!props.show || !props.docId) return
  loading.value = true
  contentText.value = ''
  csvRows.value = []
  loadError.value = false

  try {
    const resp = await fetch(`/api/v1/documents/${props.docId}/content`)
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    const text = await resp.text()

    if (props.fileType === '.csv' || normalizedType.value === '.csv') {
      csvRows.value = parseCSV(text)
    } else {
      contentText.value = text
    }
  } catch (err) {
    console.error('[DocumentPreview] Fetch failed:', err)
    loadError.value = true
  } finally {
    loading.value = false
  }
}

watch(() => props.show, (val) => {
  if (val && props.docId) fetchData()
}, { immediate: true })

function handleDownload() {
  const url = `/api/v1/documents/${props.docId}/file`
  const a = document.createElement('a')
  a.href = url
  a.download = props.filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}
</script>

<style scoped>
.download-btn {
  color: var(--text-primary, #333);
  padding: 4px 8px;
  border-radius: 4px;
  transition: background 0.2s;
}
.download-btn:hover {
  background: var(--bg-input-hover, rgba(0,0,0,0.05));
}

.markdown-preview {
  max-height: 70vh;
  overflow-y: auto;
  padding: 16px 20px;
  line-height: 1.7;
  font-size: 14px;
  color: var(--text-primary, #1f2937);
  background: var(--bg-input, #fff);
  border-radius: 6px;
}
.markdown-preview :deep(h1),
.markdown-preview :deep(h2),
.markdown-preview :deep(h3) {
  margin-top: 1em;
  margin-bottom: 0.5em;
  font-weight: 600;
}
.markdown-preview :deep(p) {
  margin-bottom: 0.75em;
}
.markdown-preview :deep(pre) {
  background: var(--bg-code, #f5f5f5);
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
}
.markdown-preview :deep(code) {
  background: var(--bg-code, #f5f5f5);
  padding: 2px 4px;
  border-radius: 3px;
  font-size: 0.9em;
}
.markdown-preview :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 1em 0;
}
.markdown-preview :deep(th),
.markdown-preview :deep(td) {
  border: 1px solid var(--border-light, #e5e7eb);
  padding: 6px 10px;
  text-align: left;
}
.markdown-preview :deep(th) {
  background: var(--bg-header, #f9fafb);
  font-weight: 600;
}

.text-preview {
  max-height: 70vh;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
  padding: 16px 20px;
  font-family: 'Menlo', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-primary, #1f2937);
  background: var(--bg-input, #fff);
  border-radius: 6px;
  margin: 0;
}

.csv-preview {
  max-height: 70vh;
  overflow: auto;
  border-radius: 6px;
  background: var(--bg-input, #fff);
}
.csv-table {
  border-collapse: collapse;
  width: 100%;
  font-size: 13px;
}
.csv-table th,
.csv-table td {
  border: 1px solid var(--border-light, #e5e7eb);
  padding: 6px 10px;
  text-align: left;
  white-space: nowrap;
}
.csv-table th {
  background: var(--bg-header, #f3f4f6);
  font-weight: 600;
  position: sticky;
  top: 0;
  z-index: 1;
}
.csv-table tr:hover {
  background: var(--bg-row-hover, #f9fafb);
}

.pdf-preview {
  width: 100%;
  height: 70vh;
  border: none;
  border-radius: 6px;
}

.unsupported-preview {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  color: var(--text-muted, #9ca3af);
  font-size: 15px;
}
</style>
