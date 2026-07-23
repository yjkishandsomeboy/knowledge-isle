<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import type { AppLocale } from '@/i18n'

const { locale, t } = useI18n()

function toggleLocale() {
  const nextLocale: AppLocale = locale.value === 'zh-CN' ? 'en-US' : 'zh-CN'
  locale.value = nextLocale
  document.documentElement.lang = nextLocale
  localStorage.setItem('knowledge-isle-locale', nextLocale)
}
</script>

<template>
  <button
    class="language-switch"
    type="button"
    :aria-label="t('common.switchLanguage')"
    @click="toggleLocale"
  >
    {{ t('common.language') }}
  </button>
</template>
