import type { LLMFeedback, Pillar } from '~/types/pillars'

export function usePillarsApi() {
  const config = useRuntimeConfig()

  async function createPillarInBackend() {
    const pillar: Pillar = {
      pillar_id: 0, // Placeholder, will be replaced by the backend
      description: 'Placeholder',
    }
    return await $fetch<Pillar>(`${config.public.apiBase}/llm/pillars/`, {
      method: 'POST',
      body: JSON.stringify(pillar),
      credentials: 'include',
    })
  }

  async function updatePillarInBackend(pillar: Pillar) {
    await $fetch(`${config.public.apiBase}/llm/pillars/${pillar.pillar_id}/`, {
      method: 'PUT',
      body: JSON.stringify(pillar),
      credentials: 'include',
    })
  }

  async function deletePillarInBackend(pillar: Pillar) {
    try {
      await $fetch(`${config.public.apiBase}/llm/pillars/${pillar.pillar_id}/`, {
        method: 'DELETE',
        credentials: 'include',
      })
    } catch (error) {
      console.error('Error fetching:', error)
    }
  }

  async function updateDesignIdeaInBackend(designIdea: string) {
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

  return {
    createPillarInBackend,
    updatePillarInBackend,
    deletePillarInBackend,
    updateDesignIdeaInBackend,
    getLLMFeedback,
  }
}
