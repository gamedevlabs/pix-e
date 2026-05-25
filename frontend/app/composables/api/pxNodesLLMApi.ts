import { useApi } from '~/composables/useApi'

export function usePxNodesLLMApi() {
  const { apiFetch } = useApi()
  const llm = useLLM()

  async function validateNodeAPICall(nodeId: string): Promise<NodeValidationFeedback> {
    return await apiFetch<NodeValidationFeedback>(`/api/llm/nodes/${nodeId}/validate/`, {
      method: 'POST',
      body: {
        model: llm.active_llm,
      },
      credentials: 'include',
      headers: {
        'X-CSRFToken': useCookie('csrftoken').value,
      } as HeadersInit,
    })
  }

  async function fixNodeWithAIAPICall(
    nodeId: string,
    validationIssues: NodeCoherenceIssue[] = [],
  ): Promise<FixNodeAPIResponse> {
    return await apiFetch<FixNodeAPIResponse>(`/api/llm/nodes/${nodeId}/fix/`, {
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

  async function checkPropagationAPICall(payload: {
    projectId: string
    nodeId: string
    oldDescription: string
    newDescription: string
    minConfidence?: number
  }): Promise<PropagationReport> {
    return await apiFetch<PropagationReport>(`/api/llm/propagation/check/`, {
      method: 'POST',
      body: {
        project_id: payload.projectId,
        node_id: payload.nodeId,
        old_description: payload.oldDescription,
        new_description: payload.newDescription,
        min_confidence: payload.minConfidence ?? 0.5,
      },
      credentials: 'include',
      headers: {
        'X-CSRFToken': useCookie('csrftoken').value,
      } as HeadersInit,
    })
  }

  async function fixConsistencyFindingAPICall(payload: {
    nodeId: string
    findingCategory: string
    findingDescription: string
    projectId: string
  }): Promise<ConsistencyFixResponse> {
    return await apiFetch<ConsistencyFixResponse>(`/api/llm/consistency/fix/`, {
      method: 'POST',
      body: {
        node_id: payload.nodeId,
        finding_category: payload.findingCategory,
        finding_description: payload.findingDescription,
        project_id: payload.projectId,
      },
      credentials: 'include',
      headers: {
        'X-CSRFToken': useCookie('csrftoken').value,
      } as HeadersInit,
    })
  }

  async function checkConsistencyAPICall(
    projectId: string,
    minConfidence: number = 0.5,
  ): Promise<ConsistencyReport> {
    return await apiFetch<ConsistencyReport>(`/api/llm/consistency/check/`, {
      method: 'POST',
      body: {
        project_id: projectId,
        min_confidence: minConfidence,
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
    checkConsistencyAPICall,
    checkPropagationAPICall,
    fixConsistencyFindingAPICall,
  }
}
