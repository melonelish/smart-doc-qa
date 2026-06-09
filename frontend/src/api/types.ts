/* ── Domain ── */
export interface DomainDefinition {
  id: string
  name: string
  icon: string
  description: string
  features: { q: string; a: string }[]
  docTypes: { icon: string; name: string; desc: string }[]
  capabilities: { icon: string; label: string; desc: string }[]
}

/* ── Knowledge Base ── */
export interface KnowledgeBase {
  id: string
  name: string
  description: string
  domain: string
  document_count: number
  created_at: string
  updated_at: string
}

/* ── Document ── */
export type DocumentStatus = 'uploaded' | 'processing' | 'ready' | 'failed'

export interface Document {
  id: string
  filename: string
  file_type: string
  file_size: number
  status: DocumentStatus
  chunk_count?: number
  error_message?: string
  created_at: string
  updated_at?: string
}

/* ── QA ── */
export interface SourceChunk {
  chunk_index: number
  page: string
  snippet: string
}

export interface SourceDetail {
  source: string
  chunks: SourceChunk[]
}

export interface ToolLogEntry {
  tool: string
  args: Record<string, any>
  result: string
}

export interface QuestionResponse {
  question: string
  conversation_id: string
  answer: string
  sources: string[]
  source_details: SourceDetail[]
  source_count: number
  retrieval_method: string
  tool_log: ToolLogEntry[]
}

export interface ConversationRecord {
  id: string
  conversation_id: string
  role: string
  content: string
  sources?: string[]
  created_at: string
}

/* ── History ── */
export interface ConversationSummary {
  conversation_id: string
  document_id: string
  started_at: string
  last_activity_at: string
  message_count: number
  first_question: string
  last_question: string
}

/* ── Model Config ── */
export interface ModelConfigOut {
  id: string
  name: string
  provider: string
  base_url: string
  api_key_masked: string
  model_name: string
  is_active: boolean
  created_at: string
}

export interface PresetProvider {
  key: string
  label: string
  base_url: string
  model_name: string
}
