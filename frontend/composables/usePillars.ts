import { usePillarsApi } from '@/composables/api/pillarsApi'

export async function usePillars() {
  const basics = useCrud<Pillar>('llm/pillars/')

  const config = useRuntimeConfig()
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

  return {
    basics,
    designIdea,
    llmFeedback,
    validatePillar,
    updateDesignIdea,
    getLLMFeedback,
  }
}
