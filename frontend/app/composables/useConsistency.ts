import { usePxNodesLLMApi } from '@/composables/api/pxNodesLLMApi'

export function useConsistency() {
  const pxNodesLLMApi = usePxNodesLLMApi()
  const { success, error: errorToast } = usePixeToast()

  const checking = ref(false)
  const report = ref<ConsistencyReport | null>(null)

  async function checkConsistency(
    projectId: string,
    minConfidence = 0.5,
  ): Promise<ConsistencyReport | null> {
    checking.value = true
    report.value = null
    try {
      const result = await pxNodesLLMApi.checkConsistencyAPICall(projectId, minConfidence)
      report.value = result
      const count = result.findings.length
      if (count === 0) {
        success('No consistency issues found!')
      } else {
        success(`Found ${count} consistency issue${count === 1 ? '' : 's'}.`)
      }
      return result
    } catch (err) {
      console.error('Error running consistency check:', err)
      errorToast(err)
      return null
    } finally {
      checking.value = false
    }
  }

  function clearReport() {
    report.value = null
  }

  return { checking, report, checkConsistency, clearReport }
}
