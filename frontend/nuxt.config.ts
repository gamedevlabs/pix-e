// nuxt.config.ts
import { defineNuxtConfig } from 'nuxt/config'
import fs from 'node:fs'
import path from 'node:path'
import { execSync } from 'node:child_process'

// Resolve the version safely from the root package.json or environment variables
let version = process.env.NUXT_PUBLIC_VERSION || process.env.APP_VERSION || '0.0.0'

try {
  const rootPkgPath = path.resolve(process.cwd(), '../package.json')
  if (fs.existsSync(rootPkgPath)) {
    const pkg = JSON.parse(fs.readFileSync(rootPkgPath, 'utf-8'))
    if (pkg.version) {
      version = pkg.version
    }
  }
  // Error object not required
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
} catch (_) {
  console.warn('Could not read root package.json, using fallback version:', version)
}

// Resolve the Git commit hash (from Env or local git command)
let gitHash =
  process.env.NUXT_PUBLIC_GIT_HASH || process.env.COMMIT_HASH || process.env.GITHUB_SHA || ''

if (!gitHash) {
  try {
    gitHash = execSync('git rev-parse --short HEAD', { encoding: 'utf-8' }).trim()
  } catch (e) {
    console.warn('Could not resolve Git commit hash:', e instanceof Error ? e.message : e)
  }
}

// Combine version and git hash if available
const shortGitHash = gitHash ? gitHash.substring(0, 7) : ''

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
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE ?? '',
      version: version,
      gitHash: shortGitHash,
    },
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
