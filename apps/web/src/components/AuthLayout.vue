<script setup lang="ts">
import LocaleSwitch from '@/components/LocaleSwitch.vue'
</script>

<template>
  <main class="auth-shell">
    <nav class="topbar">
      <a
        class="wordmark"
        href="/"
      >Knowledge Isle</a>
      <LocaleSwitch />
    </nav>

    <section class="auth-stage">
      <div class="auth-intro">
        <span class="coordinate">23.07 / PRIVATE ARCHIVE</span>
        <p class="eyebrow">
          <slot name="eyebrow" />
        </p>
        <h1 class="auth-title">
          <slot name="title" />
        </h1>
        <p class="description">
          <slot name="description" />
        </p>
      </div>

      <div class="auth-panel">
        <div class="panel-index">
          KI / 01
        </div>
        <slot />
      </div>

      <div
        class="contour contour-one"
        aria-hidden="true"
      />
      <div
        class="contour contour-two"
        aria-hidden="true"
      />
    </section>
  </main>
</template>
