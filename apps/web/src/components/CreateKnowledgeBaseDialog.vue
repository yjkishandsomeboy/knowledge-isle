<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { ApiError } from '@/api/http'
import type { KnowledgeBaseLocale } from '@/stores/knowledgeBases'

defineProps<{ open: boolean }>()

const emit = defineEmits<{
  close: []
  submit: [payload: { name: string; description: string; defaultLocale: KnowledgeBaseLocale }]
}>()

const { t, locale } = useI18n()
const name = ref('')
const description = ref('')
const defaultLocale = ref<KnowledgeBaseLocale>('zh-CN')
const errorKey = ref('')

function close() {
  name.value = ''
  description.value = ''
  defaultLocale.value = locale.value === 'en-US' ? 'en-US' : 'zh-CN'
  errorKey.value = ''
  emit('close')
}

function submit() {
  if (!name.value.trim()) {
    errorKey.value = 'knowledgeBases.nameRequired'
    return
  }
  errorKey.value = ''
  emit('submit', {
    name: name.value.trim(),
    description: description.value.trim(),
    defaultLocale: defaultLocale.value,
  })
}

function showApiError(error: unknown) {
  errorKey.value = error instanceof ApiError && error.status === 422
    ? 'knowledgeBases.invalidForm'
    : 'knowledgeBases.createFailed'
}

defineExpose({ showApiError })
</script>

<template>
  <div
    v-if="open"
    class="dialog-backdrop"
    role="presentation"
    @click.self="close"
  >
    <section
      class="dialog-panel"
      role="dialog"
      aria-modal="true"
      :aria-label="t('knowledgeBases.dialogTitle')"
    >
      <header class="dialog-header">
        <div>
          <span class="dialog-index">NEW ISLAND / 001</span>
          <h2>{{ t('knowledgeBases.dialogTitle') }}</h2>
        </div>
        <button
          class="dialog-close"
          type="button"
          :aria-label="t('common.close')"
          @click="close"
        >
          ×
        </button>
      </header>

      <form @submit.prevent="submit">
        <label class="field">
          <span>{{ t('knowledgeBases.name') }}</span>
          <input
            v-model="name"
            type="text"
            maxlength="120"
            required
            autofocus
          >
        </label>
        <label class="field">
          <span>{{ t('knowledgeBases.description') }}</span>
          <textarea
            v-model="description"
            rows="3"
            maxlength="2000"
          />
        </label>
        <label class="field">
          <span>{{ t('knowledgeBases.answerLanguage') }}</span>
          <select v-model="defaultLocale">
            <option value="zh-CN">{{ t('common.chinese') }}</option>
            <option value="en-US">{{ t('common.english') }}</option>
          </select>
        </label>

        <p
          v-if="errorKey"
          class="form-error"
          role="alert"
        >
          {{ t(errorKey) }}
        </p>

        <div class="dialog-actions">
          <button
            class="secondary-action"
            type="button"
            @click="close"
          >
            {{ t('common.cancel') }}
          </button>
          <button
            class="primary-action"
            type="submit"
          >
            <span>{{ t('knowledgeBases.create') }}</span>
            <span aria-hidden="true">↗</span>
          </button>
        </div>
      </form>
    </section>
  </div>
</template>
