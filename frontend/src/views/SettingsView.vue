<template>
  <div class="settings-page">
    <div class="settings-header">
      <button class="back-btn" @click="$router.push('/')">← 返回</button>
      <h2 class="settings-title">设置 · 模型管理</h2>
      <div style="flex:1"></div>
    </div>

    <div class="settings-body">
      <!-- Loading -->
      <div v-if="loading" class="loading-hint">加载中...</div>

      <!-- Config list -->
      <div v-else class="config-list">
        <div
          v-for="cfg in configs"
          :key="cfg.id"
          :class="['config-card', { active: cfg.is_active }]"
        >
          <div class="card-top">
            <span class="card-provider">{{ providerLabel(cfg.provider) }}</span>
            <span v-if="cfg.is_active" class="active-badge">当前使用</span>
          </div>
          <div class="card-name">{{ cfg.name }}</div>
          <div class="card-meta">
            <span class="meta-item">模型：{{ cfg.model_name }}</span>
            <span class="meta-item">Key：{{ cfg.api_key_masked }}</span>
          </div>
          <div class="card-actions">
            <button v-if="!cfg.is_active" class="act-btn" @click="activate(cfg.id)">设为默认</button>
            <button class="act-btn" @click="testConn(cfg.id)">测试连接</button>
            <button class="act-btn" @click="openEdit(cfg)">编辑</button>
            <button class="act-btn danger" @click="remove(cfg.id)">删除</button>
          </div>
        </div>

        <!-- Empty -->
        <div v-if="configs.length === 0" class="empty-hint">
          还没有配置模型，点击下方按钮添加你的第一个 AI 模型
        </div>
      </div>

      <!-- Add button -->
      <button class="add-btn" @click="showForm = true">+ 添加新模型</button>
    </div>

    <!-- Form overlay -->
    <Teleport to="body">
      <div v-if="showForm" class="modal-overlay" @click.self="closeForm">
        <div class="modal-card">
          <h3 class="modal-title">{{ editingId ? '编辑模型' : '添加模型' }}</h3>

          <div class="field">
            <label>名称</label>
            <input v-model="form.name" placeholder="如：我的 DeepSeek" />
          </div>

          <div class="field">
            <label>提供商</label>
            <select v-model="form.provider" @change="onProviderChange">
              <option v-for="p in presets" :key="p.key" :value="p.key">{{ p.label }}</option>
            </select>
          </div>

          <div class="field">
            <label>API 地址</label>
            <input v-model="form.base_url" placeholder="https://api.deepseek.com/v1" />
          </div>

          <div class="field">
            <label>API Key</label>
            <input
              v-model="form.api_key"
              type="password"
              placeholder="sk-..."
              :required="!editingId"
            />
          </div>

          <div class="field">
            <label>模型名称</label>
            <input v-model="form.model_name" placeholder="deepseek-chat" />
          </div>

          <div class="modal-actions">
            <button class="act-btn" @click="testFormConn" :disabled="testing">
              {{ testing ? '测试中...' : '测试连接' }}
            </button>
            <button class="act-btn primary" @click="saveForm" :disabled="saving">
              {{ saving ? '保存中...' : '保存' }}
            </button>
            <button class="act-btn" @click="closeForm">取消</button>
          </div>

          <p v-if="formMsg" :class="formMsg.startsWith('✅') ? 'msg-ok' : 'msg-err'">
            {{ formMsg }}
          </p>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import * as mcApi from '../api/modelConfig'
import type { ModelConfigOut, PresetProvider } from '../api/types'

const authStore = useAuthStore()
const token = ref(authStore.token || '')

const configs = ref<ModelConfigOut[]>([])
const presets = ref<PresetProvider[]>([])
const loading = ref(true)

const showForm = ref(false)
const editingId = ref<string | null>(null)
const saving = ref(false)
const testing = ref(false)
const formMsg = ref('')

const form = ref({
  name: '',
  provider: 'deepseek' as string,
  base_url: '',
  api_key: '',
  model_name: '',
})

onMounted(async () => {
  try {
    configs.value = await mcApi.listConfigs(token.value)
    presets.value = await mcApi.listPresets()
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})

function providerLabel(key: string): string {
  return presets.value.find(p => p.key === key)?.label || key
}

function onProviderChange() {
  const p = presets.value.find(p => p.key === form.value.provider)
  if (p && p.key !== 'custom') {
    form.value.base_url = p.base_url
    form.value.model_name = p.model_name
  }
}

function openEdit(cfg: ModelConfigOut) {
  editingId.value = cfg.id
  form.value = {
    name: cfg.name,
    provider: cfg.provider,
    base_url: cfg.base_url,
    api_key: '',
    model_name: cfg.model_name,
  }
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  editingId.value = null
  formMsg.value = ''
  form.value = { name: '', provider: 'deepseek', base_url: '', api_key: '', model_name: '' }
}

async function testFormConn() {
  // For new models, temporarily save then test
  if (editingId.value) {
    testing.value = true
    formMsg.value = ''
    try {
      const result = await mcApi.testConnection(token.value, editingId.value)
      formMsg.value = result.status === 'ok' ? '✅ ' + result.detail : '❌ ' + result.detail
    } catch (e: any) {
      formMsg.value = '❌ ' + e.message
    } finally {
      testing.value = false
    }
  } else {
    formMsg.value = '请先保存后再测试连接'
  }
}

async function testConn(id: string) {
  try {
    const result = await mcApi.testConnection(token.value, id)
    alert(result.status === 'ok' ? '✅ ' + result.detail : '❌ ' + result.detail)
  } catch (e: any) {
    alert('❌ ' + e.message)
  }
}

async function saveForm() {
  saving.value = true
  formMsg.value = ''
  try {
    if (editingId.value) {
      const payload: any = { name: form.value.name, base_url: form.value.base_url, model_name: form.value.model_name }
      if (form.value.api_key) payload.api_key = form.value.api_key
      await mcApi.updateConfig(token.value, editingId.value, payload)
    } else {
      if (!form.value.api_key) { formMsg.value = '❌ 请输入 API Key'; saving.value = false; return }
      await mcApi.createConfig(token.value, {
        name: form.value.name,
        provider: form.value.provider,
        base_url: form.value.base_url,
        api_key: form.value.api_key,
        model_name: form.value.model_name,
      })
    }
    configs.value = await mcApi.listConfigs(token.value)
    closeForm()
  } catch (e: any) {
    formMsg.value = '❌ ' + e.message
  } finally {
    saving.value = false
  }
}

async function activate(id: string) {
  await mcApi.activateConfig(token.value, id)
  configs.value = await mcApi.listConfigs(token.value)
}

async function remove(id: string) {
  if (!confirm('确定删除此模型配置？')) return
  await mcApi.deleteConfig(token.value, id)
  configs.value = await mcApi.listConfigs(token.value)
}
</script>

<style scoped>
.settings-page {
  max-width: 680px;
  margin: 0 auto;
  padding: 20px 16px 40px;
}
.settings-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}
.back-btn {
  background: var(--bg-input, #151a28);
  border: 1px solid var(--border, #252b3b);
  border-radius: 8px;
  padding: 6px 14px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-secondary, #94a3b8);
}
.settings-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary, #333);
  margin: 0;
}
.loading-hint, .empty-hint {
  text-align: center;
  padding: 40px 0;
  color: var(--text-muted, #999);
  font-size: 14px;
}
.config-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}
.config-card {
  padding: 16px;
  border: 1px solid var(--border, #e5e5e5);
  border-radius: 12px;
  background: var(--bg-card, #fff);
  transition: border-color 0.2s;
}
.config-card.active {
  border-color: #6366f1;
  box-shadow: 0 0 0 1px rgba(99,102,241,0.15);
}
.card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}
.card-provider {
  font-size: 12px;
  color: var(--text-muted, #999);
}
.active-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  background: linear-gradient(135deg, #6366f1, #7c3aed);
  color: #fff;
}
.card-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary, #333);
  margin-bottom: 6px;
}
.card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}
.meta-item {
  font-size: 12px;
  color: var(--text-secondary, #666);
}
.card-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.act-btn {
  padding: 5px 12px;
  border: 1px solid var(--border, #252b3b);
  border-radius: 6px;
  background: var(--bg-input, #151a28);
  font-size: 12px;
  color: var(--text-secondary, #94a3b8);
  cursor: pointer;
  transition: all 0.15s;
}
.act-btn:hover { border-color: #6366f1; color: #6366f1; }
.act-btn.primary { background: linear-gradient(135deg, #6366f1, #7c3aed); color: #fff; border-color: transparent; }
.act-btn.danger:hover { border-color: #e24b4a; color: #e24b4a; }
.act-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.add-btn {
  width: 100%;
  padding: 12px;
  border: 2px dashed var(--border, #e5e5e5);
  border-radius: 10px;
  background: transparent;
  font-size: 14px;
  color: var(--text-secondary, #666);
  cursor: pointer;
  transition: all 0.2s;
}
.add-btn:hover { border-color: #6366f1; color: #6366f1; }

/* Modal */
.modal-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.35);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}
.modal-card {
  width: 420px; max-width: 90vw;
  background: var(--bg-card, #fff);
  border-radius: 14px; padding: 24px;
}
.modal-title { font-size: 16px; font-weight: 600; margin: 0 0 16px; color: var(--text-primary); }
.field { margin-bottom: 12px; }
.field label { display: block; font-size: 12px; font-weight: 500; margin-bottom: 4px; color: var(--text-secondary); }
.field input, .field select {
  width: 100%; padding: 8px 10px; border: 1px solid var(--border, #252b3b);
  border-radius: 7px; font-size: 13px; background: var(--bg-input, #151a28);
  color: var(--text-primary, #f1f5f9); outline: none; box-sizing: border-box;
  -webkit-appearance: none; appearance: none;
}
.field select {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  padding-right: 30px;
}
.field input::placeholder {
  color: var(--text-muted, #64748b);
}
.field input:focus, .field select:focus { border-color: #6366f1; }
.modal-actions { display: flex; gap: 8px; margin-top: 16px; }
.msg-ok { color: #52c41a; font-size: 12px; margin-top: 8px; }
.msg-err { color: #e24b4a; font-size: 12px; margin-top: 8px; }
</style>
