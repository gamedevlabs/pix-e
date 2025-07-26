import { usePillarsApi } from '@/composables/api/pillarsApi'

export function usePillars() {
  const basics = useCrud<Pillar>('llm/pillars/')

  const pillarsApi = usePillarsApi()
  const designIdea = ref<string>('')
  const llmFeedback = ref<PillarsInContextFeedback>({
    pillarFeedback: [],
    additionalFeedback: 'There is no feedback yet.',
    proposedAdditions: [],
  })

  const pillarCompleteness = ref<PillarCompletenessFeedback>({
    proposedAdditions: [],
    ideaIssues: [],
  })

  async function updateDesignIdea() {
    await pillarsApi.updateDesignIdeaAPICall(designIdea.value)
  }

  async function getPillarsInContextFeedback() {
    //llmFeedback.value = await pillarsApi.getPillarsCompletenessAPICall() //deprecated
  }

  async function validatePillar(pillar: Pillar) {
    return await pillarsApi.validatePillarAPICall(pillar)
  }

  async function fixPillarWithAI(pillar: Pillar) {
    return await pillarsApi.fixPillarWithAIAPICall(pillar)
  }

  async function getPillarCompleteness(){
    pillarCompleteness.value = await pillarsApi.getPillarsCompletenessAPICall()
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
    getPillarCompleteness,
    getPillarContradictions,
  }
}
