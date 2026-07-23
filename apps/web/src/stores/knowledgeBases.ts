import { defineStore } from 'pinia'

import { apiRequest } from '@/api/http'

export type KnowledgeBaseLocale = 'zh-CN' | 'en-US'

export interface KnowledgeBase {
  id: string
  name: string
  description: string | null
  defaultLocale: KnowledgeBaseLocale
  createdAt: string
  updatedAt: string
}

interface CreateKnowledgeBaseInput {
  name: string
  description?: string
  defaultLocale: KnowledgeBaseLocale
}

export const useKnowledgeBasesStore = defineStore('knowledge-bases', {
  state: () => ({
    items: [] as KnowledgeBase[],
    loaded: false,
    loading: false,
  }),
  actions: {
    async load() {
      this.loading = true
      try {
        this.items = await apiRequest<KnowledgeBase[]>('/knowledge-bases')
        this.loaded = true
      } finally {
        this.loading = false
      }
    },
    async create(input: CreateKnowledgeBaseInput) {
      const item = await apiRequest<KnowledgeBase>('/knowledge-bases', {
        method: 'POST',
        body: JSON.stringify(input),
      })
      this.items = [item, ...this.items]
      return item
    },
    async remove(id: string) {
      await apiRequest<void>(`/knowledge-bases/${id}`, { method: 'DELETE' })
      this.items = this.items.filter((item) => item.id !== id)
    },
  },
})
