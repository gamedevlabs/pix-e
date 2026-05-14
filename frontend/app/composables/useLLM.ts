import { defineStore } from 'pinia'
import { PROVIDER_ICONS } from '~/utils/api-key'
import { sessionFetch, SessionExpiredError } from '~/utils/sessionFetch'
import { getSessionKey } from '~/composables/useSessionKey'

export interface LLMOption {
  label: string
  value: string
  provider: string
  apiKeyId: string | null
  icon: string
}

interface KeyModelsResponse {
  keys: Array<{
    id: string
    label: string
    provider: string
    models: Array<{
      name: string
      provider: string
      type: string
    }>
  }>
}

export const useLLM = defineStore('llm', () => {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase
  const models = ref<LLMOption[]>([])
  const activeModel = ref<string>('')
  const initialized = ref(false)
  const loading = ref(false)

  const activeModelName = computed(() => activeModel.value.split('::')[0])
  const activeKeyId = computed(() => activeModel.value.split('::')[1] || null)
  const activeModelIcon = computed(
    () => models.value.find((m) => m.value === activeModel.value)?.icon || '',
  )

  function iconForProvider(provider: string): string {
    return PROVIDER_ICONS[provider as keyof typeof PROVIDER_ICONS] || 'i-lucide-globe'
  }

  async function refreshModels() {
    loading.value = true
    try {
      const data = await sessionFetch<KeyModelsResponse>(
        `${apiBase}/api/accounts/api-keys/models/`,
        {
          credentials: 'include',
        },
      )

      const result: LLMOption[] = []

      for (const key of data.keys) {
        for (const model of key.models) {
          result.push({
            label: `${model.name} (${key.label})`,
            value: `${model.name}::${key.id}`,
            provider: key.provider,
            apiKeyId: key.id,
            icon: iconForProvider(key.provider),
          })
        }
      }

      models.value = result

      if (activeModel.value && !result.find((m) => m.value === activeModel.value)) {
        activeModel.value = ''
      }
      if (!activeModel.value && result.length > 0) {
        activeModel.value = result[0]!.value
      }

      initialized.value = true
    } catch (err) {
      if (err instanceof SessionExpiredError) {
        getSessionKey().handleSessionExpired(() => refreshModels())
      }
    } finally {
      loading.value = false
    }
  }

  return {
    models,
    activeModel,
    activeModelName,
    activeKeyId,
    activeModelIcon,
    initialized,
    loading,
    refreshModels,
    iconForProvider,
  }
})
