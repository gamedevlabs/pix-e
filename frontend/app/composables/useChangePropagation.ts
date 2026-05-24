import { usePxNodesLLMApi } from '@/composables/api/pxNodesLLMApi'

export function useChangePropagation() {
  const pxNodesLLMApi = usePxNodesLLMApi()
  const { success, error: errorToast } = usePixeToast()

  const checking = ref(false)
  const report = ref<PropagationReport | null>(null)

  async function checkPropagation(payload: {
    projectId: string
    nodeId: string
    oldDescription: string
    newDescription: string
  }): Promise<PropagationReport | null> {
    checking.value = true
    report.value = null
    try {
      const result = await pxNodesLLMApi.checkPropagationAPICall(payload)
      report.value = result
      const count = result.findings.length
      if (count === 0) {
        success('No other nodes are affected by this change.')
      } else {
        success(`${count} node${count === 1 ? '' : 's'} may need updating after this change.`)
      }
      return result
    } catch (err) {
      console.error('Error running change propagation check:', err)
      errorToast(err)
      return null
    } finally {
      checking.value = false
    }
  }

  function clearReport() {
    report.value = null
  }

  return { checking, report, checkPropagation, clearReport }
}
