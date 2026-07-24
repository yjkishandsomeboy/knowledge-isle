import { defineStore } from 'pinia'

import { apiRequest } from '@/api/http'

export interface ChatCitation {
  documentId: string
  filename: string
  snippet: string
  rank: number
}

export interface ChatAnswer {
  conversationId: string
  messageId: string
  answer: string
  citations: ChatCitation[]
  createdAt: string
}

export const useChatStore = defineStore('chat', {
  state: () => ({
    conversationId: null as string | null,
    answer: null as ChatAnswer | null,
    asking: false,
  }),
  actions: {
    async ask(knowledgeBaseId: string, question: string) {
      this.asking = true
      try {
        this.answer = await apiRequest<ChatAnswer>(
          `/knowledge-bases/${knowledgeBaseId}/chat`,
          {
            method: 'POST',
            body: JSON.stringify({
              question,
              conversationId: this.conversationId,
            }),
          },
        )
        this.conversationId = this.answer.conversationId
        return this.answer
      } finally {
        this.asking = false
      }
    },
  },
})
