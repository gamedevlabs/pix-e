import { usePillarsApi } from '@/composables/api/pillarsApi'

export function usePillars() {
  const basics = useCrud<Pillar>('llm/pillars/')

  const pillarsApi = usePillarsApi()
  const designIdea = ref<string>('')
  const llmFeedback = ref<string>('Feedback will be displayed here')

  async function updateDesignIdea() {
    await pillarsApi.updateDesignIdeaAPICall(designIdea.value)
  }

  async function getLLMFeedback() {
    llmFeedback.value = await pillarsApi.getLLMFeedback()
  }

  async function validatePillar(pillar: Pillar) {
    return await pillarsApi.validatePillarAPICall(pillar)
  }

  async function fixPillarWithAI(pillar: Pillar) {
    const updatedPillar = await pillarsApi.fixPillarWithAIAPICall(pillar)
    pillar.name = updatedPillar.name
    pillar.description = updatedPillar.description
    pillar.llm_feedback = null
  }
  return {
    ...basics,
    designIdea,
    llmFeedback,
    validatePillar,
    updateDesignIdea,
    getLLMFeedback,
    fixPillarWithAI,
  }
}
