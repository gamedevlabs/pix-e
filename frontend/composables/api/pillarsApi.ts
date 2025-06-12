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

  async function getLLMFeedback() {
    return (
      await $fetch<PillarFeedback>(`${config.public.apiBase}/llm/feedback/`, {
        method: 'POST',
        body: {
          model: llm.active_llm,
        },
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').valu,
        } as HeadersIni,
      })
    ).content_feedback
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
          'X-CSRFToken': useCookie('csrftoken').valu,
        } as HeadersIni,
      },
    )
  }

  async function fixPillarWithAIAPICall(pillar: Pillar) {
    return await $fetch<PillarDTO>(`${config.public.apiBase}/llm/pillars/${pillar.id}/fix/`, {
      method: 'POST',
      body: pillar,
      credentials: 'include',
      headers: {
        'X-CSRFToken': useCookie('csrftoken').value,
      } as HeadersInit,
    })
  }
  return {
    updateDesignIdeaAPICall,
    validatePillarAPICall,
    getLLMFeedback,
    fixPillarWithAIAPICal,
  }
}
