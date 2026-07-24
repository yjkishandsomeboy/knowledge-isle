import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { i18n } from '@/i18n'
import type { DocumentItem, DocumentStatus } from '@/stores/documents'
import { useKnowledgeBasesStore } from '@/stores/knowledgeBases'

import KnowledgeBaseDetailView from './KnowledgeBaseDetailView.vue'

const routerMocks = vi.hoisted(() => ({
  push: vi.fn(),
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { knowledgeBaseId: 'knowledge-base-id' } }),
  useRouter: () => ({ push: routerMocks.push }),
}))

const POLL_INTERVAL_MS = 2_000

function createDocument(status: DocumentStatus): DocumentItem {
  return {
    id: 'document-id',
    knowledgeBaseId: 'knowledge-base-id',
    originalFilename: 'document.txt',
    contentType: 'text/plain',
    sizeBytes: 12,
    status,
    extractedText: null,
    errorMessage: null,
    createdAt: '2026-07-24T00:00:00Z',
    updatedAt: '2026-07-24T00:00:00Z',
  }
}

function jsonResponse(body: unknown) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  })
}

function mountView() {
  const pinia = createPinia()
  setActivePinia(pinia)
  const knowledgeBases = useKnowledgeBasesStore()
  knowledgeBases.loaded = true
  knowledgeBases.items = [{
    id: 'knowledge-base-id',
    name: 'Test knowledge base',
    description: null,
    defaultLocale: 'en-US',
    createdAt: '2026-07-24T00:00:00Z',
    updatedAt: '2026-07-24T00:00:00Z',
  }]

  return mount(KnowledgeBaseDetailView, {
    global: {
      plugins: [pinia, i18n],
      stubs: { LocaleSwitch: true },
    },
  })
}

describe('KnowledgeBaseDetailView document status polling', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    routerMocks.push.mockReset()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.useRealTimers()
  })

  it('refreshes a processing document until it is processed', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse([createDocument('processing')]))
      .mockResolvedValueOnce(jsonResponse([createDocument('processed')]))
    vi.stubGlobal('fetch', fetchMock)
    const wrapper = mountView()

    await flushPromises()

    expect(wrapper.get('.document-status').text()).toBe('Processing')
    expect(vi.getTimerCount()).toBe(1)

    await vi.advanceTimersByTimeAsync(POLL_INTERVAL_MS)
    await flushPromises()

    expect(wrapper.get('.document-status').text()).toBe('Ready')
    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(vi.getTimerCount()).toBe(0)

    wrapper.unmount()
  })

  it('starts polling after an upload and stops when processing fails', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse([]))
      .mockResolvedValueOnce(jsonResponse(createDocument('processing')))
      .mockResolvedValueOnce(jsonResponse([createDocument('failed')]))
    vi.stubGlobal('fetch', fetchMock)
    const wrapper = mountView()
    await flushPromises()

    const input = wrapper.get('input[type="file"]')
    Object.defineProperty(input.element, 'files', {
      configurable: true,
      value: [new File(['document'], 'document.txt', { type: 'text/plain' })],
    })
    await input.trigger('change')
    await flushPromises()

    expect(wrapper.get('.document-status').text()).toBe('Processing')
    expect(vi.getTimerCount()).toBe(1)

    await vi.advanceTimersByTimeAsync(POLL_INTERVAL_MS)
    await flushPromises()

    expect(wrapper.get('.document-status').text()).toBe('Failed')
    expect(fetchMock).toHaveBeenCalledTimes(3)
    expect(vi.getTimerCount()).toBe(0)

    wrapper.unmount()
  })

  it('keeps the current list when a polling request fails', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse([createDocument('processing')]))
      .mockRejectedValueOnce(new Error('temporarily unavailable'))
      .mockResolvedValueOnce(jsonResponse([createDocument('processed')]))
    vi.stubGlobal('fetch', fetchMock)
    const wrapper = mountView()
    await flushPromises()

    await vi.advanceTimersByTimeAsync(POLL_INTERVAL_MS)
    await flushPromises()

    expect(wrapper.get('.document-status').text()).toBe('Processing')
    expect(wrapper.find('.loading-state').exists()).toBe(false)
    expect(vi.getTimerCount()).toBe(1)

    await vi.advanceTimersByTimeAsync(POLL_INTERVAL_MS)
    await flushPromises()

    expect(wrapper.get('.document-status').text()).toBe('Ready')
    expect(fetchMock).toHaveBeenCalledTimes(3)

    wrapper.unmount()
  })

  it('clears the refresh timer when the view is unmounted', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse([createDocument('processing')]))
    vi.stubGlobal('fetch', fetchMock)
    const wrapper = mountView()
    await flushPromises()

    expect(vi.getTimerCount()).toBe(1)

    wrapper.unmount()

    expect(vi.getTimerCount()).toBe(0)
    await vi.advanceTimersByTimeAsync(POLL_INTERVAL_MS)
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })
})
