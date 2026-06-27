import { usePxNodesLLMApi } from '@/composables/api/pxNodesLLMApi'
import { useApi } from '@/composables/useApi'

type FixState = {
  loading: boolean
  suggestion: string | null
  originalDescription: string | null
}

function findingKey(finding: ConsistencyFinding): string {
  return `${finding.entity_id}|${finding.category}|${finding.message}`
}

export function useConsistency() {
  const pxNodesLLMApi = usePxNodesLLMApi()
  const { apiFetch } = useApi()
  const { success, error: errorToast } = usePixeToast()

  const checking = ref(false)
  const report = ref<ConsistencyReport | null>(null)
  const fixSuggestions = ref<Record<string, FixState>>({})

  async function checkConsistency(
    projectId: string,
    minConfidence = 0.5,
    layers: 'all' | 'structural' | 'semantic' = 'all',
  ): Promise<ConsistencyReport | null> {
    checking.value = true
    report.value = null
    fixSuggestions.value = {}
    try {
      const result = await pxNodesLLMApi.checkConsistencyAPICall(projectId, minConfidence, layers)
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
    fixSuggestions.value = {}
  }

  async function requestFix(finding: ConsistencyFinding, projectId: string) {
    const key = findingKey(finding)
    fixSuggestions.value[key] = { loading: true, suggestion: null, originalDescription: null }
    try {
      const result = await pxNodesLLMApi.fixConsistencyFindingAPICall({
        nodeId: finding.entity_id,
        findingCategory: finding.category,
        findingDescription: finding.message,
        projectId,
      })
      fixSuggestions.value[key] = {
        loading: false,
        suggestion: result.suggested_description,
        originalDescription: result.original_description,
      }
    } catch (err) {
      console.error('Error requesting consistency fix:', err)
      errorToast(err)
      // eslint-disable-next-line @typescript-eslint/no-dynamic-delete
      delete fixSuggestions.value[key]
    }
  }

  async function applyFix(
    finding: ConsistencyFinding,
    newDescription: string,
    projectId: string,
    minConfidence = 0.5,
  ) {
    try {
      await apiFetch(`/api/pxnodes/${finding.entity_id}/`, {
        method: 'PATCH',
        body: { description: newDescription },
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      })
    } catch (err) {
      console.error('Failed to apply consistency fix:', err)
      errorToast(err)
      return
    }
    await checkConsistency(projectId, minConfidence)
  }

  function dismissFix(finding: ConsistencyFinding) {
    // eslint-disable-next-line @typescript-eslint/no-dynamic-delete
    delete fixSuggestions.value[findingKey(finding)]
  }

  return {
    checking,
    report,
    fixSuggestions,
    checkConsistency,
    clearReport,
    requestFix,
    applyFix,
    dismissFix,
  }
}
