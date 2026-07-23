import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import { i18n } from '@/i18n'

import HomeView from './HomeView.vue'

describe('HomeView', () => {
  it('renders the product name', () => {
    const wrapper = mount(HomeView, {
      global: {
        plugins: [i18n],
      },
    })

    expect(wrapper.text()).toContain('Knowledge Isle')
  })
})
