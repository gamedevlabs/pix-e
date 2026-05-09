import { defineStore } from 'pinia'
import { SessionExpiredError } from '~/utils/sessionFetch'
import { PROVIDER_ICONS } from '~/utils/api-key'

/**
 * An LLM model option associated with a user's stored API key.
 *
 * Each option pairs a model name with the specific API key that provides access.
 */
export interface LLMOption {
  /** Display label for the model, e.g. "gpt-4o (My Key)". */
  label: string
  /** Composite value in the format "model_name::key_id". */
  value: string
  /** Provider identifier (e.g. "openai", "gemini", "morpheus", "custom"). */
  provider: string
  /** The API key ID this model belongs to. */
  apiKeyId: string | null
  /** Icon name for the provider. */
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

/**
 * Pinia store for managing available LLM models and the user's active model selection.
 *
 * Fetches available models from the personal API keys endpoint and tracks
 * the currently selected model for use across the application.
 */
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

  /** Returns the icon name for a given provider identifier. Falls back to a generic globe icon. */
  function iconForProvider(provider: string): string {
    return PROVIDER_ICONS[provider as keyof typeof PROVIDER_ICONS] || 'i-lucide-globe'
  }

  /**
   * Fetches available models from the personal API keys endpoint.
   *
   * Calls `/api/accounts/api-keys/models/` to retrieve models for all stored keys.
   * Maintains the current selection if it still exists in the response;
   * otherwise resets to the first available model or clears the selection.
   */
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

      // Keep current selection if it still exists, otherwise pick first
      if (activeModel.value && !result.find((m) => m.value === activeModel.value)) {
        activeModel.value = ''
      }
      if (!activeModel.value && result.length > 0) {
        activeModel.value = result[0].value
      }
    } catch (err) {
      // Let session expiry bubble up so password modal appears
      if (err instanceof SessionExpiredError) {
        throw err
      }
      // Fallback: if no user keys or not logged in, show nothing
      models.value = []
    } finally {
      loading.value = false
      initialized.value = true
    }
  }

  /** Ensures models have been fetched at least once. Safe to call multiple times — subsequent calls are no-ops. */
  async function ensureInit() {
    if (!initialized.value) {
      try {
        await refreshModels()
      } catch {
        // Session expiry during initial load — no modal possible at mount time.
        // LLM call wrappers (callWithRetry in usePillars) will catch and show the
        // password modal when the user actually tries to use an AI feature.
      }
    }
  }

  return {
    models,
    activeModel,
    activeModelName,
    activeKeyId,
    activeModelIcon,
    loading,
    initialized,
    refreshModels,
    ensureInit,
  }
})
