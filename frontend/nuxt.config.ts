// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2024-11-01',
  devtools: { enabled: true },
  app: {
    pageTransition: { name: 'page', mode: 'out-in' },
    head: {
      title: 'Pixie',
      link: [{ rel: 'icon', type: 'image/x-icon', href: '/favicon.png' }],
    },
  },

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
    mode: 'svg',
    collections: ['heroicons', 'lucide'],
    clientBundle: {
      scan: true,
      sizeLimitKb: 512,
    },
    serverBundle: false,
    provider: 'iconify',
  },

  runtimeConfig: {
    public: {
      apiBase: 'http://localhost:8000',
    },
  },

  nitro: {
    devProxy: {
      '/moodboards': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        cookiePathRewrite: '/',
        prependPath: true,
      },
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        cookiePathRewrite: '/',
        ws: true,
      },
      '/accounts': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        cookiePathRewrite: '/',
      },
      '/llm': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        cookiePathRewrite: '/',
      },
      '/media': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        prependPath: true,
      },
    },
  },
})
