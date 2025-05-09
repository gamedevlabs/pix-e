import type { LLMFeedback, Pillar, PillarDTO } from '~/types/pillars'

export function usePillarsApi() {
  const config = useRuntimeConfig()

  async function createPillarAPICall() {
    const pillar: PillarDTO = {
      pillar_id: 0,
      title: '',
      description: '',
    }
    return await $fetch<Pillar>(`${config.public.apiBase}/llm/pillars/`, {
      method: 'POST',
      body: JSON.stringify(pillar),
      credentials: 'include',
    })
  }

  async function updatePillarAPICall(pillar: Pillar) {
    const pillarDTO: PillarDTO = {
      pillar_id: pillar.pillar_id,
      title: pillar.title,
      description: pillar.descript,
    }
    await $fetch(`${config.public.apiBase}/llm/pillars/${pillar.pillar_id}/`, {
      method: 'PUT',
      body: JSON.stringify(pillarDTO),
      credentials: 'include',
    })
  }

  async function deletePillarAPICall(pillar: Pillar) {
    try {
      await $fetch(`${config.public.apiBase}/llm/pillars/${pillar.pillar_id}/`, {
        method: 'DELETE',
        credentials: 'include',
      })
    } catch (error) {
      console.error('Error fetching:', error)
    }
  }

  async function updateDesignIdeaAPICall(designIdea: string) {
    if (designIdea.trim() === '') return
    try {
      await $fetch(`${config.public.apiBase}/llm/design/0/`, {
        method: 'PUT',
        body: {
          description: designIdea.trim(),
        },
        credentials: 'include',
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
    createPillarAPICall,
    updatePillarAPICall,
    deletePillarAPICall,
    updateDesignIdeaAPICall,
    validatePillarAPICall,
    getLLMFeedback,
  }
}
