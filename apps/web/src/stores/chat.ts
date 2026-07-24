import { defineStore } from 'pinia'

import { apiRequest } from '@/api/http'

export interface ChatCitation {
  documentId: string
  filename: string
  snippet: string
  rank: number
  chunkId: string | null
  startOffset: number | null
  endOffset: number | null
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
    async askStream(knowledgeBaseId: string, question: string) {
      this.asking = true
      this.answer = {
        conversationId: this.conversationId ?? '',
        messageId: '',
        answer: '',
        citations: [],
        createdAt: new Date().toISOString(),
      }
      try {
        const response = await fetch(`/api/v1/knowledge-bases/${knowledgeBaseId}/chat/stream`, {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question, conversationId: this.conversationId }),
        })
        if (!response.ok || !response.body) throw new Error('Streaming request failed')
        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''
        for (;;) {
          const { value, done } = await reader.read()
          buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done })
          const events = buffer.split('\n\n')
          buffer = events.pop() ?? ''
          for (const event of events) {
            const dataLine = event.split('\n').find((line) => line.startsWith('data:'))
            if (!dataLine) continue
            const payload = JSON.parse(dataLine.slice(5).trim()) as { text?: string; conversationId?: string; messageId?: string; citations?: ChatCitation[] }
            if (payload.text) this.answer.answer += payload.text
            if (payload.conversationId) this.conversationId = payload.conversationId
            if (payload.conversationId) this.answer.conversationId = payload.conversationId
            if (payload.messageId) this.answer.messageId = payload.messageId
            if (payload.citations) this.answer.citations = payload.citations
          }
          if (done) break
        }
        return this.answer
      } finally {
        this.asking = false
      }
    },
  },
})
