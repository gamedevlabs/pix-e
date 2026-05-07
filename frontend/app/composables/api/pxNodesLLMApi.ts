export function usePxNodesLLMApi() {
  const config = useRuntimeConfig()
  const llm = useLLM()

  async function validateNodeAPICall(nodeId: string): Promise<NodeValidationFeedback> {
    return await $fetch<NodeValidationFeedback>(
      `${config.public.apiBase}/llm/nodes/${nodeId}/validate/`,
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
    return await $fetch<FixNodeAPIResponse>(`${config.public.apiBase}/llm/nodes/${nodeId}/fix/`, {
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
    })
  }

  async function acceptNodeFixAPICall(
    nodeId: string,
    name: string,
    description: string,
    components: { id: string; value: string | number | boolean | null }[] = [],
  ): Promise<PxNode> {
    return await $fetch<PxNode>(`${config.public.apiBase}/llm/nodes/${nodeId}/accept-fix/`, {
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
