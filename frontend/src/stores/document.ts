import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import type { Document, DocumentStatus } from '../api/types'
import * as docApi from '../api/document'

export const useDocumentStore = defineStore('document', () => {
  const items = ref<Document[]>([])
  const loading = ref(false)
  const uploadProgress = ref(0)
  const processingStatus = reactive<Record<string, { stage: string; percent: number }>>({})

  async function fetchByKb(kbId: string) {
    loading.value = true
    try {
      items.value = await docApi.fetchKBDocuments(kbId)
    } finally {
      loading.value = false
    }
  }

  async function upload(file: File, kbId?: string) {
    uploadProgress.value = 0
    const result = await docApi.uploadFile(file, kbId)
    items.value.unshift({
      id: result.id,
      filename: result.filename,
      file_type: result.file_type,
      file_size: result.file_size,
      status: result.status as DocumentStatus,
      created_at: result.created_at,
    })
    uploadProgress.value = 100
    return result
  }

  async function process(docId: string) {
    processingStatus[docId] = { stage: 'processing', percent: 0 }
    await docApi.processDocument(docId)
    // Do NOT mark as ready here — the backend processes asynchronously.
    // The document status will be updated via WebSocket or polling.
  }

  async function remove(docId: string) {
    // Optimistic removal: update UI immediately, rollback on failure
    const idx = items.value.findIndex((d) => d.id === docId)
    if (idx === -1) return
    const [removed] = items.value.splice(idx, 1)
    try {
      await docApi.deleteDocument(docId)
    } catch (err) {
      // Rollback on failure
      items.value.splice(idx, 0, removed)
      throw err
    }
  }

  function updateProgress(docId: string, stage: string, percent: number) {
    processingStatus[docId] = { stage, percent }
    const doc = items.value.find((d) => d.id === docId)
    if (doc) doc.status = 'processing'
  }

  return {
    items, loading, uploadProgress, processingStatus,
    fetchByKb, upload, process, remove, updateProgress,
  }
})
