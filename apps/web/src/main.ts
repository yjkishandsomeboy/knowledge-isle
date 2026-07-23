import { VueQueryPlugin } from '@tanstack/vue-query'
import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from './App.vue'
import { i18n } from './i18n'
import { router } from './router'
import './styles/main.css'

const pinia = createPinia()

createApp(App).use(pinia).use(VueQueryPlugin).use(i18n).use(router).mount('#app')
