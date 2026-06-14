import { defineStore } from 'pinia'
import { useApi } from '~/composables/useApi'

export const useProject = defineStore('project', () => {
  const projects = ref<Project[]>([])
  const activeProjectId = ref<number | null>(null)
  const isLoading = ref(false)
  const isSwitching = ref(false)
  const isCloning = ref(false)
  const { success, error: errorToast } = usePixeToast()
  const { apiFetch } = useApi()
  const { addLog } = useSessionLog()

  async function fetchProjects() {
    isLoading.value = true
    try {
      const data = await apiFetch<Project[]>(`/api/projects/`, {
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
    // log project switch start
    addLog('info', 'project_switch_started', { projectId })

    if (!projectId || projectId === activeProjectId.value) return
    isSwitching.value = true
    try {
      const data = await apiFetch<Project>(`/api/projects/${projectId}/switch/`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      })
      activeProjectId.value = data.id
      await fetchProjects()
      success('Project switched!')
      // log project switch sucess
      addLog('info', 'project_switch_succeeded', { projectId })
    } catch (err) {
      errorToast(err)
      // log project switch fail
      addLog('error', 'project_switch_failed', {
        projectId,
        message: err instanceof Error ? err.message : String(err),
      })
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
    // log project clone started
    addLog('info', 'project_clone_started', { projectId })

    if (!projectId) return
    isCloning.value = true
    try {
      await apiFetch<Project>(`/api/projects/${projectId}/clone/`, {
        method: 'POST',
        body: payload,
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      })
      await fetchProjects()
      success('Project cloned!')
      // log project clone success
      addLog('info', 'project_clone_succeeded', { projectId })
    } catch (err) {
      errorToast(err)
      // log project clone fail
      addLog('info', 'project_clone_failed', {
        projectId,
        message: err instanceof Error ? err.message : String(err),
      })
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
