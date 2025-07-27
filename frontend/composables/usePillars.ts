import { usePillarsApi } from '@/composables/api/pillarsApi'

export function usePillars() {
  const basics = useCrud<Pillar>('llm/pillars/')

  const pillarsApi = usePillarsApi()
  const designIdea = ref<string>('')
  const llmFeedback = ref<PillarsInContextFeedback>({
    coverage: {
      pillarFeedback: [],
    },
    contradictions: {
      contradictions: [],
    },
    proposedAdditions: {
      proposedAdditions: [],
    },
  })

  async function updateDesignIdea() {
    await pillarsApi.updateDesignIdeaAPICall(designIdea.value)
  }

  async function getPillarsInContextFeedback() {
    llmFeedback.value = await pillarsApi.getPillarsInContextAPICall()
  }

  async function validatePillar(pillar: Pillar) {
    return await pillarsApi.validatePillarAPICall(pillar)
  }

  async function fixPillarWithAI(pillar: Pillar) {
    return await pillarsApi.fixPillarWithAIAPICall(pillar)
  }

  async function getPillarContradictions() {
    llmFeedback.value.contradictions = await pillarsApi.getPillarsContradictionsAPICall()
  }

  return {
    ...basics,
    designIdea,
    llmFeedback,
    validatePillar,
    updateDesignIdea,
    getPillarsInContextFeedback,
    fixPillarWithAI,
    getPillarContradictions,
  }
}
