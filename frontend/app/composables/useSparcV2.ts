import { useSparcV2Api, type ProgressEvent } from '~/composables/api/sparcV2Api'

// Shared state for SPARC V2
const v2Result = ref<SPARCV2Response | null>(null)
const isEvaluating = ref(false)
const evaluationError = ref<string | null>(null)
const reEvaluatingAspect = ref<string | null>(null)
const progressMessage = ref<string | null>(null)
const progressCurrent = ref<number>(0)
const progressTotal = ref<number>(10)
const pillarMode = ref<PillarMode>('smart')
const contextStrategy = ref<SparcContextStrategy>('router')
const uploadedDocument = ref<File | null>(null)

export function useSparcV2() {
  const api = useSparcV2Api()
  const { gameConcept, context } = useSparc()
  const toast = usePixeToast()
  const toastDirect = useToast()

  async function runV2Evaluation() {
    if (!gameConcept.value?.trim()) {
      toastDirect.add({
        title: 'Warning',
        description: 'Please enter a game concept first',
        color: 'warning',
      })
      return
    }

    isEvaluating.value = true
    evaluationError.value = null
    progressMessage.value = 'Initializing evaluation...'
    progressCurrent.value = 0
    progressTotal.value = 10

    try {
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
    } catch (error) {
      evaluationError.value = error instanceof Error ? error.message : 'Evaluation failed'
      toast.error('Evaluation failed: ' + evaluationError.value)
    } finally {
      isEvaluating.value = false
    }
  }

  async function runAspectEvaluation(aspect: SPARCV2AspectName) {
    if (!gameConcept.value?.trim()) {
      toastDirect.add({
        title: 'Warning',
        description: 'Please enter a game concept first',
        color: 'warning',
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

      toast.success(`${formatAspectName(aspect)} re-evaluated!`)
    } catch (error) {
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
    pillarMode,
    contextStrategy,
    uploadedDocument,

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
