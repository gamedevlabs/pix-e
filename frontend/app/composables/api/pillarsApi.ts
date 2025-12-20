export function usePillarsApi() {
  const config = useRuntimeConfig()
  const llm = useLLM()

  async function updateDesignIdeaAPICall(designIdea: string) {
    if (designIdea.trim() === '') return
    try {
      await $fetch(`${config.public.apiBase}/llm/design/`, {
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

  async function validatePillarAPICall(pillar: Pillar) {
    pillar.llm_feedback = await $fetch<PillarFeedback>(
      `${config.public.apiBase}/llm/pillars/${pillar.id}/validate/`,
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

  async function fixPillarWithAIAPICall(pillar: Pillar, validationIssues: StructuralIssue[] = []) {
    return await $fetch<FixPillarAPIResponse>(
      `${config.public.apiBase}/llm/pillars/${pillar.id}/fix/`,
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

  async function acceptPillarFixAPICall(pillarId: number, name: string, description: string) {
    return await $fetch<Pillar>(`${config.public.apiBase}/llm/pillars/${pillarId}/accept-fix/`, {
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

  async function getContextInPillarsAPICall(
    context: string,
    contextStrategy: PillarsContextStrategy = 'raw',
  ) {
    return await $fetch<ContextInPillarsFeedback>(
      `${config.public.apiBase}/llm/feedback/context/`,
      {
        method: 'POST',
        body: {
          model: llm.active_llm,
          context: context,
          context_strategy: contextStrategy,
        },
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      },
    )
  }

  // --- New agentic evaluation endpoints ---

  async function evaluateAllAPICall(
    executionMode: ExecutionMode = 'agentic',
    contextStrategy: PillarsContextStrategy = 'raw',
  ) {
    return await $fetch<EvaluateAllResponse>(
      `${config.public.apiBase}/llm/feedback/evaluate-all/`,
      {
        method: 'POST',
        body: {
          model: llm.active_llm,
          execution_mode: executionMode,
          context_strategy: contextStrategy,
        },
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      },
    )
  }

  async function resolveContradictionsAPICall(
    contradictions: ContradictionsResponse,
    contextStrategy: PillarsContextStrategy = 'raw',
  ) {
    return await $fetch<ContradictionResolutionResponse>(
      `${config.public.apiBase}/llm/feedback/resolve-contradictions/`,
      {
        method: 'POST',
        body: {
          model: llm.active_llm,
          contradictions: contradictions,
          context_strategy: contextStrategy,
        },
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      },
    )
  }

  async function acceptAdditionAPICall(name: string, description: string) {
    return await $fetch<Pillar>(`${config.public.apiBase}/llm/feedback/accept-addition/`, {
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
