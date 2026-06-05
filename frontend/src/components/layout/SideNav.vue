<template>
  <n-layout-sider
    bordered
    :native-scrollbar="false"
    :collapsed-width="0"
    width="240"
    class="sidebar"
    :style="{ background: 'var(--bg-secondary)', height: '100vh' }"
  >
    <div class="sidebar-header">
      <div class="logo">
        <div class="logo-icon">📄</div>
        <div class="logo-text">
          <h2>SmartDocQA</h2>
          <span>智能文档问答</span>
        </div>
      </div>
    </div>
    <nav class="sidebar-nav">
      <div class="nav-section-label">领域导航</div>
      <div
        v-for="d in domainStore.domains"
        :key="d.id"
        class="domain-item-wrapper"
        :class="{ active: domainStore.current === d.id, disabled: d.id === 'legal' }"
        @click="selectDomain(d.id)"
      >
        <span class="nav-icon">{{ d.icon }}</span>
        <span class="nav-label">{{ d.name }}</span>
        <n-tag v-if="d.id === 'legal'" size="tiny" :bordered="false" style="margin-left: auto">开发中</n-tag>
      </div>
      
      <!-- KB Quick Access -->
      <div class="nav-section-label mt-4">知识库</div>
      <div v-if="kbStore.list.length === 0" class="sidebar-empty">
        <span>暂无知识库</span>
      </div>
      <div
        v-for="kb in kbStore.list"
        :key="kb.id"
        class="kb-item-wrapper"
        :class="{ active: kbStore.currentKbId === kb.id }"
        @click.stop="selectKB(kb.id)"
      >
        <span class="nav-icon"></span>
        <span class="nav-label">{{ kb.name }}</span>
        <span class="kb-count">{{ kb.document_count || 0 }}</span>
        <span class="kb-del" @click.stop="confirmDeleteKB(kb.id)" title="删除知识库">✕</span>
      </div>
    </nav>
    <div class="sidebar-footer">
      <span class="status-dot"></span>
      <span>LangChain + FAISS</span>
    </div>
  </n-layout-sider>
</template>

<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { NLayoutSider, NTag, useDialog } from 'naive-ui'
import { useRouter } from 'vue-router'
import { useDomainStore } from '../../stores/domain'
import { useKnowledgeBaseStore } from '../../stores/knowledgeBase'
import { useConversationStore } from '../../stores/conversation'

const router = useRouter()
const dialog = useDialog()
const domainStore = useDomainStore()
const kbStore = useKnowledgeBaseStore()
const convStore = useConversationStore()

onMounted(async () => {
  await kbStore.fetchList(domainStore.current)
})

function selectDomain(id: string) {
  if (id === 'legal') return
  domainStore.select(id)
  kbStore.currentKbId = null
  convStore.clear()
  router.push('/')
}

function selectKB(kbId: string) {
  kbStore.currentKbId = kbId
  router.push(`/kb/${kbId}`)
}

function confirmDeleteKB(kbId: string) {
  const kb = kbStore.list.find(k => k.id === kbId)
  if (!kb) return
  dialog.warning({
    title: '删除知识库',
    content: `确定要删除知识库 "${kb.name}" 吗？此操作不可撤销。`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      await kbStore.remove(kbId)
      if (kbStore.currentKbId === kbId) {
        kbStore.currentKbId = null
        router.push('/')
      }
    }
  })
}

// Watch domain changes → reload KB list
watch(() => domainStore.current, async () => {
  await kbStore.fetchList(domainStore.current)
  kbStore.currentKbId = null
  router.push('/')
})
</script>

<style scoped>
.sidebar-header {
  padding: 20px 16px 16px;
  border-bottom: 1px solid var(--border);
}
.logo {
  display: flex;
  align-items: center;
  gap: 10px;
}
.logo-icon {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6, #a855f7);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: #fff;
  flex-shrink: 0;
}
.logo-text h2 {
  font-size: 14px;
  font-weight: 700;
  background: linear-gradient(135deg, #0ea5e9, #6366f1);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.logo-text span {
  font-size: 10px;
  color: var(--text-muted);
}
.sidebar-nav {
  flex: 1;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.nav-section-label {
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-muted);
  padding: 6px 8px 4px;
  font-weight: 600;
}
.domain-item-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.domain-item-wrapper:hover {
  background: var(--bg-card-hover);
}
.domain-item-wrapper.active {
  background: var(--accent);
  color: #fff;
}
.domain-item-wrapper.disabled { opacity: 0.4; cursor: not-allowed; }
.nav-label { flex: 1; }
.nav-icon { font-size: 16px; width: 20px; text-align: center; }
.sidebar-footer {
  padding: 10px 16px;
  border-top: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--text-muted);
}
.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 8px #10b981;
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* KB items in sidebar */
.mt-4 { margin-top: 12px; }
.sidebar-empty {
  padding: 8px;
  font-size: 11px;
  color: var(--text-muted);
  text-align: center;
}
.kb-item-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  font-size: 13px;
  color: var(--text-secondary);
}
.kb-item-wrapper:hover {
  background: var(--bg-card-hover);
  color: var(--text-primary);
}
.kb-item-wrapper.active {
  background: var(--accent);
  color: #fff;
}
.kb-count {
  margin-left: auto;
  font-size: 10px;
  background: var(--bg-input);
  padding: 1px 6px;
  border-radius: 10px;
  color: var(--text-muted);
}
.kb-item-wrapper.active .kb-count {
  background: rgba(255,255,255,0.2);
  color: #fff;
}
.kb-del {
  font-size: 10px;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s;
  padding: 0 4px;
  line-height: 1;
  color: var(--text-muted);
  flex-shrink: 0;
}
.kb-item-wrapper:hover .kb-del {
  opacity: 0.6;
}
.kb-del:hover {
  opacity: 1 !important;
  color: #ef4444;
}
</style>