import { useSparcApi } from '@/composables/api/sparcApi'

export function useSparc() {
  const sparcApi = useSparcApi()

  // Use shared game concept state
  const { designIdea: gameConcept, fetchGameConcept } = useGameConcept()

  const context = ref<string>('')
  const quickScanResult = ref<SPARCQuickScanResponse | null>(null)
  const monolithicResult = ref<SPARCMonolithicResponse | null>(null)
  const evaluations = ref<SPARCEvaluation[]>([])

  const isLoadingQuickScan = ref(false)
  const isLoadingMonolithic = ref(false)

  async function runQuickScan() {
    if (gameConcept.value.trim() === '') {
      console.warn('Game concept is empty')
      return
    }

    isLoadingQuickScan.value = true
    try {
      const result = await sparcApi.runQuickScanAPICall(
        gameConcept.value.trim(),
        context.value.trim(),
      )
      quickScanResult.value = result
    } catch (error) {
      console.error('Error running quick scan:', error)
    } finally {
      isLoadingQuickScan.value = false
    }
  }

  async function runMonolithic() {
    if (gameConcept.value.trim() === '') {
      console.warn('Game concept is empty')
      return
    }

    isLoadingMonolithic.value = true
    try {
      const result = await sparcApi.runMonolithicAPICall(
        gameConcept.value.trim(),
        context.value.trim(),
      )
      monolithicResult.value = result
    } catch (error) {
      console.error('Error running monolithic:', error)
    } finally {
      isLoadingMonolithic.value = false
    }
  }

  async function loadEvaluations() {
    try {
      evaluations.value = await sparcApi.getEvaluationsAPICall()

      // Load most recent quick_scan and monolithic results
      const latestQuickScan = evaluations.value.find((e) => e.mode === 'quick_scan')
      const latestMonolithic = evaluations.value.find((e) => e.mode === 'monolithic')

      // For quick_scan, find the aggregated result
      if (latestQuickScan && latestQuickScan.aspect_results.length > 0) {
        const aggregatedResult = latestQuickScan.aspect_results.find(
          (r) => r.aspect === 'aggregated',
        )
        if (aggregatedResult && aggregatedResult.result_data) {
          quickScanResult.value = aggregatedResult.result_data as SPARCQuickScanResponse
        }
      }

      // For monolithic, get the result (should be the only one or first one)
      if (latestMonolithic && latestMonolithic.aspect_results.length > 0) {
        const monolithicData = latestMonolithic.aspect_results[0]
        if (monolithicData && monolithicData.result_data) {
          monolithicResult.value = monolithicData.result_data as SPARCMonolithicResponse
        }
      }
    } catch (error) {
      console.error('Error loading evaluations:', error)
    }
  }

  return {
    gameConcept,
    context,
    quickScanResult,
    monolithicResult,
    evaluations,
    isLoadingQuickScan,
    isLoadingMonolithic,
    fetchGameConcept,
    runQuickScan,
    runMonolithic,
    loadEvaluations,
  }
}
