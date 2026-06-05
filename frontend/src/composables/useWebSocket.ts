import { ref, onUnmounted } from 'vue'

export function useWebSocket(docId: string) {
  const connected = ref(false)
  const progress = ref({ stage: '', percent: 0 })
  let ws: WebSocket | null = null

  function connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${protocol}//${window.location.host}/ws/progress/${docId}`
    ws = new WebSocket(url)
    ws.onopen = () => { connected.value = true }
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'progress') {
          progress.value = { stage: data.stage, percent: data.percent }
        }
      } catch {
        // ignore
      }
    }
    ws.onclose = () => { connected.value = false }
    ws.onerror = () => { connected.value = false }
  }

  function disconnect() {
    if (ws) {
      ws.close()
      ws = null
    }
  }

  onUnmounted(() => disconnect())

  return { connected, progress, connect, disconnect }
}
