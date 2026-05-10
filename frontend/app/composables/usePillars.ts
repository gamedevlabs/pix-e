import { usePillarsApi } from '@/composables/api/pillarsApi'
import { InvalidApiKeyError, SessionExpiredError } from '~/utils/sessionFetch'
import { usePixeToast } from '~/composables/usePixeToast'
import type { ExecutionMode } from '~/composables/useContextStrategies'
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
  const isEvaluating = ref(false)
  const executionMode = ref<ExecutionMode>('agentic')
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const evaluationResult = ref<any>(null)
  const evaluationError = ref<string | null>(null)

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

  async function fixPillarWithAI(pillar: Pillar, _validationIssues?: unknown): Promise<FixPillarAPIResponse | null> {
    try {
      const result = await callWithRetry(() => pillarsApi.fixPillarWithAIAPICall(pillar))
      return result ?? null
    } catch (err) {
      handleLLMError(err)
      return null
    }
  }

  async function acceptPillarFix(pillarId: number, name: string, description: string): Promise<Pillar> {
    // TODO: implement when endpoint exists
    return { id: pillarId, name, description } as Pillar
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
      llmFeedback.value.coverage = (await callWithRetry(() => pillarsApi.getPillarsCompletenessAPICall()))!
    } catch (err) {
      handleLLMError(err)
    }
  }

  async function getPillarsAdditions() {
    try {
      llmFeedback.value.proposedAdditions = (await callWithRetry(() => pillarsApi.getPillarsAdditionsAPICall()))!
    } catch (err) {
      handleLLMError(err)
    }
  }

  async function getContextInPillarsFeedback() {
    try {
      const result = await callWithRetry(() => pillarsApi.getContextInPillarsAPICall(additionalFeature.value))
      if (result) featureFeedback.value = result
    } catch (err) {
      handleLLMError(err)
    }
  }

  async function evaluateAll(mode?: ExecutionMode) {
    isEvaluating.value = true
    evaluationError.value = null
    try {
      const _modeToUse = mode ?? executionMode.value  // used by evaluateAllAPICall when implemented
      await callWithRetry(() => getPillarsInContextFeedback())
    } catch (err) {
      handleLLMError(err)
    } finally {
      isEvaluating.value = false
    }
  }

  function setExecutionMode(mode: ExecutionMode) {
    executionMode.value = mode
  }

  async function acceptAddition(name: string, description: string) {
    return await pillarsApi.acceptAdditionAPICall(name, description)
  }

  function clearEvaluation() {
    evaluationResult.value = null
    evaluationError.value = null
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
    acceptPillarFix,
    getPillarContradictions,
    getPillarsCompleteness,
    getPillarsAdditions,
    getContextInPillarsFeedback,
    isEvaluating,
    executionMode,
    evaluationResult,
    evaluationError,
    evaluateAll,
    setExecutionMode,
    acceptAddition,
    clearEvaluation,
  }
}
