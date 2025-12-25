import { defineStore } from 'pinia'

export const useProject = defineStore('project', () => {
  const projects = ref<Project[]>([])
  const activeProjectId = ref<number | null>(null)
  const isLoading = ref(false)
  const isSwitching = ref(false)
  const isCloning = ref(false)
  const { success, error: errorToast } = usePixeToast()
  const config = useRuntimeConfig()

  async function fetchProjects() {
    isLoading.value = true
    try {
      const data = await $fetch<Project[]>(`${config.public.apiBase}/game-concept/projects/`, {
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
      const data = await $fetch<Project>(
        `${config.public.apiBase}/game-concept/projects/${projectId}/switch/`,
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

  async function cloneProject(
    projectId: number,
    payload: {
      name: string
      include_concept: boolean
      include_pillars: boolean
      include_charts: boolean
      include_nodes: boolean
    },
  ) {
    if (!projectId) return
    isCloning.value = true
    try {
      await $fetch<Project>(`${config.public.apiBase}/game-concept/projects/${projectId}/clone/`, {
        method: 'POST',
        body: payload,
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      })
      await fetchProjects()
      success('Project cloned!')
    } catch (err) {
      errorToast(err)
    } finally {
      isCloning.value = false
    }
  }

  return {
    projects,
    activeProjectId,
    isLoading,
    isSwitching,
    isCloning,
    fetchProjects,
    switchProject,
    cloneProject,
  }
})
