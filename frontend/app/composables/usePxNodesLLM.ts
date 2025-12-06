import { usePxNodesLLMApi } from '@/composables/api/pxNodesLLMApi'

export function usePxNodesLLM() {
  const pxNodesLLMApi = usePxNodesLLMApi()
  const { success, error: errorToast } = usePixeToast()

  async function validateNode(nodeId: string): Promise<NodeValidationFeedback | null> {
    try {
      return await pxNodesLLMApi.validateNodeAPICall(nodeId)
    } catch (err) {
      console.error('Error validating node:', err)
      errorToast(err)
      return null
    }
  }

  async function fixNodeWithAI(
    nodeId: string,
    validationIssues: NodeCoherenceIssue[] = [],
  ): Promise<FixNodeAPIResponse | null> {
    try {
      return await pxNodesLLMApi.fixNodeWithAIAPICall(nodeId, validationIssues)
    } catch (err) {
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
    try {
      const result = await pxNodesLLMApi.acceptNodeFixAPICall(nodeId, name, description, components)
      success('Node updated successfully!')
      return result
    } catch (err) {
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
