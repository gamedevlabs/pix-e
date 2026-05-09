import { usePillarsApi } from '@/composables/api/pillarsApi'
import { InvalidApiKeyError, SessionExpiredError } from '~/utils/sessionFetch'
import { usePixeToast } from '~/composables/usePixeToast'
import { getSessionKey } from '~/composables/useSessionKey'

export function usePillars() {
  const basics = useCrud<Pillar>('api/llm/pillars/')

  const pillarsApi = usePillarsApi()
  const { error: errorToast } = usePixeToast()
  const designIdea = ref<string>('')
  const llmFeedback = ref<PillarsInContextFeedback>({
    coverage: {
      pillarFeedback: [],
    },
    contradictions: {
      contradictions: [],
    },
    proposedAdditions: {
      additions: [],
    },
  })

  const featureFeedback = ref<ContextInPillarsFeedback>({
    rating: 0,
    feedback: '',
  })

  const additionalFeature = ref<string>('')

  /**
   * Wrap an async call so that SessionExpiredError triggers the password
   * re-entry modal instead of an unhandled rejection.  On success the
   * retry re-executes the same call so the UI eventually gets its data.
   */
  async function callWithRetry<T>(fn: () => Promise<T>): Promise<T | undefined> {
    try {
      return await fn()
    } catch (err) {
      if (err instanceof SessionExpiredError) {
        getSessionKey().handleSessionExpired(fn)
        return undefined
      }
      throw err
    }
  }

  async function updateDesignIdea() {
    await pillarsApi.updateDesignIdeaAPICall(designIdea.value)
  }

  async function getPillarsInContextFeedback() {
    try {
      llmFeedback.value = (await callWithRetry(() => pillarsApi.getPillarsInContextAPICall()))!
    } catch (err) {
      handleLLMError(err)
    }
  }

  async function validatePillar(pillar: Pillar) {
    try {
      return await callWithRetry(() => pillarsApi.validatePillarAPICall(pillar))
    } catch (err) {
      handleLLMError(err)
    }
  }

  async function fixPillarWithAI(pillar: Pillar) {
    try {
      return await callWithRetry(() => pillarsApi.fixPillarWithAIAPICall(pillar))
    } catch (err) {
      handleLLMError(err)
    }
  }

  async function getPillarContradictions() {
    try {
      llmFeedback.value.contradictions = (await callWithRetry(() => pillarsApi.getPillarsContradictionsAPICall()))!
    } catch (err) {
      handleLLMError(err)
    }
  }

  async function getPillarsCompleteness() {
    try {
      llmFeedback.value.coverage = await callWithRetry(() => pillarsApi.getPillarsCompletenessAPICall())
    } catch (err) {
      handleLLMError(err)
    }
  }

  async function getPillarsAdditions() {
    try {
      llmFeedback.value.proposedAdditions = await callWithRetry(() => pillarsApi.getPillarsAdditionsAPICall())
    } catch (err) {
      handleLLMError(err)
    }
  }

  async function getContextInPillarsFeedback() {
    try {
      featureFeedback.value = await callWithRetry(() => pillarsApi.getContextInPillarsAPICall(additionalFeature.value))
    } catch (err) {
      handleLLMError(err)
    }
  }

  function handleLLMError(err: unknown) {
    if (err instanceof InvalidApiKeyError) {
      errorToast(err, 'Go to Settings to re-add your API key.', 'API Key Invalid')
      // Bump refresh flag so SettingsOverlay refetches keys on next open
      useState('apiKeyRefreshFlag', () => 0).value++
    } else if (err instanceof SessionExpiredError) {
      // Shouldn't reach here — callWithRetry handles it — but safety net
      getSessionKey().handleSessionExpired(() => Promise.reject(err))
    } else {
      errorToast(err)
    }
  }

  return {
    ...basics,
    designIdea,
    llmFeedback,
    featureFeedback,
    additionalFeature,
    validatePillar,
    updateDesignIdea,
    getPillarsInContextFeedback,
    fixPillarWithAI,
    getPillarContradictions,
    getPillarsCompleteness,
    getPillarsAdditions,
    getContextInPillarsFeedback,
  }
}
