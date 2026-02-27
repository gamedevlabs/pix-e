// nuxt.config.ts
import { defineNuxtConfig } from 'nuxt/config'

// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2024-11-01',
  devtools: { enabled: true },
  srcDir: 'app/',
  app: {
    pageTransition: { name: 'page', mode: 'out-in' },
    head: {
      title: 'pix:e',
      link: [{ rel: 'icon', type: 'image/x-icon', href: '/favicon.png' }],
    },
  },

  components: [
    {
      path: '~/components',
      pathPrefix: false,
    },
  ],

  modules: [
    //'@nuxt/content',
    '@nuxt/eslint',
    '@nuxt/fonts',
    '@nuxt/icon',
    '@nuxt/image',
    '@nuxt/test-utils',
    '@nuxt/ui',
  ],

  css: ['~/assets/css/main.css'],
  runtimeConfig: {
    // Server-only. Prefer env at runtime; empty string keeps types stable.
    openaiApiKey: process.env.OPENAI_API_KEY ?? '',
    public: {
      apiBase: 'http://localhost:8000',
      // mock-only study deployment; no dataMode switching
    },
  },
})
