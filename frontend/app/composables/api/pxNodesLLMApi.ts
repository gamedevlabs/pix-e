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
    strategy?: PropagationStrategy
    semanticTopK?: number
    maxDepth?: number
  }): Promise<PropagationReport> {
    return await apiFetch<PropagationReport>(`/api/llm/propagation/check/`, {
      method: 'POST',
      body: {
        project_id: payload.projectId,
        node_id: payload.nodeId,
        old_description: payload.oldDescription,
        new_description: payload.newDescription,
        min_confidence: payload.minConfidence ?? 0.0,
        strategy: payload.strategy ?? 'flat',
        semantic_top_k: payload.semanticTopK ?? 10,
        max_depth: payload.maxDepth ?? 3,
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

  async function fixPropagationNodeAPICall(
    affectedNodeId: string,
    changedNodeId: string,
    changedNodeOldDescription: string,
    changedNodeNewDescription: string,
  ): Promise<PropagationFixResponse> {
    return await apiFetch<PropagationFixResponse>(`/api/llm/propagation/fix/`, {
      method: 'POST',
      body: {
        affected_node_id: affectedNodeId,
        changed_node_id: changedNodeId,
        changed_node_old_description: changedNodeOldDescription,
        changed_node_new_description: changedNodeNewDescription,
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
    layers: 'all' | 'structural' | 'semantic' = 'all',
  ): Promise<ConsistencyReport> {
    return await apiFetch<ConsistencyReport>(`/api/llm/consistency/check/`, {
      method: 'POST',
      body: {
        project_id: projectId,
        min_confidence: minConfidence,
        layers,
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
    fixPropagationNodeAPICall,
  }
}
