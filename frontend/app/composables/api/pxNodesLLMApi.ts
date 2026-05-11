import { useApi } from '~/composables/useApi'

export function usePxNodesLLMApi() {
  const { apiFetch } = useApi()
  const llm = useLLM()

  async function validateNodeAPICall(nodeId: string): Promise<NodeValidationFeedback> {
    return await apiFetch<NodeValidationFeedback>(
      `/api/llm/nodes/${nodeId}/validate/`,
      {
        method: 'POST',
        body: {
          model: llm.active_llm,
        },
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      },
    )
  }

  async function fixNodeWithAIAPICall(
    nodeId: string,
    validationIssues: NodeCoherenceIssue[] = [],
  ): Promise<FixNodeAPIResponse> {
    return await apiFetch<FixNodeAPIResponse>(
      `/api/llm/nodes/${nodeId}/fix/`,
      {
        method: 'POST',
        body: {
          model: llm.active_llm,
          validation_issues: validationIssues.map((issue) => ({
            title: issue.title,
            description: issue.description,
          })),
        },
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      },
    )
  }

  async function acceptNodeFixAPICall(
    nodeId: string,
    name: string,
    description: string,
    components: { id: string; value: string | number | boolean | null }[] = [],
  ): Promise<PxNode> {
    return await apiFetch<PxNode>(`/api/llm/nodes/${nodeId}/accept-fix/`, {
      method: 'POST',
      body: {
        name,
        description,
        components,
      },
      credentials: 'include',
      headers: {
        'X-CSRFToken': useCookie('csrftoken').value,
      } as HeadersInit,
    })
  }

  return {
    validateNodeAPICall,
    fixNodeWithAIAPICall,
    acceptNodeFixAPICall,
  }
}
