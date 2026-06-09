import type { ModelConfigOut, PresetProvider } from './types'

const BASE = '/api/v1/model-configs'

function headers(token: string): Record<string, string> {
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  }
}

export async function listConfigs(token: string): Promise<ModelConfigOut[]> {
  const res = await fetch(BASE + '/', { headers: headers(token) })
  if (!res.ok) throw new Error('Failed to load model configs')
  return res.json()
}

export async function listPresets(): Promise<PresetProvider[]> {
  const res = await fetch(BASE + '/presets')
  if (!res.ok) throw new Error('Failed to load presets')
  return res.json()
}

export async function createConfig(
  token: string,
  body: { name: string; provider: string; base_url: string; api_key: string; model_name: string },
): Promise<ModelConfigOut> {
  const res = await fetch(BASE + '/', {
    method: 'POST',
    headers: headers(token),
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error('Failed to create model config')
  return res.json()
}

export async function updateConfig(
  token: string,
  id: string,
  body: { name?: string; base_url?: string; api_key?: string; model_name?: string },
): Promise<ModelConfigOut> {
  const res = await fetch(BASE + '/' + id, {
    method: 'PUT',
    headers: headers(token),
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error('Failed to update model config')
  return res.json()
}

export async function deleteConfig(token: string, id: string): Promise<void> {
  const res = await fetch(BASE + '/' + id, {
    method: 'DELETE',
    headers: headers(token),
  })
  if (!res.ok) throw new Error('Failed to delete model config')
}

export async function activateConfig(token: string, id: string): Promise<void> {
  const res = await fetch(BASE + '/' + id + '/activate', {
    method: 'POST',
    headers: headers(token),
  })
  if (!res.ok) throw new Error('Failed to activate model config')
}

export async function testConnection(
  token: string,
  id: string,
): Promise<{ status: string; detail: string }> {
  const res = await fetch(BASE + '/' + id + '/test', {
    method: 'POST',
    headers: headers(token),
  })
  if (!res.ok) throw new Error('Failed to test connection')
  return res.json()
}
