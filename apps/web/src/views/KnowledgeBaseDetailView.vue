<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import { ApiError } from '@/api/http'
import LocaleSwitch from '@/components/LocaleSwitch.vue'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import { useDocumentsStore } from '@/stores/documents'
import { useKnowledgeBasesStore } from '@/stores/knowledgeBases'

const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const chat = useChatStore()
const knowledgeBases = useKnowledgeBasesStore()
const documents = useDocumentsStore()
const fileInput = ref<HTMLInputElement | null>(null)
const loadError = ref(false)
const uploadError = ref('')
const question = ref('')
const chatError = ref(false)
const documentRefreshInterval = 2_000
let documentRefreshTimer: ReturnType<typeof setTimeout> | null = null
let mounted = true

const knowledgeBaseId = computed(() => String(route.params.knowledgeBaseId))
const knowledgeBase = computed(() => knowledgeBases.items.find((item) => item.id === knowledgeBaseId.value))

function stopDocumentRefresh() {
  if (documentRefreshTimer === null) return
  clearTimeout(documentRefreshTimer)
  documentRefreshTimer = null
}

function scheduleDocumentRefresh() {
  if (!mounted || documentRefreshTimer !== null) return
  if (!documents.items.some((document) => document.status === 'processing')) return

  documentRefreshTimer = setTimeout(async () => {
    documentRefreshTimer = null
    try {
      await documents.load(knowledgeBaseId.value, false)
    } catch {
      // Keep the currently displayed documents and retry while processing continues.
    }
    scheduleDocumentRefresh()
  }, documentRefreshInterval)
}

onMounted(async () => {
  try {
    if (!knowledgeBases.loaded) await knowledgeBases.load()
    await documents.load(knowledgeBaseId.value)
    scheduleDocumentRefresh()
  } catch {
    loadError.value = true
  }
})

onUnmounted(() => {
  mounted = false
  stopDocumentRefresh()
})

function chooseFile() {
  fileInput.value?.click()
}

async function uploadFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  uploadError.value = ''
  try {
    await documents.upload(knowledgeBaseId.value, file)
    scheduleDocumentRefresh()
  } catch (error) {
    uploadError.value = error instanceof ApiError && error.status === 415
      ? 'documents.unsupportedType'
      : 'documents.uploadFailed'
  }
}

async function logout() {
  await auth.logout()
  await router.push({ name: 'login' })
}

async function askQuestion() {
  if (!question.value.trim()) return
  chatError.value = false
  try {
    await chat.askStream(knowledgeBaseId.value, question.value.trim())
    question.value = ''
  } catch {
    chatError.value = true
  }
}

function formatSize(size: number) {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(locale.value, { dateStyle: 'medium' }).format(new Date(value))
}
</script>

<template>
  <main class="dashboard-shell">
    <aside class="sidebar">
      <a class="wordmark" href="/app">Knowledge Isle</a>
      <nav class="side-nav">
        <a href="/app"><span>01</span>{{ t('dashboard.overview') }}</a>
        <a class="active" href="#documents"><span>02</span>{{ t('dashboard.knowledgeBases') }}</a>
        <span class="future-item"><span>03</span>{{ t('dashboard.conversations') }}</span>
      </nav>
      <div class="sidebar-footer">
        <span>{{ auth.user?.email }}</span>
        <button type="button" @click="logout">{{ t('auth.logout') }}</button>
      </div>
    </aside>

    <section class="dashboard-main">
      <header class="dashboard-header">
        <div>
          <p class="eyebrow">{{ t('documents.eyebrow') }}</p>
          <h1>{{ knowledgeBase?.name || t('documents.title') }}</h1>
        </div>
        <LocaleSwitch />
      </header>

      <div id="documents" class="workspace-content document-workspace">
        <button class="back-link" type="button" @click="router.push({ name: 'dashboard' })">
          <span aria-hidden="true">←</span> {{ t('documents.back') }}
        </button>
        <div class="document-toolbar">
          <div>
            <span class="empty-index">ARCHIVE / {{ String(documents.items.length).padStart(3, '0') }}</span>
            <h2>{{ t('documents.title') }}</h2>
            <p>{{ knowledgeBase?.description || t('knowledgeBases.noDescription') }}</p>
          </div>
          <div>
            <input
              ref="fileInput"
              class="visually-hidden"
              type="file"
              accept=".pdf,.md,.markdown,.txt,application/pdf,text/markdown,text/plain"
              @change="uploadFile"
            >
            <button class="primary-action compact-action" type="button" :disabled="documents.uploading" @click="chooseFile">
              <span>{{ documents.uploading ? t('common.working') : t('documents.upload') }}</span>
              <span aria-hidden="true">↗</span>
            </button>
            <small class="upload-hint">{{ t('documents.formats') }}</small>
          </div>
        </div>

        <p v-if="uploadError" class="form-error" role="alert">{{ t(uploadError) }}</p>
        <p v-if="loadError" class="form-error" role="alert">{{ t('documents.loadFailed') }}</p>
        <div v-else-if="documents.loading" class="loading-state">{{ t('common.loading') }}</div>
        <div v-else-if="documents.items.length" class="document-list">
          <article v-for="(document, index) in documents.items" :key="document.id" class="document-row">
            <div class="document-number">{{ String(index + 1).padStart(2, '0') }}</div>
            <div class="document-meta">
              <h3>{{ document.originalFilename }}</h3>
              <p>{{ formatSize(document.sizeBytes) }} · {{ formatDate(document.createdAt) }}</p>
            </div>
            <span class="document-status" :class="`status-${document.status}`">{{ t(`documents.status.${document.status}`) }}</span>
          </article>
        </div>
        <div v-else class="document-empty">
          <span class="empty-index">NO SOURCES / 000</span>
          <h2>{{ t('documents.emptyTitle') }}</h2>
          <p>{{ t('documents.emptyDescription') }}</p>
        </div>

        <section class="chat-panel">
          <header>
            <span class="empty-index">CONCURRENT ANSWER / 001</span>
            <h2>{{ t('chat.title') }}</h2>
            <p>{{ t('chat.description') }}</p>
          </header>
          <form class="chat-form" @submit.prevent="askQuestion">
            <textarea
              v-model="question"
              :placeholder="t('chat.placeholder')"
              rows="3"
              maxlength="4000"
            />
            <button class="primary-action compact-action" type="submit" :disabled="chat.asking || !question.trim()">
              <span>{{ chat.asking ? t('chat.thinking') : t('chat.submit') }}</span>
              <span aria-hidden="true">↗</span>
            </button>
          </form>
          <p v-if="chatError" class="form-error" role="alert">{{ t('chat.failed') }}</p>
          <article v-if="chat.answer" class="answer-panel">
            <div class="answer-copy">{{ chat.answer.answer }}</div>
            <ol v-if="chat.answer.citations.length" class="citation-list">
              <li v-for="citation in chat.answer.citations" :key="`${chat.answer.messageId}-${citation.rank}`">
                <strong>[{{ citation.rank }}] {{ citation.filename }}</strong>
                <small v-if="citation.startOffset !== null && citation.endOffset !== null">
                  {{ citation.startOffset }}-{{ citation.endOffset }}
                </small>
                <p>{{ citation.snippet }}</p>
              </li>
            </ol>
          </article>
        </section>
      </div>
    </section>
  </main>
</template>
