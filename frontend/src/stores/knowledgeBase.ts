import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { KnowledgeBase } from '../api/types'
import * as kbApi from '../api/knowledgeBase'

export const useKnowledgeBaseStore = defineStore('knowledgeBase', () => {
  const list = ref<KnowledgeBase[]>([])
  const currentKbId = ref<string | null>(null)
  const loading = ref(false)

  const currentKb = computed(() =>
    list.value.find((kb) => kb.id === currentKbId.value) || null,
  )

  async function fetchList(domain?: string) {
    loading.value = true
    try {
      list.value = await kbApi.fetchKBs(domain)
    } finally {
      loading.value = false
    }
  }

  async function create(params: kbApi.CreateKBParams) {
    const kb = await kbApi.createKB(params)
    list.value.unshift(kb)
    return kb
  }

  async function remove(kbId: string) {
    await kbApi.deleteKB(kbId)
    list.value = list.value.filter((kb) => kb.id !== kbId)
    if (currentKbId.value === kbId) {
      currentKbId.value = null
    }
  }

  function select(kbId: string | null) {
    currentKbId.value = kbId
  }

  return { list, currentKbId, currentKb, loading, fetchList, create, remove, select }
})
