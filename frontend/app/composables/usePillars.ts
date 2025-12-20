import { usePillarsApi } from '@/composables/api/pillarsApi'

// Shared state - singleton pattern for cross-component reactivity
const items = ref<Pillar[]>([])
const loading = ref(false)
const error = ref<unknown>(null)

const featureFeedback = ref<ContextInPillarsFeedback>({
  rating: 0,
  feedback: '',
})

const additionalFeature = ref<string>('')

// Evaluation state (supports both monolithic and agentic modes)
const evaluationResult = ref<EvaluateAllResponse | null>(null)
const isEvaluating = ref(false)
const evaluationError = ref<string | null>(null)
const executionMode = ref<ExecutionMode>('agentic')

export function usePillars() {
  const config = useRuntimeConfig()
  const pillarsApi = usePillarsApi()
  const { success, error: errorToast } = usePixeToast()
  const API_URL = `${config.public.apiBase}/llm/pillars/`

  // Use shared game concept state
  const {
    designIdea,
    isSavingConcept,
    conceptHistory,
    isLoadingHistory,
    isRestoringConcept,
    fetchGameConcept,
    saveGameConcept,
    fetchConceptHistory,
    restoreConcept,
  } = useGameConcept()

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

  async function updateDesignIdea() {
    await pillarsApi.updateDesignIdeaAPICall(designIdea.value)
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

  async function getContextInPillarsFeedback() {
    featureFeedback.value = await pillarsApi.getContextInPillarsAPICall(additionalFeature.value)
  }

  // --- Evaluation methods (supports monolithic and agentic modes) ---

  async function evaluateAll(mode?: ExecutionMode) {
    isEvaluating.value = true
    evaluationError.value = null
    const modeToUse = mode ?? executionMode.value
    try {
      evaluationResult.value = await pillarsApi.evaluateAllAPICall(modeToUse)
    } catch (err) {
      console.error('Error evaluating pillars:', err)
      evaluationError.value = 'Failed to evaluate pillars. Please try again.'
    } finally {
      isEvaluating.value = false
    }
  }

  function setExecutionMode(mode: ExecutionMode) {
    executionMode.value = mode
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
    // Game concept history
    conceptHistory,
    isLoadingHistory,
    isRestoringConcept,
    fetchConceptHistory,
    restoreConcept,
    // Pillar-specific state
    featureFeedback,
    additionalFeature,
    // Pillar operations
    validatePillar,
    updateDesignIdea,
    fixPillarWithAI,
    acceptPillarFix,
    getContextInPillarsFeedback,
    // Evaluation (monolithic + agentic)
    evaluationResult,
    isEvaluating,
    evaluationError,
    executionMode,
    evaluateAll,
    setExecutionMode,
    resolveContradictions,
    acceptAddition,
    clearEvaluation,
  }
}
