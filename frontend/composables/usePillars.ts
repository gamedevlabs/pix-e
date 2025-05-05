import type { Pillar } from '@/types/pillars'
import { usePillarsApi } from '@/composables/api/pillarsApi'

export async function usePillars() {
  const pillarsApi = usePillarsApi()
  const pillars = ref<Pillar[]>([])
  const designIdea = ref<string>('')
  const llmFeedback = ref<string>('Feedback will be displayed here')

  async function createPillar(newPillar: string) {
    const pillar: Pillar = await pillarsApi.createPillarInBackend(newPillar)
    pillars.value.splice(pillar.pillar_id, 0, pillar)
  }

  async function deletePillar(pillar: Pillar) {
    await pillarsApi.deletePillarInBackend(pillar)
    const index = pillars.value.findIndex((p) => p.pillar_id === pillar.pillar_id)
    if (index !== -1) {
      pillars.value.splice(index, 1)
    }
  }

  async function updateDesignIdea(newDesignIdea: string) {
    designIdea.value = newDesignIdea
    await pillarsApi.updateDesignIdeaInBackend(newDesignIdea)
  }

  async function getLLMFeedback() {
    llmFeedback.value = await pillarsApi.getLLMFeedback()
  }


  return {
    pillars,
    designIdea,
    llmFeedback,
    createPillar,
    deletePillar,
    updateDesignIdea,
    getLLMFeedback,
  }
}
