import { usePxNodesLLMApi } from '@/composables/api/pxNodesLLMApi'

export function usePxNodesLLM() {
  const pxNodesLLMApi = usePxNodesLLMApi()
  const { success, error: errorToast } = usePixeToast()
  const { addLog } = useSessionLog()

  async function validateNode(nodeId: string): Promise<NodeValidationFeedback | null> {
    addLog('info', 'px_node_validation_started', { nodeId })

    try {
      const result = await pxNodesLLMApi.validateNodeAPICall(nodeId)
      addLog('info', 'px_node_validation_succeeded', {
        nodeId,
      })

      return result
    } catch (err) {
      addLog('error', 'px_node_validation_failed', {
        nodeId,
        message: err instanceof Error ? err.message : String(err),
      })
      console.error('Error validating node:', err)
      errorToast(err)
      return null
    }
  }

  async function fixNodeWithAI(
    nodeId: string,
    validationIssues: NodeCoherenceIssue[] = [],
  ): Promise<FixNodeAPIResponse | null> {
    addLog('info', 'px_node_ai_fix_started', {
      nodeId,
      issueCount: validationIssues.length,
    })

    try {
      const result = await pxNodesLLMApi.fixNodeWithAIAPICall(nodeId, validationIssues)

      addLog('info', 'px_node_ai_fix_succeeded', {
        nodeId,
      })

      return result
    } catch (err) {
      addLog('error', 'px_node_ai_fix_failed', {
        nodeId,
        issueCount: validationIssues.length,
        message: err instanceof Error ? err.message : String(err),
      })
      console.error('Error fixing node with AI:', err)
      errorToast(err)
      return null
    }
  }

  async function acceptNodeFix(
    nodeId: string,
    name: string,
    description: string,
    components: { id: string; value: string | number | boolean | null }[] = [],
  ): Promise<PxNode | null> {
    addLog('info', 'px_node_fix_accept_started', {
      nodeId,
      hasName: name.trim().length > 0,
      hasDescription: description.trim().length > 0,
      componentCount: components.length,
    })

    try {
      const result = await pxNodesLLMApi.acceptNodeFixAPICall(nodeId, name, description, components)
      success('Node updated successfully!')
      addLog('info', 'px_node_fix_accept_succeeded', {
        nodeId,
        componentCount: components.length,
      })
      return result
    } catch (err) {
      addLog('error', 'px_node_fix_accept_failed', {
        nodeId,
        componentCount: components.length,
        message: err instanceof Error ? err.message : String(err),
      })
      console.error('Error accepting node fix:', err)
      errorToast(err)
      return null
    }
  }

  return {
    validateNode,
    fixNodeWithAI,
    acceptNodeFix,
  }
}
