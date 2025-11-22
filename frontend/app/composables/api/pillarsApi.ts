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

  async function getPillarsInContextAPICall() {
    return await $fetch<PillarsInContextFeedback>(
      `${config.public.apiBase}/llm/feedback/overall/`,
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

  async function getPillarsContradictionsAPICall() {
    return await $fetch<PillarContradictionsFeedback>(
      `${config.public.apiBase}/llm/feedback/contradictions/`,
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

  async function getPillarsCompletenessAPICall() {
    return await $fetch<PillarCompletenessFeedback>(
      `${config.public.apiBase}/llm/feedback/completeness/`,
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

  async function getPillarsAdditionsAPICall() {
    return await $fetch<PillarAdditionsFeedback>(
      `${config.public.apiBase}/llm/feedback/additions/`,
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

  async function fixPillarWithAIAPICall(
    pillar: Pillar,
    validationIssues: StructuralIssue[] = [],
  ) {
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
    return await $fetch<Pillar>(
      `${config.public.apiBase}/llm/pillars/${pillarId}/accept-fix/`,
      {
        method: 'POST',
        body: {
          name,
          description,
        },
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      },
    )
  }

  async function getContextInPillarsAPICall(context: string) {
    return await $fetch<ContextInPillarsFeedback>(
      `${config.public.apiBase}/llm/feedback/context/`,
      {
        method: 'POST',
        body: {
          model: llm.active_llm,
          context: context,
        },
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      },
    )
  }

  return {
    updateDesignIdeaAPICall,
    validatePillarAPICall,
    getPillarsInContextAPICall,
    getPillarsContradictionsAPICall,
    getPillarsCompletenessAPICall,
    getPillarsAdditionsAPICall,
    fixPillarWithAIAPICall,
    acceptPillarFixAPICall,
    getContextInPillarsAPICall,
  }
}
