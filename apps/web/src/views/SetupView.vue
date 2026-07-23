<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { ApiError } from '@/api/http'
import AuthLayout from '@/components/AuthLayout.vue'
import type { AppLocale } from '@/i18n'
import { useAuthStore } from '@/stores/auth'

const { locale, t } = useI18n()
const router = useRouter()
const auth = useAuthStore()

const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const setupToken = ref('')
const submitting = ref(false)
const errorKey = ref('')

const passwordMismatch = computed(
  () => confirmPassword.value.length > 0 && password.value !== confirmPassword.value,
)

async function submit() {
  errorKey.value = ''
  if (passwordMismatch.value) {
    errorKey.value = 'auth.passwordMismatch'
    return
  }

  submitting.value = true
  try {
    await auth.setup({
      email: email.value,
      password: password.value,
      setupToken: setupToken.value,
      locale: locale.value as AppLocale,
    })
    await router.push({ name: 'dashboard' })
  } catch (error) {
    errorKey.value = error instanceof ApiError && error.status === 403
      ? 'auth.invalidSetupToken'
      : 'auth.setupFailed'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <AuthLayout>
    <template #eyebrow>
      {{ t('setup.eyebrow') }}
    </template>
    <template #title>
      {{ t('setup.title') }}
    </template>
    <template #description>
      {{ t('setup.description') }}
    </template>

    <form @submit.prevent="submit">
      <header class="form-header">
        <span>{{ t('setup.formLabel') }}</span>
        <strong>01 / 01</strong>
      </header>

      <label class="field">
        <span>{{ t('auth.email') }}</span>
        <input
          v-model.trim="email"
          type="email"
          autocomplete="email"
          required
        >
      </label>
      <label class="field">
        <span>{{ t('auth.password') }}</span>
        <input
          v-model="password"
          type="password"
          autocomplete="new-password"
          minlength="12"
          required
        >
        <small>{{ t('auth.passwordHint') }}</small>
      </label>
      <label class="field">
        <span>{{ t('auth.confirmPassword') }}</span>
        <input
          v-model="confirmPassword"
          type="password"
          autocomplete="new-password"
          minlength="12"
          required
        >
      </label>
      <label class="field">
        <span>{{ t('auth.setupToken') }}</span>
        <input
          v-model="setupToken"
          type="password"
          autocomplete="off"
          required
        >
        <small>{{ t('auth.setupTokenHint') }}</small>
      </label>

      <p
        v-if="errorKey"
        class="form-error"
        role="alert"
      >
        {{ t(errorKey) }}
      </p>

      <button
        class="primary-action"
        type="submit"
        :disabled="submitting"
      >
        <span>{{ submitting ? t('common.working') : t('setup.submit') }}</span>
        <span aria-hidden="true">↗</span>
      </button>
    </form>
  </AuthLayout>
</template>
