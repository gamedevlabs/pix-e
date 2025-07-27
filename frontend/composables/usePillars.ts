import { usePillarsApi } from '@/composables/api/pillarsApi'

export function usePillars() {
  const basics = useCrud<Pillar>('llm/pillars/')

  const pillarsApi = usePillarsApi()
  const designIdea = ref<string>('')
  const llmFeedback = ref<PillarsInContextFeedback>({
    ideaIssues: [],
    proposedAdditions: [],
    contradictions: [],
  })

  const pillarCompleteness = ref<PillarCompletenessFeedback>({
    proposedAdditions: [],
    ideaIssues: [],
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
    return await pillarsApi.getPillarsContradictionsAPICall()
  }

  return {
    ...basics,
    designIdea,
    llmFeedback,
    pillarCompleteness,
    validatePillar,
    updateDesignIdea,
    getPillarsInContextFeedback,
    fixPillarWithAI,
    getPillarContradictions,
  }
}
