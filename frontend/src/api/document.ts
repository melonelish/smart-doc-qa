import client from './client'
import type { Document } from './types'

export interface UploadResult {
  id: string
  filename: string
  file_type: string
  file_size: number
  status: string
  created_at: string
}

export async function uploadFile(file: File, kbId?: string): Promise<UploadResult> {
  const form = new FormData()
  form.append('file', file)
  if (kbId) {
    const res = await client.post(`/knowledge-bases/${kbId}/upload`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return res.data
  }
  const res = await client.post('/documents/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}

export async function processDocument(docId: string): Promise<any> {
  const res = await client.post(`/documents/${docId}/process`)
  return res.data
}

export async function fetchDocuments(skip = 0, limit = 50): Promise<Document[]> {
  const res = await client.get('/documents/', { params: { skip, limit } })
  return res.data.items
}

export async function fetchKBDocuments(kbId: string): Promise<Document[]> {
  const res = await client.get(`/knowledge-bases/${kbId}/documents`)
  return res.data.items
}

export async function deleteDocument(docId: string): Promise<void> {
  await client.delete(`/documents/${docId}`)
}

export async function getDocumentContent(docId: string): Promise<string> {
  const res = await client.get(`/documents/${docId}/content`)
  return res.data
}
