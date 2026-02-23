import type { ProjectDataProvider } from '~/studyMock'
import { createMockProjectDataProvider } from '~/studyMock'

const NUXT_APP_KEY = 'pixeProjectDataProvider'

export function useProjectDataProvider(): ProjectDataProvider {
  const nuxtApp = useNuxtApp()
  const anyApp = nuxtApp as Record<string, unknown>

  if (anyApp[NUXT_APP_KEY]) return anyApp[NUXT_APP_KEY] as ProjectDataProvider

  const provider = createMockProjectDataProvider()
  anyApp[NUXT_APP_KEY] = provider
  return provider
}
