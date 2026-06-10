import { useSparcApi } from '@/composables/api/sparcApi'
import { useSparcV2Api, type ProgressEvent } from '~/composables/api/sparcV2Api'

// Shared state for SPARC V2
const v2Result = ref<SPARCV2Response | null>(null)
const isEvaluating = ref(false)
const evaluationError = ref<string | null>(null)
const reEvaluatingAspect = ref<string | null>(null)
const progressMessage = ref<string | null>(null)
const progressCurrent = ref<number>(0)
const progressTotal = ref<number>(10)
const evaluationMode = ref<SparcV2EvaluationMode>('agentic')
const pillarMode = ref<PillarMode>('smart')
const contextStrategy = ref<SparcContextStrategy>('router')
const uploadedDocument = ref<File | null>(null)
const monolithicResult = ref<SPARCMonolithicResponse | null>(null)

export function useSparcV2() {
  const api = useSparcV2Api()
  const sparcApi = useSparcApi()
  const { gameConcept, context } = useSparc()
  const toast = usePixeToast()
  const toastDirect = useToast()
  const { addLog } = useSessionLog()

  async function runV2Evaluation() {
    addLog('info', 'sparc_v2_evaluation_started', {
      evaluationMode: evaluationMode.value,
      pillarMode: pillarMode.value,
      contextStrategy: contextStrategy.value,
      hasUploadedDocument: Boolean(uploadedDocument.value),
      conceptLength: gameConcept.value.length,
      contextLength: context.value.length,
    })

    if (!gameConcept.value?.trim()) {
      toastDirect.add({
        title: 'Warning',
        description: 'Please enter a game concept first',
        color: 'warning',
      })
      addLog('warn', 'sparc_evaluation_blocked', {
        reason: 'missing_game_concept',
        evaluationMode: evaluationMode.value,
      })
      return
    }

    try {
      if (evaluationMode.value === 'monolithic') {
        await runMonolithicEvaluation()
        return
      }

      isEvaluating.value = true
      evaluationError.value = null
      progressMessage.value = 'Initializing evaluation...'
      progressCurrent.value = 0
      progressTotal.value = 10

      await api.runV2EvaluateStreamAPICall(
        gameConcept.value,
        context.value,
        pillarMode.value,
        contextStrategy.value,
        (event: ProgressEvent) => {
          // Handle progress updates
          progressMessage.value = event.message
          if (event.current !== undefined) {
            progressCurrent.value = event.current
          }
          if (event.total !== undefined) {
            progressTotal.value = event.total
          }
        },
        (result: SPARCV2Response) => {
          // Handle completion
          v2Result.value = result
          progressMessage.value = 'Evaluation complete!'
          toast.success('V2 Evaluation complete!')
        },
        (error: string) => {
          // Handle error
          evaluationError.value = error
          toast.error('Evaluation failed: ' + error)
        },
        uploadedDocument.value, // Pass the uploaded document
      )
      addLog('info', 'sparc_v2_evaluation_succeeded', {
        evaluationMode: evaluationMode.value,
      })
    } catch (error) {
      addLog('error', 'sparc_v2_evaluation_failed', {
        evaluationMode: evaluationMode.value,
        message: error instanceof Error ? error.message : String(error),
      })
      evaluationError.value = error instanceof Error ? error.message : 'Evaluation failed'
      toast.error('Evaluation failed: ' + evaluationError.value)
    } finally {
      isEvaluating.value = false
    }
  }

  async function runMonolithicEvaluation() {
    addLog('info', 'sparc_monolithic_evaluation_started', {
      conceptLength: gameConcept.value.length,
      contextLength: context.value.length,
    })

    isEvaluating.value = true
    evaluationError.value = null
    progressMessage.value = 'Running monolithic evaluation...'
    progressCurrent.value = 0
    progressTotal.value = 0

    try {
      const result = await sparcApi.runMonolithicAPICall(gameConcept.value, context.value)
      monolithicResult.value = result
      progressMessage.value = 'Evaluation complete!'
      toast.success('Monolithic evaluation complete!')

      addLog('info', 'sparc_monolithic_evaluation_succeeded')
    } catch (error) {
      addLog('error', 'sparc_monolithic_evaluation_failed', {
        message: error instanceof Error ? error.message : String(error),
      })
      evaluationError.value = error instanceof Error ? error.message : 'Evaluation failed'
      toast.error('Evaluation failed: ' + evaluationError.value)
    } finally {
      isEvaluating.value = false
    }
  }

  async function runAspectEvaluation(aspect: SPARCV2AspectName) {
    addLog('info', 'sparc_aspect_evaluation_started', {
      aspect,
      contextStrategy: contextStrategy.value,
    })

    if (!gameConcept.value?.trim()) {
      toastDirect.add({
        title: 'Warning',
        description: 'Please enter a game concept first',
        color: 'warning',
      })
      addLog('warn', 'sparc_evaluation_blocked', {
        reason: 'missing_game_concept',
        evaluationMode: evaluationMode.value,
      })
      return
    }

    reEvaluatingAspect.value = aspect

    try {
      const result = await api.runV2AspectAPICall(
        gameConcept.value,
        aspect,
        context.value,
        contextStrategy.value,
      )

      // Merge the new aspect result into existing results
      if (v2Result.value) {
        v2Result.value = {
          ...v2Result.value,
          aspect_results: {
            ...v2Result.value.aspect_results,
            ...result.aspect_results,
          },
        }
      } else {
        v2Result.value = result
      }

      addLog('info', 'sparc_aspect_evaluation_succeeded', {
        aspect,
      })
      toast.success(`${formatAspectName(aspect)} re-evaluated!`)
    } catch (error) {
      addLog('error', 'sparc_aspect_evaluation_failed', {
        aspect,
        message: error instanceof Error ? error.message : String(error),
      })
      const msg = error instanceof Error ? error.message : 'Re-evaluation failed'
      toast.error(msg)
    } finally {
      reEvaluatingAspect.value = null
    }
  }

  function clearV2Results() {
    v2Result.value = null
    evaluationError.value = null
  }

  // Computed helpers
  const hasV2Results = computed(() => v2Result.value !== null)

  const aspectResultsList = computed(() => {
    if (!v2Result.value) return []

    return Object.entries(v2Result.value.aspect_results).map(([name, result]) => ({
      name,
      ...result,
    }))
  })

  const sortedAspectResults = computed(() => {
    const results = aspectResultsList.value
    const statusOrder: Record<SPARCV2Status, number> = {
      well_defined: 0,
      needs_work: 1,
      not_provided: 2,
    }
    return [...results].sort((a, b) => statusOrder[a.status] - statusOrder[b.status])
  })

  const wellDefinedCount = computed(
    () => aspectResultsList.value.filter((r) => r.status === 'well_defined').length,
  )

  const needsWorkCount = computed(
    () => aspectResultsList.value.filter((r) => r.status === 'needs_work').length,
  )

  const notProvidedCount = computed(
    () => aspectResultsList.value.filter((r) => r.status === 'not_provided').length,
  )

  return {
    // State
    v2Result,
    isEvaluating,
    evaluationError,
    reEvaluatingAspect,
    progressMessage,
    progressCurrent,
    progressTotal,
    evaluationMode,
    pillarMode,
    contextStrategy,
    uploadedDocument,
    monolithicResult,

    // Actions
    runV2Evaluation,
    runAspectEvaluation,
    clearV2Results,

    // Computed
    hasV2Results,
    aspectResultsList,
    sortedAspectResults,
    wellDefinedCount,
    needsWorkCount,
    notProvidedCount,
  }
}

// Helper function to format aspect names for display
export function formatAspectName(aspect: string): string {
  return aspect
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

// Helper to get status color
export function getStatusColor(
  status: SPARCV2Status,
): 'primary' | 'secondary' | 'success' | 'info' | 'warning' | 'error' | 'neutral' {
  switch (status) {
    case 'well_defined':
      return 'success'
    case 'needs_work':
      return 'warning'
    case 'not_provided':
      return 'neutral'
  }
}

// Helper to get status icon
export function getStatusIcon(status: SPARCV2Status): string {
  switch (status) {
    case 'well_defined':
      return 'i-heroicons-check-circle'
    case 'needs_work':
      return 'i-heroicons-exclamation-triangle'
    case 'not_provided':
      return 'i-heroicons-minus-circle'
  }
}
