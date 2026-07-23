<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import LocaleSwitch from '@/components/LocaleSwitch.vue'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const router = useRouter()
const auth = useAuthStore()

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
        <span class="future-item"><span>02</span>{{ t('dashboard.knowledgeBases') }}</span>
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

      <div class="empty-state">
        <span class="empty-index">FIRST ISLAND / 001</span>
        <h2>{{ t('dashboard.emptyTitle') }}</h2>
        <p>{{ t('dashboard.emptyDescription') }}</p>
        <button
          class="primary-action"
          type="button"
          disabled
        >
          <span>{{ t('dashboard.nextStep') }}</span>
          <span>＋</span>
        </button>
      </div>
    </section>
  </main>
</template>
