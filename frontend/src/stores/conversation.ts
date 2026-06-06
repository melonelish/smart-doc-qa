import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ConversationSummary, ToolLogEntry, SourceDetail } from '../api/types'
import * as qaApi from '../api/qa'

let _msgId = 0
function nextMsgId() {
  return 'm' + Date.now() + '_' + (_msgId++)
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: string[]
  sourceDetails?: SourceDetail[]
  toolLog?: ToolLogEntry[]
  retrievalMethod?: string
  timestamp: number
}

const STORAGE_PREFIX = 'smartdocqa_conv_'

function _storageKey(kbId: string) {
  return STORAGE_PREFIX + kbId
}

export const useConversationStore = defineStore('conversation', () => {
  const messages = ref<Message[]>([])
  const conversationId = ref<string | null>(null)
  const currentKbId = ref<string | null>(null)
  const streaming = ref(false)
  const history = ref<ConversationSummary[]>([])
  const loadingHistory = ref(false)

  function addMessage(msg: Message) {
    messages.value.push(msg)
  }

  function updateLastMessage(content: string) {
    const last = messages.value[messages.value.length - 1]
    if (last && last.role === 'assistant') {
      last.content = content
    }
  }

  function appendToLastMessage(text: string) {
    const idx = messages.value.length - 1
    const last = messages.value[idx]
    if (last && last.role === 'assistant') {
      messages.value[idx] = { ...last, content: last.content + text }
    }
  }

  function updateLastAssistant(updates: Partial<Message>) {
    const idx = messages.value.length - 1
    const last = messages.value[idx]
    if (last && last.role === 'assistant') {
      messages.value[idx] = { ...last, ...updates }
    }
  }

  function save() {
    if (!currentKbId.value || messages.value.length === 0) return
    const data = {
      conversationId: conversationId.value,
      messages: messages.value,
      savedAt: new Date().toISOString(),
    }
    try {
      sessionStorage.setItem(_storageKey(currentKbId.value), JSON.stringify(data))
    } catch (e) { console.warn('save failed:', e) }
  }

  function loadFromStorage(kbId: string) {
    try {
      const raw = sessionStorage.getItem(_storageKey(kbId))
      if (!raw) return false
      const data = JSON.parse(raw)
      conversationId.value = data.conversationId
      messages.value = (data.messages || []).map((m: any) => ({
        id: m.id || nextMsgId(),
        role: m.role,
        content: m.content,
        sources: m.sources,
        sourceDetails: m.sourceDetails,
        toolLog: m.toolLog,
        retrievalMethod: m.retrievalMethod,
        timestamp: m.timestamp,
      }))
      currentKbId.value = kbId
      return true
    } catch { return false }
  }

  function clearSaved(kbId?: string) {
    const id = kbId || currentKbId.value
    if (id) sessionStorage.removeItem(_storageKey(id))
  }

  async function sendQuestion(params: qaApi.QuestionParams) {
    if (params.kb_id) currentKbId.value = params.kb_id
    streaming.value = true

    // Clean up any empty assistant messages from previous failed requests
    messages.value = messages.value.filter(
      (m) => !(m.role === 'assistant' && m.content === '')
    )

    const userMsg: Message = {
      id: nextMsgId(),
      role: 'user',
      content: params.question,
      timestamp: Date.now(),
    }
    addMessage(userMsg)

    const assistantMsg: Message = {
      id: nextMsgId(),
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
    }
    addMessage(assistantMsg)

    const payload: qaApi.QuestionParams = {
      ...params,
      conversation_id: conversationId.value || undefined,
      top_k: 4,
      use_hybrid: true,
      use_rerank: true,
    }

    try {
      await qaApi.askQuestionStream(
        payload,
        (token) => appendToLastMessage(token),
        (meta) => {
          conversationId.value = meta.conversation_id
          updateLastAssistant({
            sources: meta.sources,
            sourceDetails: meta.source_details,
            toolLog: meta.tool_log,
            retrievalMethod: meta.retrieval_method,
          })
        },
        () => { 
          streaming.value = false
          save()
          // 刷新历史记录
          loadHistory()
        },
        (err) => {
          streaming.value = false
          updateLastAssistant({ content: '❌ 请求失败：' + (err.message || '未知错误') })
        },
      )
    } catch (err: any) {
      streaming.value = false
      updateLastAssistant({ content: '❌ 请求失败：' + (err?.message || '未知错误') })
    }
  }

  async function loadHistory(kbId?: string) {
    loadingHistory.value = true
    try {
      const id = kbId || currentKbId.value || undefined
      history.value = await qaApi.listConversations(id)
    } finally {
      loadingHistory.value = false
    }
  }

  async function restoreConversation(convId: string, docId: string) {
    conversationId.value = convId
    const records = await qaApi.fetchHistory(docId, convId)
    messages.value = records.map((r) => ({
      id: nextMsgId(),
      role: r.role as 'user' | 'assistant',
      content: r.content,
      sources: r.sources,
      timestamp: new Date(r.created_at).getTime(),
    }))
  }

  async function removeConversation(convId: string) {
    await qaApi.deleteConversation(convId)
    history.value = history.value.filter((h) => h.conversation_id !== convId)
    if (conversationId.value === convId) {
      clear()
    }
  }

  function clear() {
    save()
    messages.value = []
    conversationId.value = null
  }

  return {
    messages, conversationId, currentKbId, streaming, history, loadingHistory,
    addMessage, updateLastMessage, appendToLastMessage,
    sendQuestion, loadHistory, restoreConversation,
    removeConversation, clear, save, loadFromStorage, clearSaved,
  }
})
