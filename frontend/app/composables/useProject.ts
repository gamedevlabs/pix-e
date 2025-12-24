import { defineStore } from 'pinia'

export const useProject = defineStore('project', () => {
  const projects = ref<GameConcept[]>([])
  const activeProjectId = ref<number | null>(null)
  const isLoading = ref(false)
  const isSwitching = ref(false)
  const { success, error: errorToast } = usePixeToast()
  const config = useRuntimeConfig()

  async function fetchProjects() {
    isLoading.value = true
    try {
      const data = await $fetch<GameConcept[]>(`${config.public.apiBase}/game-concept/history/`, {
        credentials: 'include',
        headers: useRequestHeaders(['cookie']),
      })
      projects.value = data || []
      activeProjectId.value = projects.value.find((project) => project.is_current)?.id ?? null
    } catch (err) {
      errorToast(err)
    } finally {
      isLoading.value = false
    }
  }

  async function switchProject(projectId: number) {
    if (!projectId || projectId === activeProjectId.value) return
    isSwitching.value = true
    try {
      const data = await $fetch<GameConcept>(
        `${config.public.apiBase}/game-concept/${projectId}/restore/`,
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            'X-CSRFToken': useCookie('csrftoken').value,
          } as HeadersInit,
        },
      )
      activeProjectId.value = data.id
      await fetchProjects()
      success('Project switched!')
    } catch (err) {
      errorToast(err)
    } finally {
      isSwitching.value = false
    }
  }

  return {
    projects,
    activeProjectId,
    isLoading,
    isSwitching,
    fetchProjects,
    switchProject,
  }
})
