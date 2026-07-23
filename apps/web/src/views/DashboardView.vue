<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import LocaleSwitch from '@/components/LocaleSwitch.vue'
import { useAuthStore } from '@/stores/auth'
import CreateKnowledgeBaseDialog from '@/components/CreateKnowledgeBaseDialog.vue'
import { useKnowledgeBasesStore } from '@/stores/knowledgeBases'

const { t } = useI18n()
const router = useRouter()
const auth = useAuthStore()
const knowledgeBases = useKnowledgeBasesStore()
const dialogOpen = ref(false)
const dialogRef = ref<InstanceType<typeof CreateKnowledgeBaseDialog> | null>(null)
const loadError = ref(false)

onMounted(async () => {
  try {
    await knowledgeBases.load()
  } catch {
    loadError.value = true
  }
})

async function logout() {
  await auth.logout()
  await router.push({ name: 'login' })
}
</script>

<template>
  <main class="dashboard-shell">
    <aside class="sidebar">
      <a
        class="wordmark"
        href="/app"
      >Knowledge Isle</a>
      <nav class="side-nav">
        <a
          class="active"
          href="/app"
        ><span>01</span>{{ t('dashboard.overview') }}</a>
        <a
          class="active"
          href="#knowledge-bases"
        ><span>02</span>{{ t('dashboard.knowledgeBases') }}</a>
        <span class="future-item"><span>03</span>{{ t('dashboard.conversations') }}</span>
      </nav>
      <div class="sidebar-footer">
        <span>{{ auth.user?.email }}</span>
        <button
          type="button"
          @click="logout"
        >
          {{ t('auth.logout') }}
        </button>
      </div>
    </aside>

    <section class="dashboard-main">
      <header class="dashboard-header">
        <div>
          <p class="eyebrow">
            {{ t('dashboard.eyebrow') }}
          </p>
          <h1>{{ t('dashboard.title') }}</h1>
        </div>
        <LocaleSwitch />
      </header>

      <div
        id="knowledge-bases"
        class="workspace-content"
      >
        <header class="content-toolbar">
          <div>
            <span class="empty-index">ARCHIVE / 001</span>
            <h2>{{ t('knowledgeBases.title') }}</h2>
          </div>
          <button
            class="primary-action compact-action"
            type="button"
            @click="dialogOpen = true"
          >
            <span>{{ t('knowledgeBases.create') }}</span>
            <span aria-hidden="true">＋</span>
          </button>
        </header>

        <p
          v-if="loadError"
          class="form-error"
          role="alert"
        >
          {{ t('knowledgeBases.loadFailed') }}
        </p>

        <div
          v-else-if="knowledgeBases.loading"
          class="loading-state"
        >
          {{ t('common.loading') }}
        </div>

        <div
          v-else-if="knowledgeBases.items.length > 0"
          class="knowledge-base-grid"
        >
          <article
            v-for="(item, index) in knowledgeBases.items"
            :key="item.id"
            class="knowledge-base-card"
            role="link"
            tabindex="0"
            @click="router.push({ name: 'knowledge-base-detail', params: { knowledgeBaseId: item.id } })"
            @keydown.enter="router.push({ name: 'knowledge-base-detail', params: { knowledgeBaseId: item.id } })"
          >
            <span class="card-index">{{ String(index + 1).padStart(2, '0') }} / ISLAND</span>
            <h3>{{ item.name }}</h3>
            <p>{{ item.description || t('knowledgeBases.noDescription') }}</p>
            <footer>
              <span>{{ item.defaultLocale }}</span>
              <span>0 {{ t('knowledgeBases.documents') }}</span>
            </footer>
          </article>
        </div>

        <div
          v-else
          class="empty-state"
        >
          <span class="empty-index">FIRST ISLAND / 001</span>
          <h2>{{ t('dashboard.emptyTitle') }}</h2>
          <p>{{ t('dashboard.emptyDescription') }}</p>
          <button
            class="primary-action"
            type="button"
            @click="dialogOpen = true"
          >
            <span>{{ t('knowledgeBases.createFirst') }}</span>
            <span aria-hidden="true">＋</span>
          </button>
        </div>
      </div>
    </section>

    <CreateKnowledgeBaseDialog
      ref="dialogRef"
      :open="dialogOpen"
      @close="dialogOpen = false"
      @submit="async (payload) => {
        try {
          await knowledgeBases.create(payload)
          dialogOpen = false
        } catch (error) {
          dialogRef?.showApiError(error)
        }
      }"
    />
  </main>
</template>
