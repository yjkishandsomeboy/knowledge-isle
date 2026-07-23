import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/app',
    },
    {
      path: '/setup',
      name: 'setup',
      component: () => import('@/views/SetupView.vue'),
      meta: { public: true },
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/app',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
    },
    {
      path: '/app/knowledge-bases/:knowledgeBaseId',
      name: 'knowledge-base-detail',
      component: () => import('@/views/KnowledgeBaseDetailView.vue'),
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  try {
    await auth.loadStatus()
  } catch {
    if (to.name !== 'login') return { name: 'login', query: { unavailable: '1' } }
    return true
  }

  if (!auth.initialized && to.name !== 'setup') return { name: 'setup' }
  if (auth.initialized && !auth.authenticated && to.name !== 'login') return { name: 'login' }
  if (auth.authenticated && (to.name === 'login' || to.name === 'setup')) {
    return { name: 'dashboard' }
  }
  return true
})
