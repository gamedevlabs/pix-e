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

  icon: {
    provider: 'server',
    clientBundle: {
      scan: true,
    },
    localApiEndpoint: '/_icons',
  },

  runtimeConfig: {
    apiUrl: process.env.NUXT_API_URL ?? 'http://backend-dev:8000',
    public: { apiBase: process.env.NUXT_PUBLIC_API_BASE ?? '' },
  },

  vite: {
    optimizeDeps: {
      include: ['@vue/devtools-core', '@vue/devtools-kit', 'pinia', 'chart.js'],
    },
    server: {
      watch: {
        usePolling: true,
        interval: 1000,
      },

      hmr: {
        protocol: 'wss',
        clientPort: 443,
      },
    },
  },
})
