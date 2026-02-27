import { useProjectDataProvider } from '~/studyMock'

export function usePillarsApi() {
  // Helper: load current pillars + design idea from the mock store
  async function getContext() {
    const provider = useProjectDataProvider()
    const pillars = (await provider.getEntities('pillars')) as Pillar[]
    const designState = await provider.getEntities('design')
    const designIdea =
      (designState[0] as Record<string, unknown>)?.description as string | undefined ?? ''
    return { pillars, designIdea }
  }

  // updateDesignIdea is now purely local – persist to mock store
  async function updateDesignIdeaAPICall(designIdea: string) {
    if (designIdea.trim() === '') return
    try {
      const provider = useProjectDataProvider()
      const existing = await provider.getEntities('design')
      if (existing.length > 0) {
        const id = String((existing[0] as Record<string, unknown>).id)
        await provider.updateEntity('design', id, { description: designIdea.trim() })
      } else {
        await provider.createEntity('design', { description: designIdea.trim() })
      }
    } catch (error) {
      console.error('Error saving design idea:', error)
    }
  }

  async function getPillarsInContextAPICall() {
    const { pillars, designIdea } = await getContext()
    return await $fetch<PillarsInContextFeedback>('/api/llm/feedback/overall', {
      method: 'POST',
      body: { pillars, designIdea },
    })
  }

  async function getPillarsContradictionsAPICall() {
    const { pillars, designIdea } = await getContext()
    return await $fetch<PillarContradictionsFeedback>('/api/llm/feedback/contradictions', {
      method: 'POST',
      body: { pillars, designIdea },
    })
  }

  async function getPillarsCompletenessAPICall() {
    const { pillars, designIdea } = await getContext()
    return await $fetch<PillarCompletenessFeedback>('/api/llm/feedback/completeness', {
      method: 'POST',
      body: { pillars, designIdea },
    })
  }

  async function getPillarsAdditionsAPICall() {
    const { pillars, designIdea } = await getContext()
    return await $fetch<PillarAdditionsFeedback>('/api/llm/feedback/additions', {
      method: 'POST',
      body: { pillars, designIdea },
    })
  }

  async function validatePillarAPICall(pillar: Pillar) {
    pillar.llm_feedback = await $fetch<PillarFeedback>('/api/llm/pillars/validate', {
      method: 'POST',
      body: { name: pillar.name, description: pillar.description },
    })
  }

  async function fixPillarWithAIAPICall(pillar: Pillar) {
    return await $fetch<PillarDTO>('/api/llm/pillars/fix', {
      method: 'POST',
      body: { name: pillar.name, description: pillar.description },
    })
  }

  async function getContextInPillarsAPICall(context: string) {
    const { pillars } = await getContext()
    return await $fetch<ContextInPillarsFeedback>('/api/llm/feedback/context', {
      method: 'POST',
      body: { pillars, context },
    })
  }

  return {
    updateDesignIdeaAPICall,
    validatePillarAPICall,
    getPillarsInContextAPICall,
    getPillarsContradictionsAPICall,
    getPillarsCompletenessAPICall,
    getPillarsAdditionsAPICall,
    fixPillarWithAIAPICall,
    getContextInPillarsAPICall,
  }
}
