import { usePillarsApi } from '@/composables/api/pillarsApi'

// Shared state - singleton pattern for cross-component reactivity
const items = ref<Pillar[]>([])
const loading = ref(false)
const error = ref<unknown>(null)

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

// Agentic evaluation state
const evaluationResult = ref<EvaluateAllResponse | null>(null)
const isEvaluating = ref(false)
const evaluationError = ref<string | null>(null)

export function usePillars() {
  const config = useRuntimeConfig()
  const pillarsApi = usePillarsApi()
  const { success, error: errorToast } = usePixeToast()
  const API_URL = `${config.public.apiBase}/llm/pillars/`

  // Shared fetch function
  async function fetchAll() {
    loading.value = true
    try {
      const data = await $fetch<Pillar[]>(API_URL, {
        credentials: 'include',
        headers: useRequestHeaders(['cookie']),
      })
      items.value = data || []
    } catch (err) {
      error.value = err
      errorToast(err)
    } finally {
      loading.value = false
    }
  }

  async function createItem(payload: Partial<Pillar>) {
    try {
      const result = await $fetch<Pillar>(API_URL, {
        method: 'POST',
        body: payload,
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      })
      success('Item created successfully!')
      await fetchAll()
      return result
    } catch (err) {
      error.value = err
      errorToast(err)
      return null
    }
  }

  async function updateItem(id: number | string, payload: Partial<Pillar>) {
    try {
      await $fetch<Pillar>(`${API_URL}${id}/`, {
        method: 'PATCH',
        body: payload,
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      })
      success('Item updated successfully!')
      await fetchAll()
    } catch (err) {
      error.value = err
      errorToast(err)
    }
  }

  async function deleteItem(id: number | string) {
    try {
      await $fetch<null>(`${API_URL}${id}/`, {
        method: 'DELETE',
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      })
      success('Item deleted successfully!')
      await fetchAll()
    } catch (err) {
      error.value = err
      errorToast(err)
    }
  }

  // Game concept operations
  const isSavingConcept = ref(false)

  async function fetchGameConcept() {
    try {
      const data = await $fetch<{ content: string }>(
        `${config.public.apiBase}/game-concept/current/`,
        {
          credentials: 'include',
          headers: useRequestHeaders(['cookie']),
        },
      )
      designIdea.value = data?.content ?? ''
    } catch {
      // No current concept exists, that's ok
      designIdea.value = ''
    }
  }

  async function saveGameConcept() {
    if (!designIdea.value.trim()) return

    isSavingConcept.value = true
    try {
      await $fetch(`${config.public.apiBase}/game-concept/update_current/`, {
        method: 'POST',
        body: { content: designIdea.value },
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      })
      success('Game concept saved!')
    } catch (err) {
      error.value = err
      errorToast(err)
    } finally {
      isSavingConcept.value = false
    }
  }

  async function updateDesignIdea() {
    await pillarsApi.updateDesignIdeaAPICall(designIdea.value)
  }

  async function getPillarsInContextFeedback() {
    llmFeedback.value = await pillarsApi.getPillarsInContextAPICall()
  }

  async function validatePillar(pillar: Pillar) {
    return await pillarsApi.validatePillarAPICall(pillar)
  }

  async function fixPillarWithAI(pillar: Pillar, validationIssues: StructuralIssue[] = []) {
    return await pillarsApi.fixPillarWithAIAPICall(pillar, validationIssues)
  }

  async function acceptPillarFix(pillarId: number, name: string, description: string) {
    return await pillarsApi.acceptPillarFixAPICall(pillarId, name, description)
  }

  async function getPillarContradictions() {
    llmFeedback.value.contradictions = await pillarsApi.getPillarsContradictionsAPICall()
  }

  async function getPillarsCompleteness() {
    llmFeedback.value.coverage = await pillarsApi.getPillarsCompletenessAPICall()
  }

  async function getPillarsAdditions() {
    llmFeedback.value.proposedAdditions = await pillarsApi.getPillarsAdditionsAPICall()
  }

  async function getContextInPillarsFeedback() {
    featureFeedback.value = await pillarsApi.getContextInPillarsAPICall(additionalFeature.value)
  }

  // --- New agentic evaluation methods ---

  async function evaluateAll() {
    isEvaluating.value = true
    evaluationError.value = null
    try {
      evaluationResult.value = await pillarsApi.evaluateAllAPICall()
    } catch (err) {
      console.error('Error evaluating pillars:', err)
      evaluationError.value = 'Failed to evaluate pillars. Please try again.'
    } finally {
      isEvaluating.value = false
    }
  }

  async function resolveContradictions(contradictions: ContradictionsResponse) {
    return await pillarsApi.resolveContradictionsAPICall(contradictions)
  }

  async function acceptAddition(name: string, description: string) {
    return await pillarsApi.acceptAdditionAPICall(name, description)
  }

  function clearEvaluation() {
    evaluationResult.value = null
    evaluationError.value = null
  }

  return {
    // CRUD operations with shared state
    items,
    loading,
    error,
    fetchAll,
    createItem,
    updateItem,
    deleteItem,
    // Game concept
    designIdea,
    isSavingConcept,
    fetchGameConcept,
    saveGameConcept,
    // Pillar-specific state
    llmFeedback,
    featureFeedback,
    additionalFeature,
    // Pillar operations
    validatePillar,
    updateDesignIdea,
    getPillarsInContextFeedback,
    fixPillarWithAI,
    acceptPillarFix,
    getPillarContradictions,
    getPillarsCompleteness,
    getPillarsAdditions,
    getContextInPillarsFeedback,
    // Agentic evaluation
    evaluationResult,
    isEvaluating,
    evaluationError,
    evaluateAll,
    resolveContradictions,
    acceptAddition,
    clearEvaluation,
  }
}
