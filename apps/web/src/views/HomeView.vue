<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import type { AppLocale } from '@/i18n'

type ApiState = 'checking' | 'online' | 'offline'

const { locale, t } = useI18n()
const apiState = ref<ApiState>('checking')

function toggleLocale() {
  const nextLocale: AppLocale = locale.value === 'zh-CN' ? 'en-US' : 'zh-CN'
  locale.value = nextLocale
  document.documentElement.lang = nextLocale
}

onMounted(async () => {
  try {
    const response = await fetch('/api/v1/health')
    apiState.value = response.ok ? 'online' : 'offline'
  } catch {
    apiState.value = 'offline'
  }
})
</script>

<template>
  <main class="shell">
    <nav
      class="topbar"
      aria-label="Primary navigation"
    >
      <a
        class="wordmark"
        href="/"
      >{{ t('brand') }}</a>
      <button
        class="language-switch"
        type="button"
        @click="toggleLocale"
      >
        {{ t('language') }}
      </button>
    </nav>

    <section class="hero">
      <div
        class="contour contour-one"
        aria-hidden="true"
      />
      <div
        class="contour contour-two"
        aria-hidden="true"
      />

      <div class="hero-copy">
        <p class="eyebrow">
          {{ t('eyebrow') }}
        </p>
        <h1>{{ t('title') }}</h1>
        <p class="description">
          {{ t('description') }}
        </p>
      </div>

      <aside class="status-card">
        <div class="status-heading">
          <span
            class="pulse"
            :class="apiState"
            aria-hidden="true"
          />
          <span>{{ t('statusLabel') }}</span>
        </div>
        <strong>{{ t(apiState) }}</strong>

        <dl>
          <div>
            <dt>{{ t('foundation') }}</dt>
            <dd>{{ t('foundationValue') }}</dd>
          </div>
          <div>
            <dt>{{ t('scope') }}</dt>
            <dd>{{ t('scopeValue') }}</dd>
          </div>
        </dl>
      </aside>
    </section>

    <footer>
      <span>01</span>
      <span class="footer-line" />
      <span>Foundation</span>
    </footer>
  </main>
</template>
