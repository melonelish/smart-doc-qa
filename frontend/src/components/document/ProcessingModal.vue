<template>
  <n-modal
    :show="show"
    preset="card"
    style="width: 420px; max-width: 90vw"
    :mask-closable="false"
    class="processing-modal"
    @update:show="$emit('update:show', false)"
  >
    <div class="processing-content">
      <div class="processing-icon">{{ icon }}</div>
      <h3 class="processing-title">{{ title }}</h3>
      <p class="processing-filename">{{ filename }}</p>

      <div class="processing-stages">
        <div
          v-for="stage in stages"
          :key="stage.key"
          :class="['stage', stageStatus(stage.key)]"
        >
          <span class="stage-icon">{{ stageIcon(stage.key) }}</span>
          <span class="stage-text">{{ stage.label }}</span>
        </div>
      </div>

      <div class="processing-progress-bar">
        <div class="processing-progress-fill" :style="{ width: percent + '%' }" />
      </div>

      <p class="processing-hint">处理速度取决于文档大小和 AI 服务响应时间</p>

      <n-button
        v-if="percent >= 100 || percent <= 0 || timedOut"
        size="small"
        type="primary"
        style="margin-top: 12px"
        @click="$emit('update:show', false)"
      >
        关闭
      </n-button>
    </div>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import { NModal, NButton } from 'naive-ui'

const props = defineProps<{
  show: boolean
  filename: string
  docId: string
  error?: boolean
}>()

const emit = defineEmits<{
  'update:show': [value: boolean]
  'complete': [payload: { chunk_count: number }]
}>()

const stages = [
  { key: 'read', label: '读取文件内容', threshold: 10 },
  { key: 'split', label: '智能文本分割', threshold: 30 },
  { key: 'embed', label: 'AI 向量嵌入', threshold: 50 },
  { key: 'store', label: '构建检索索引', threshold: 80 },
]

const percent = ref(0)
const completedStages = ref<Set<string>>(new Set())
const activeStage = ref<string | null>(null)
const ws = ref<WebSocket | null>(null)
const timedOut = ref(false)
let autoCloseTimer: ReturnType<typeof setTimeout> | null = null
let pollTimer: ReturnType<typeof setInterval> | null = null

const title = computed(() => {
  if (timedOut.value && percent.value < 100) return '⚠️ 等待处理中...'
  if (props.error) return '❌ 处理失败'
  if (percent.value >= 100) return '✅ 处理完成'
  return '正在处理文档...'
})

const icon = computed(() => {
  if (timedOut.value && percent.value < 100) return '⏳'
  if (props.error) return '❌'
  if (percent.value >= 100) return '✅'
  return '⚙️'
})

function stageStatus(key: string): string {
  if (completedStages.value.has(key)) return 'done'
  if (activeStage.value === key) return 'active'
  return 'pending'
}

function stageIcon(key: string): string {
  if (completedStages.value.has(key)) return '✓'
  if (activeStage.value === key) return '◉'
  return '○'
}

function updateStages(pct: number) {
  completedStages.value = new Set()
  activeStage.value = null
  for (const stage of stages) {
    if (pct >= stage.threshold + 20 || pct >= 100) {
      completedStages.value.add(stage.key)
    } else if (pct >= stage.threshold) {
      activeStage.value = stage.key
      break
    }
  }
}

function handleProgressComplete() {
  if (autoCloseTimer) return
  autoCloseTimer = setTimeout(() => {
    emit('complete', { chunk_count: 0 })
    emit('update:show', false)
  }, 800)
}

async function checkDocumentStatus(docId: string) {
  try {
    const resp = await fetch(`/api/v1/documents/${docId}`)
    if (!resp.ok) return null
    return await resp.json()
  } catch {
    return null
  }
}

function startPolling(docId: string) {
  stopPolling()
  let elapsed = 0
  pollTimer = setInterval(async () => {
    elapsed += 2000
    const doc = await checkDocumentStatus(docId)
    if (doc) {
      if (doc.status === 'ready') {
        percent.value = 100
        updateStages(100)
        stopPolling()
        handleProgressComplete()
      } else if (doc.status === 'failed') {
        percent.value = 0
        updateStages(0)
        timedOut.value = true
        stopPolling()
        // Close modal after showing error briefly
        setTimeout(() => {
          emit('update:show', false)
        }, 2000)
      } else if (doc.status === 'processing' && percent.value === 0) {
        // No WS progress yet but doc is actually processing — nudge UI
        activeStage.value = 'read'
      }
    }
    if (elapsed >= 30000 && percent.value < 100) {
      timedOut.value = true
    }
  }, 2000)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function connectWS(docId: string) {
  disconnectWS()

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const url = `${protocol}//${window.location.host}/ws/progress/${docId}`
  const socket = new WebSocket(url)
  ws.value = socket
  let wsConnected = false

  socket.onopen = () => {
    wsConnected = true
  }

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.type === 'progress') {
        percent.value = Math.min(data.percent, 100)
        updateStages(percent.value)
        stopPolling()

        if (percent.value >= 100) {
          handleProgressComplete()
        }
      }
    } catch {
      // ignore
    }
  }

  socket.onerror = () => {
    wsConnected = false
    // Fall back to polling if WebSocket fails
    startPolling(docId)
  }

  socket.onclose = () => {
    ws.value = null
    // If WS closed before completion and we haven't timed out, resume polling
    if (percent.value < 100 && !timedOut.value) {
      startPolling(docId)
    }
  }

  // Fallback: if WS doesn't connect within 3s, start polling anyway
  setTimeout(() => {
    if (!wsConnected && percent.value < 100 && !timedOut.value) {
      startPolling(docId)
    }
  }, 3000)
}

function disconnectWS() {
  if (autoCloseTimer) {
    clearTimeout(autoCloseTimer)
    autoCloseTimer = null
  }
  stopPolling()
  if (ws.value) {
    ws.value.close()
    ws.value = null
  }
}

watch(
  () => props.show,
  async (val) => {
    if (val && props.docId) {
      percent.value = 0
      completedStages.value = new Set()
      activeStage.value = null
      timedOut.value = false

      // Immediate status check — if already done, close right away
      const doc = await checkDocumentStatus(props.docId)
      if (doc?.status === 'ready') {
        percent.value = 100
        updateStages(100)
        handleProgressComplete()
        return
      } else if (doc?.status === 'failed') {
        percent.value = 0
        updateStages(0)
        timedOut.value = true
        return
      }

      connectWS(props.docId)
      startPolling(props.docId)
    } else {
      disconnectWS()
    }
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  disconnectWS()
})

defineExpose({ start: connectWS })
</script>

<style scoped>
.processing-content {
  text-align: center;
}

.processing-icon {
  font-size: 40px;
  margin-bottom: 12px;
}

.processing-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 4px;
  color: var(--text-primary);
}

.processing-filename {
  font-size: 13px;
  color: var(--accent-light);
  margin: 0 0 20px;
  word-break: break-all;
}

.processing-stages {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.stage {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: var(--text-muted);
  transition: var(--transition);
  padding: 6px 8px;
  border-radius: 6px;
}

.stage.active {
  color: var(--accent-light);
  background: var(--info-bg);
}

.stage.active .stage-icon {
  animation: pulse 1.5s ease-in-out infinite;
}

.stage.done {
  color: var(--success);
}

.stage .stage-icon {
  width: 20px;
  text-align: center;
  font-size: 14px;
}

.processing-progress-bar {
  height: 4px;
  background: var(--bg-input);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 12px;
}

.processing-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), var(--accent-light));
  border-radius: 2px;
  transition: width 0.5s ease;
}

.processing-hint {
  font-size: 11px;
  color: var(--text-muted);
  margin: 0;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
