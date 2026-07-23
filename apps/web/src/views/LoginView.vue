<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { ApiError } from '@/api/http'
import AuthLayout from '@/components/AuthLayout.vue'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const router = useRouter()
const auth = useAuthStore()

const email = ref('')
const password = ref('')
const submitting = ref(false)
const errorKey = ref('')

async function submit() {
  errorKey.value = ''
  submitting.value = true
  try {
    await auth.login({ email: email.value, password: password.value })
    await router.push({ name: 'dashboard' })
  } catch (error) {
    errorKey.value = error instanceof ApiError && error.status === 401
      ? 'auth.invalidCredentials'
      : 'auth.loginFailed'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <AuthLayout>
    <template #eyebrow>
      {{ t('login.eyebrow') }}
    </template>
    <template #title>
      {{ t('login.title') }}
    </template>
    <template #description>
      {{ t('login.description') }}
    </template>

    <form @submit.prevent="submit">
      <header class="form-header">
        <span>{{ t('login.formLabel') }}</span>
        <strong>SECURE / SESSION</strong>
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
          autocomplete="current-password"
          required
        >
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
        <span>{{ submitting ? t('common.working') : t('login.submit') }}</span>
        <span aria-hidden="true">→</span>
      </button>
    </form>
  </AuthLayout>
</template>
