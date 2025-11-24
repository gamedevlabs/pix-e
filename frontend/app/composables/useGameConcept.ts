// Shared state - singleton pattern for cross-component reactivity
const designIdea = ref<string>('')
const isSavingConcept = ref(false)
const conceptHistory = ref<GameConcept[]>([])
const isLoadingHistory = ref(false)
const isRestoringConcept = ref(false)

export function useGameConcept() {
  const config = useRuntimeConfig()
  const { success, error: errorToast } = usePixeToast()

  async function fetchGameConcept() {
    try {
      const data = await $fetch<{ content: string }>(
        `${config.public.apiBase}/game-concept/current/`,
        {
          credentials: 'include',
          headers: useRequestHeaders(['cookie']),
        },
      )
      designIdea.value = data?.content ?? ''
    } catch {
      // No current concept exists, that's ok
      designIdea.value = ''
    }
  }

  async function saveGameConcept() {
    if (!designIdea.value.trim()) return

    isSavingConcept.value = true
    try {
      await $fetch(`${config.public.apiBase}/game-concept/update_current/`, {
        method: 'POST',
        body: { content: designIdea.value },
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      })
      success('Game concept saved!')
      // Refresh history after save
      await fetchConceptHistory()
    } catch (err) {
      errorToast(err)
    } finally {
      isSavingConcept.value = false
    }
  }

  async function fetchConceptHistory() {
    isLoadingHistory.value = true
    try {
      const data = await $fetch<GameConcept[]>(`${config.public.apiBase}/game-concept/history/`, {
        credentials: 'include',
        headers: useRequestHeaders(['cookie']),
      })
      conceptHistory.value = data || []
    } catch (err) {
      errorToast(err)
    } finally {
      isLoadingHistory.value = false
    }
  }

  async function restoreConcept(conceptId: number) {
    isRestoringConcept.value = true
    try {
      const data = await $fetch<GameConcept>(
        `${config.public.apiBase}/game-concept/${conceptId}/restore/`,
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            'X-CSRFToken': useCookie('csrftoken').value,
          } as HeadersInit,
        },
      )
      designIdea.value = data.content
      success('Game concept restored!')
      // Refresh history
      await fetchConceptHistory()
    } catch (err) {
      errorToast(err)
    } finally {
      isRestoringConcept.value = false
    }
  }

  return {
    designIdea,
    isSavingConcept,
    conceptHistory,
    isLoadingHistory,
    isRestoringConcept,
    fetchGameConcept,
    saveGameConcept,
    fetchConceptHistory,
    restoreConcept,
  }
}
