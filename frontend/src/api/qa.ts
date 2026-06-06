import client from './client'
import type { QuestionResponse, ConversationRecord, ConversationSummary } from './types'

export interface QuestionParams {
  document_id?: string
  kb_id?: string
  question: string
  conversation_id?: string
  top_k?: number
  use_hybrid?: boolean
  use_rerank?: boolean
}

export async function askQuestion(params: QuestionParams): Promise<QuestionResponse> {
  const res = await client.post('/qa/ask', params)
  return res.data
}

export async function askQuestionStream(
  params: QuestionParams,
  onToken: (token: string) => void,
  onMeta: (meta: any) => void,
  onDone: () => void,
  onError: (err: Error) => void,
): Promise<void> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 30000)

  let tokenCount = 0
  let metaReceived = false

  try {
    const res = await fetch('/api/v1/qa/ask-stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
      signal: controller.signal,
    })
    clearTimeout(timeoutId)

    if (!res.ok) {
      const text = await res.text().catch(() => '')
      onError(new Error(`HTTP ${res.status}: ${text}`))
      return
    }

    const reader = res.body?.getReader()
    if (!reader) {
      onError(new Error('No response body'))
      return
    }
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (data.type === 'token') {
              tokenCount++
              onToken(data.text)
            } else if (data.type === 'meta') {
              metaReceived = true
              onMeta(data)
            } else if (data.type === 'done') {
              onDone()
              return
            } else if (data.type === 'error') {
              onError(new Error(data.message || 'Stream error'))
              return
            }
          } catch {
            // skip malformed
          }
        }
      }
    }
    onDone()
  } catch (err: any) {
    clearTimeout(timeoutId)
    if (err.name === 'AbortError') {
      onError(new Error('请求超时，请稍后重试'))
    } else {
      onError(err instanceof Error ? err : new Error(String(err)))
    }
  }
}

export async function fetchHistory(
  docId: string,
  conversationId?: string,
): Promise<ConversationRecord[]> {
  const params: Record<string, any> = {}
  if (conversationId) params.conversation_id = conversationId
  const res = await client.get(`/qa/history/${docId}`, { params })
  return res.data.items
}

export async function listConversations(kbId?: string): Promise<ConversationSummary[]> {
  const params: Record<string, any> = {}
  if (kbId) params.kb_id = kbId
  const res = await client.get('/qa/history', { params })
  return res.data.conversations
}

export async function deleteConversation(
  conversationId: string,
): Promise<void> {
  await client.delete(`/qa/conversation/${conversationId}`)
}
