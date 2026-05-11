import { useProject } from '@/composables/useProject'
import { useApi } from '~/composables/useApi'

// Shared state - singleton pattern for cross-component reactivity
const designIdea = ref<string>('')
const isSavingConcept = ref(false)
const conceptHistory = ref<GameConcept[]>([])
const isLoadingHistory = ref(false)
const isRestoringConcept = ref(false)

export function useGameConcept() {
  const { apiFetch } = useApi()
  const { success, error: errorToast } = usePixeToast()
  const projectStore = useProject()

  async function fetchGameConcept() {
    try {
      const data = await apiFetch<{ content: string }>(
        `/api/game-concept/current/`,
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
      await apiFetch(`/api/game-concept/update_current/`, {
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
      const data = await apiFetch<GameConcept[]>(
        `/api/game-concept/history/`,
        {
          credentials: 'include',
          headers: useRequestHeaders(['cookie']),
        },
      )
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
      const data = await apiFetch<GameConcept>(
        `/api/game-concept/${conceptId}/restore/`,
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

  watch(
    () => projectStore.activeProjectId,
    async (nextId, previousId) => {
      if (previousId !== null && nextId !== previousId) {
        await fetchGameConcept()
        await fetchConceptHistory()
      }
    },
  )

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
