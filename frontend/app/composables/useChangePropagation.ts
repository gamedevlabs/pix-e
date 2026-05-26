import { usePxNodesLLMApi } from '@/composables/api/pxNodesLLMApi'
import { useApi } from '@/composables/useApi'

type PropagationFixState = {
  loading: boolean
  suggestion: string | null
  originalDescription: string | null
}

export function useChangePropagation() {
  const pxNodesLLMApi = usePxNodesLLMApi()
  const { apiFetch } = useApi()
  const { success, error: errorToast } = usePixeToast()

  const checking = ref(false)
  const report = ref<PropagationReport | null>(null)
  const propagationFixSuggestions = ref<Record<string, PropagationFixState>>({})

  async function checkPropagation(payload: {
    projectId: string
    nodeId: string
    oldDescription: string
    newDescription: string
  }): Promise<PropagationReport | null> {
    checking.value = true
    report.value = null
    propagationFixSuggestions.value = {}
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
    propagationFixSuggestions.value = {}
  }

  async function requestPropagationFix(
    affectedNodeId: string,
    changedNodeId: string,
    oldDescription: string,
    newDescription: string,
  ) {
    propagationFixSuggestions.value[affectedNodeId] = {
      loading: true,
      suggestion: null,
      originalDescription: null,
    }
    try {
      const result = await pxNodesLLMApi.fixPropagationNodeAPICall(
        affectedNodeId,
        changedNodeId,
        oldDescription,
        newDescription,
      )
      propagationFixSuggestions.value[affectedNodeId] = {
        loading: false,
        suggestion: result.suggested_description,
        originalDescription: result.original_description,
      }
    } catch (err) {
      console.error('Error requesting propagation fix:', err)
      errorToast(err)
      delete propagationFixSuggestions.value[affectedNodeId]
    }
  }

  async function applyPropagationFix(affectedNodeId: string, suggestedDescription: string) {
    try {
      await apiFetch(`/api/pxnodes/${affectedNodeId}/`, {
        method: 'PATCH',
        body: { description: suggestedDescription },
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      })
      delete propagationFixSuggestions.value[affectedNodeId]
      if (report.value) {
        report.value = {
          ...report.value,
          findings: report.value.findings.filter((f) => f.affected_node_id !== affectedNodeId),
        }
      }
      success('Fix applied successfully.')
    } catch (err) {
      console.error('Failed to apply propagation fix:', err)
      errorToast(err)
    }
  }

  function dismissPropagationFix(affectedNodeId: string) {
    delete propagationFixSuggestions.value[affectedNodeId]
  }

  return {
    checking,
    report,
    propagationFixSuggestions,
    checkPropagation,
    clearReport,
    requestPropagationFix,
    applyPropagationFix,
    dismissPropagationFix,
  }
}
