import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import * as authApi from '../api/auth'

const TOKEN_KEY = 'smartdocqa_token'
const USER_KEY = 'smartdocqa_user'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const username = ref<string | null>(localStorage.getItem(USER_KEY))
  const loading = ref(false)

  const isLoggedIn = computed(() => !!token.value)

  function saveAuth(t: string, user: string, userId: string) {
    token.value = t
    username.value = user
    localStorage.setItem(TOKEN_KEY, t)
    localStorage.setItem(USER_KEY, user)
    localStorage.setItem('smartdocqa_userid', userId)
  }

  function clearAuth() {
    token.value = null
    username.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    localStorage.removeItem('smartdocqa_userid')
  }

  async function doLogin(user: string, pass: string) {
    loading.value = true
    try {
      const resp = await authApi.login(user, pass)
      saveAuth(resp.access_token, resp.username, resp.user_id)
      return true
    } finally {
      loading.value = false
    }
  }

  async function doRegister(user: string, pass: string) {
    loading.value = true
    try {
      const resp = await authApi.register(user, pass)
      saveAuth(resp.access_token, resp.username, resp.user_id)
      return true
    } finally {
      loading.value = false
    }
  }

  function logout() {
    clearAuth()
  }

  return {
    token,
    username,
    loading,
    isLoggedIn,
    doLogin,
    doRegister,
    logout,
    clearAuth,
  }
})
