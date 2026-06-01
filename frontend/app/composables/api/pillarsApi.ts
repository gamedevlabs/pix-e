import { useApi } from '~/composables/useApi'

export function usePillarsApi() {
  const { apiFetch } = useApi()
  const llm = useLLM()

  async function updateDesignIdeaAPICall(designIdea: string) {
    if (designIdea.trim() === '') return
    try {
      await apiFetch('/api/llm/design/', {
        method: 'PUT',
        body: {
          description: designIdea.trim(),
        },
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      })
    } catch (error) {
      console.error('Error fetching:', error)
    }
  }

  function modelBody(): { model: string | undefined; api_key_id: string | null } {
    return { model: llm.activeModelName || undefined, api_key_id: llm.activeKeyId }
  }

  async function validatePillarAPICall(pillar: Pillar) {
    pillar.llm_feedback = await apiFetch<PillarFeedback>(
      `/api/llm/pillars/${pillar.id}/validate/`,
      {
        method: 'POST',
        body: {
          ...modelBody(),
        },
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      },
    )
  }

  async function fixPillarWithAIAPICall(pillar: Pillar, validationIssues: StructuralIssue[] = []) {
    return await apiFetch<FixPillarAPIResponse>(`/api/llm/pillars/${pillar.id}/fix/`, {
      method: 'POST',
      body: {
        ...modelBody(),
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

  async function acceptPillarFixAPICall(pillarId: number, name: string, description: string) {
    return await apiFetch<Pillar>(`/api/llm/pillars/${pillarId}/accept-fix/`, {
      method: 'POST',
      body: {
        name,
        description,
      },
      credentials: 'include',
      headers: {
        'X-CSRFToken': useCookie('csrftoken').value,
      } as HeadersInit,
    })
  }

  async function getContextInPillarsAPICall(context: string) {
    return await apiFetch<ContextInPillarsFeedback>(`/api/llm/feedback/context/`, {
      method: 'POST',
      body: {
        ...modelBody(),
        context: context,
      },
      credentials: 'include',
      headers: {
        'X-CSRFToken': useCookie('csrftoken').value,
      } as HeadersInit,
    })
  }

  // --- New agentic evaluation endpoints ---

  async function evaluateAllAPICall(executionMode: ExecutionMode = 'agentic') {
    return await apiFetch<EvaluateAllResponse>(`/api/llm/feedback/evaluate-all/`, {
      method: 'POST',
      body: {
        ...modelBody(),
        execution_mode: executionMode,
      },
      credentials: 'include',
      headers: {
        'X-CSRFToken': useCookie('csrftoken').value,
      } as HeadersInit,
    })
  }

  async function resolveContradictionsAPICall(contradictions: ContradictionsResponse) {
    return await apiFetch<ContradictionResolutionResponse>(
      `/api/llm/feedback/resolve-contradictions/`,
      {
        method: 'POST',
        body: {
          ...modelBody(),
          contradictions: contradictions,
        },
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      },
    )
  }

  async function acceptAdditionAPICall(name: string, description: string) {
    return await apiFetch<Pillar>(`/api/llm/feedback/accept-addition/`, {
      method: 'POST',
      body: {
        name,
        description,
      },
      credentials: 'include',
      headers: {
        'X-CSRFToken': useCookie('csrftoken').value,
      } as HeadersInit,
    })
  }

  return {
    updateDesignIdeaAPICall,
    validatePillarAPICall,
    fixPillarWithAIAPICall,
    acceptPillarFixAPICall,
    getContextInPillarsAPICall,
    // Unified evaluation (monolithic + agentic)
    evaluateAllAPICall,
    resolveContradictionsAPICall,
    acceptAdditionAPICall,
  }
}
