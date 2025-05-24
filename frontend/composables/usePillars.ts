import { usePillarsApi } from '@/composables/api/pillarsApi'

export async function usePillars() {
  const config = useRuntimeConfig()
  const pillarsApi = usePillarsApi()
  const pillars = ref<Pillar[]>([])
  const designIdea = ref<string>('')
  const llmFeedback = ref<string>('Feedback will be displayed here')

  async function createPillar() {
    const pillar: Pillar = await pillarsApi.createPillarAPICall()
    pillar.llm_feedback = ''
    pillars.value.splice(pillar.pillar_id, 0, pillar)
    return pillar
  }

  async function updatePillar(pillar: Pillar) {
    await pillarsApi.updatePillarAPICall(pillar)
  }

  async function deletePillar(pillar: Pillar) {
    await pillarsApi.deletePillarAPICall(pillar)
    const index = pillars.value.findIndex((p) => p.pillar_id === pillar.pillar_id)
    if (index !== -1) {
      pillars.value.splice(index, 1)
    }
  }

  async function updateDesignIdea() {
    await pillarsApi.updateDesignIdeaAPICall(designIdea.value)
  }

  async function getLLMFeedback() {
    llmFeedback.value = await pillarsApi.getLLMFeedback()
  }

  async function validatePillar(pillar: Pillar) {
    return await pillarsApi.validatePillarAPICall(pillar)
  }

  async function initalPillarFetch() {
    await useFetch<PillarDTO[]>(`${config.public.apiBase}/llm/pillars/`, {
      credentials: 'include',
      headers: useRequestHeaders(['cookie']),
    })
      .then((data) => {
        if (data.data) {
          data.data.value?.forEach((dto) => {
            const pillar: Pillar = {
              pillar_id: dto.pillar_id,
              title: dto.title,
              description: dto.description,
              llm_feedback: '',
              display_open: false,
            }
            pillars.value.push(pillar)
          })
        }
      })
      .catch((error) => {
        console.error('Error fetching:', error)
      })
  }

  return {
    pillars,
    designIdea,
    llmFeedback,
    initalPillarFetch,
    createPillar,
    updatePillar,
    deletePillar,
    validatePillar,
    updateDesignIdea,
    getLLMFeedback,
  }
}
