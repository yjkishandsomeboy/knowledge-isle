import { defineStore } from 'pinia'

import { apiRequest } from '@/api/http'

export type DocumentStatus = 'processing' | 'processed' | 'failed' | 'uploaded'

export interface DocumentItem {
  id: string
  knowledgeBaseId: string
  originalFilename: string
  contentType: string
  sizeBytes: number
  status: DocumentStatus
  extractedText: string | null
  errorMessage: string | null
  createdAt: string
  updatedAt: string
}

export const useDocumentsStore = defineStore('documents', {
  state: () => ({
    items: [] as DocumentItem[],
    loading: false,
    uploading: false,
  }),
  actions: {
    async load(knowledgeBaseId: string, showLoading = true) {
      if (showLoading) this.loading = true
      try {
        this.items = await apiRequest<DocumentItem[]>(
          `/knowledge-bases/${knowledgeBaseId}/documents`,
        )
      } finally {
        if (showLoading) this.loading = false
      }
    },
    async upload(knowledgeBaseId: string, file: File) {
      this.uploading = true
      const formData = new FormData()
      formData.append('file', file)
      try {
        const document = await apiRequest<DocumentItem>(
          `/knowledge-bases/${knowledgeBaseId}/documents`,
          { method: 'POST', body: formData },
        )
        this.items = [document, ...this.items]
        return document
      } finally {
        this.uploading = false
      }
    },
  },
})
