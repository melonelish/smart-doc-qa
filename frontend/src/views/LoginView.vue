<template>
  <div class="login-page">
    <div class="login-bg-glow-1"></div>
    <div class="login-bg-glow-2"></div>
    <div class="login-card">
      <div class="login-logo">
        <span class="logo-icon">🧠</span>
        <span>Smart Doc QA</span>
      </div>
      <p class="login-subtitle">智能文档问答平台</p>

      <div class="login-tabs">
        <button
          :class="['tab-btn', { active: mode === 'login' }]"
          @click="mode = 'login'"
        >登录</button>
        <button
          :class="['tab-btn', { active: mode === 'register' }]"
          @click="mode = 'register'"
        >注册</button>
      </div>

      <form @submit.prevent="handleSubmit" class="login-form">
        <div class="field">
          <label class="field-label">用户名</label>
          <input
            v-model="form.username"
            class="field-input"
            :class="{ 'input-error': tried && !validUsername }"
            placeholder="请输入用户名（2-20个字符）"
            autocomplete="username"
            required
          />
          <p class="field-hint" :class="{ 'hint-error': tried && !validUsername }">用户名需 2-50 个字符</p>
        </div>
        <div class="field">
          <label class="field-label">密码</label>
          <input
            v-model="form.password"
            type="password"
            class="field-input"
            :class="{ 'input-error': tried && !validPassword }"
            placeholder="请输入密码（至少6个字符）"
            autocomplete="current-password"
            required
          />
          <p class="field-hint" :class="{ 'hint-error': tried && !validPassword }">密码需 6-128 个字符</p>
        </div>

        <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>

        <button type="submit" class="submit-btn" :disabled="authStore.loading">
          {{ authStore.loading ? '处理中...' : (mode === 'login' ? '登  录' : '注  册') }}
        </button>
      </form>

      <p class="hint">
        {{ mode === 'login' ? '还没有账号？' : '已有账号？' }}
        <button class="link-btn" @click="mode = mode === 'login' ? 'register' : 'login'">
          {{ mode === 'login' ? '去注册' : '去登录' }}
        </button>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const mode = ref<'login' | 'register'>('login')
const tried = ref(false)
const errorMsg = ref('')
const form = reactive({ username: '', password: '' })

const validUsername = computed(() => {
  const len = form.username.trim().length
  return len >= 2 && len <= 50
})
const validPassword = computed(() => {
  const len = form.password.length
  return len >= 6 && len <= 128
})

async function handleSubmit() {
  tried.value = true
  if (!validUsername.value || !validPassword.value) return
  errorMsg.value = ''
  try {
    const ok = mode.value === 'login'
      ? await authStore.doLogin(form.username, form.password)
      : await authStore.doRegister(form.username, form.password)
    if (ok) {
      router.replace('/')
    }
  } catch (e: any) {
    const msg = e?.message || e?.detail || (typeof e === 'string' ? e : '操作失败')
    errorMsg.value = msg
  }
}
</script>

<style scoped>
.login-page {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: var(--bg-primary, #0a0e17);
  overflow: hidden;
}
.login-bg-glow-1,
.login-bg-glow-2 {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  pointer-events: none;
  z-index: 0;
}
.login-bg-glow-1 {
  width: 500px;
  height: 500px;
  background: rgba(99, 102, 241, 0.12);
  top: -150px;
  right: -100px;
}
.login-bg-glow-2 {
  width: 400px;
  height: 400px;
  background: rgba(139, 92, 246, 0.10);
  bottom: -120px;
  left: -80px;
}
.login-card {
  position: relative;
  z-index: 1;
  width: 380px;
  padding: 44px 36px;
  background: var(--bg-card, #1a1f2e);
  border-radius: 20px;
  border: 1px solid var(--border, #252b3b);
  box-shadow: var(--shadow-lg, 0 8px 32px rgba(0, 0, 0, 0.5));
}
.login-logo {
  text-align: center;
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary, #f1f5f9);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.logo-icon {
  font-size: 26px;
}
.login-subtitle {
  text-align: center;
  font-size: 12px;
  color: var(--text-muted, #64748b);
  margin: 4px 0 28px;
}
.login-tabs {
  display: flex;
  gap: 0;
  margin-bottom: 24px;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid var(--border, #252b3b);
  background: var(--bg-input, #151a28);
}
.tab-btn {
  flex: 1;
  padding: 9px 0;
  border: none;
  background: transparent;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-muted, #64748b);
  cursor: pointer;
  transition: all 0.25s;
}
.tab-btn.active {
  background: linear-gradient(135deg, #6366f1 0%, #7c3aed 100%);
  color: #fff;
  font-weight: 600;
}
.login-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.field-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary, #94a3b8);
  letter-spacing: 0.3px;
}
.field-input {
  padding: 11px 14px;
  border: 1px solid var(--border, #252b3b);
  border-radius: 10px;
  font-size: 14px;
  background: var(--bg-input, #151a28);
  color: var(--text-primary, #f1f5f9);
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.field-input::placeholder {
  color: var(--text-muted, #64748b);
  font-size: 13px;
}
.field-input:focus {
  border-color: var(--accent, #6366f1);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.12);
}
.field-input.input-error {
  border-color: #e24b4a !important;
  box-shadow: 0 0 0 3px rgba(226, 75, 74, 0.12) !important;
}
.field-hint {
  font-size: 11px;
  color: var(--text-muted, #64748b);
  margin: 0;
  transition: color 0.2s;
}
.hint-error {
  color: #e24b4a;
}
.error-msg {
  color: #e24b4a;
  font-size: 12px;
  margin: 0;
  text-align: center;
  background: rgba(226, 75, 74, 0.08);
  padding: 8px 12px;
  border-radius: 8px;
}
.submit-btn {
  padding: 12px 0;
  border: none;
  border-radius: 10px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s, transform 0.2s;
  margin-top: 4px;
  letter-spacing: 1px;
}
.submit-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
.submit-btn:not(:disabled):hover {
  opacity: 0.9;
  transform: translateY(-1px);
}
.submit-btn:not(:disabled):active {
  transform: translateY(0);
}
.hint {
  text-align: center;
  font-size: 13px;
  color: var(--text-muted, #64748b);
  margin-top: 18px;
}
.link-btn {
  background: none;
  border: none;
  color: var(--accent-light, #818cf8);
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  padding: 0;
  transition: opacity 0.2s;
}
.link-btn:hover {
  opacity: 0.8;
}
</style>
