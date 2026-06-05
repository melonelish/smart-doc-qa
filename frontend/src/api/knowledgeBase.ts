import client from './client'
import type { KnowledgeBase } from './types'

export interface CreateKBParams {
  name: string
  description?: string
  domain?: string
}

export async function fetchKBs(domain?: string): Promise<KnowledgeBase[]> {
  const params: Record<string, any> = {}
  if (domain) params.domain = domain
  const res = await client.get('/knowledge-bases/', { params })
  return res.data.items
}

export async function fetchKB(kbId: string): Promise<KnowledgeBase> {
  const res = await client.get(`/knowledge-bases/${kbId}`)
  return res.data
}

export async function createKB(params: CreateKBParams): Promise<KnowledgeBase> {
  const res = await client.post('/knowledge-bases/', params)
  return res.data
}

export async function deleteKB(kbId: string): Promise<void> {
  await client.delete(`/knowledge-bases/${kbId}`)
}

export async function rebuildKBIndex(kbId: string): Promise<void> {
  await client.post(`/knowledge-bases/${kbId}/rebuild-index`)
}
