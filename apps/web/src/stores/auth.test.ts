import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from './auth'

describe('auth store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.restoreAllMocks()
  })

  it('loads the unauthenticated setup state', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({ initialized: false, authenticated: false, user: null }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        ),
      ),
    )

    const auth = useAuthStore()
    await auth.loadStatus()

    expect(auth.loaded).toBe(true)
    expect(auth.initialized).toBe(false)
    expect(auth.authenticated).toBe(false)
  })

  it('marks the administrator authenticated after login', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            id: 'admin-id',
            email: 'admin@example.com',
            locale: 'zh-CN',
            createdAt: '2026-07-23T00:00:00Z',
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        ),
      ),
    )

    const auth = useAuthStore()
    await auth.login({ email: 'admin@example.com', password: 'secure-password' })

    expect(auth.initialized).toBe(true)
    expect(auth.authenticated).toBe(true)
    expect(auth.user?.email).toBe('admin@example.com')
  })
})
