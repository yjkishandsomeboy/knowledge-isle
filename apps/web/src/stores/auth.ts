import { defineStore } from 'pinia'

import { apiRequest } from '@/api/http'
import type { AppLocale } from '@/i18n'

export interface AuthUser {
  id: string
  email: string
  locale: AppLocale
  createdAt: string
}

interface AuthStatus {
  initialized: boolean
  authenticated: boolean
  user: AuthUser | null
}

interface SetupInput {
  email: string
  password: string
  setupToken: string
  locale: AppLocale
}

interface LoginInput {
  email: string
  password: string
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    initialized: false,
    authenticated: false,
    user: null as AuthUser | null,
    loaded: false,
  }),
  actions: {
    async loadStatus(force = false) {
      if (this.loaded && !force) return
      const status = await apiRequest<AuthStatus>('/auth/status')
      this.initialized = status.initialized
      this.authenticated = status.authenticated
      this.user = status.user
      this.loaded = true
    },
    async setup(input: SetupInput) {
      this.user = await apiRequest<AuthUser>('/auth/setup', {
        method: 'POST',
        body: JSON.stringify(input),
      })
      this.initialized = true
      this.authenticated = true
      this.loaded = true
      localStorage.setItem('knowledge-isle-locale', input.locale)
    },
    async login(input: LoginInput) {
      this.user = await apiRequest<AuthUser>('/auth/login', {
        method: 'POST',
        body: JSON.stringify(input),
      })
      this.initialized = true
      this.authenticated = true
      this.loaded = true
    },
    async logout() {
      await apiRequest<void>('/auth/logout', { method: 'POST' })
      this.authenticated = false
      this.user = null
      this.loaded = true
    },
  },
})
