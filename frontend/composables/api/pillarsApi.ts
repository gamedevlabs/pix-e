export function usePillarsApi() {
  const config = useRuntimeConfig()

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
      await $fetch<LLMFeedback>(`${config.public.apiBase}/llm/feedback/`, {
        method: 'GET',
        credentials: 'include',
      })
    ).feedback
  }

  async function validatePillarAPICall(pillar: Pillar) {
    pillar.llm_feedback = (
      await $fetch<LLMFeedback>(
        `${config.public.apiBase}/llm/pillars/${pillar.pillar_id}/validate/`,
        {
          method: 'GET',
          credentials: 'include',
        },
      )
    ).feedback
    pillar.display_open = true
  }

  return {
    updateDesignIdeaAPICall,
    validatePillarAPICall,
    getLLMFeedback,
  }
}
