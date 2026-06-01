import { usePillarsApi } from '@/composables/api/pillarsApi'
import { useProject } from '@/composables/useProject'
import { useApi } from '~/composables/useApi'

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
  const { apiFetch } = useApi()
  const pillarsApi = usePillarsApi()
  const { success, error: errorToast } = usePixeToast()
  const projectStore = useProject()

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
      const data = await apiFetch<Pillar[]>('/api/llm/pillars/', {
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
      const result = await apiFetch<Pillar>('/api/llm/pillars/', {
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
      await apiFetch<Pillar>(`/api/llm/pillars/${id}/`, {
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
      await apiFetch<null>(`/api/llm/pillars/${id}/`, {
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

  function extractErrorDetail(err: unknown): string {
    const data = (err as Record<string, unknown>)?.data as Record<string, unknown> | undefined
    if (data?.detail && typeof data.detail === 'string') return data.detail
    if (data?.error && typeof data.error === 'string') return data.error
    if (err instanceof Error) return err.message
    return 'An unexpected error occurred'
  }

  async function validatePillar(pillar: Pillar) {
    try {
      return await pillarsApi.validatePillarAPICall(pillar)
    } catch (err) {
      errorToast(extractErrorDetail(err))
      return undefined
    }
  }

  async function fixPillarWithAI(pillar: Pillar, validationIssues: StructuralIssue[] = []) {
    try {
      return await pillarsApi.fixPillarWithAIAPICall(pillar, validationIssues)
    } catch (err) {
      errorToast(extractErrorDetail(err))
      return undefined
    }
  }

  async function acceptPillarFix(pillarId: number, name: string, description: string) {
    return await pillarsApi.acceptPillarFixAPICall(pillarId, name, description)
  }

  async function getContextInPillarsFeedback() {
    const context = additionalFeature.value?.trim()
    if (!context) return
    try {
      featureFeedback.value = await pillarsApi.getContextInPillarsAPICall(context)
    } catch (err) {
      errorToast(extractErrorDetail(err))
    }
  }

  // --- Evaluation methods (supports monolithic and agentic modes) ---

  async function evaluateAll(mode?: ExecutionMode) {
    isEvaluating.value = true
    evaluationError.value = null
    const modeToUse = mode ?? executionMode.value
    try {
      const result = await pillarsApi.evaluateAllAPICall(modeToUse)
      evaluationResult.value = result

      // Surface agent errors when some agents failed
      const agentErrors = (result as Record<string, unknown>)?.metadata?.agent_errors as
        | Array<{ agent: string; error: string }>
        | undefined
      if (agentErrors && agentErrors.length > 0) {
        const messages = agentErrors
          .map((e) => {
            const truncated = e.error.length > 120 ? e.error.slice(0, 120) + '...' : e.error
            return `${e.agent}: ${truncated}`
          })
          .join('; ')
        errorToast(`Some agents failed: ${messages}`)
      }
    } catch (err) {
      evaluationError.value = extractErrorDetail(err)
      errorToast(evaluationError.value)
    } finally {
      isEvaluating.value = false
    }
  }

  function setExecutionMode(mode: ExecutionMode) {
    executionMode.value = mode
  }

  async function resolveContradictions(contradictions: ContradictionsResponse) {
    try {
      return await pillarsApi.resolveContradictionsAPICall(contradictions)
    } catch (err) {
      errorToast(extractErrorDetail(err))
      return undefined
    }
  }

  watch(
    () => projectStore.activeProjectId,
    async (nextId, previousId) => {
      if (previousId !== null && nextId !== previousId) {
        await fetchAll()
        await fetchGameConcept()
      }
    },
  )

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
