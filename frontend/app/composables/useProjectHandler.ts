import type { Project } from '~/utils/project'

export const useProjectHandler = () => {
  // state
  const currentProjectId = useState<number | null>('project_currentProjectId', () => null)
  const currentProject = useState<Project | null>('project_currentProject', () => null)
  // initializer must be synchronous for useState; fetch projects explicitly below
  //const projects = useState<Project[]>('project_projects', () => [])

  const isProjectSelected = computed(() => !!currentProjectId.value)

  const config = useRuntimeConfig()
  const API_URL = config.public.apiBase + '/api/projects/'
  const { items, createItem, updateItem, fetchAll, fetchById, deleteItem } =
    useCrudWithAuthentication<Project>('api/projects/')

  // actions
  const fetchProjects = async (): Promise<Project[]> => {
    return await fetchAll()
  }

  const fetchProjectById = async (id: number): Promise<Project | null> => {
    return await fetchById(id)
  }

  const selectProject = async (projectId: number) => {
    const data = await $fetch<Project>(`${API_URL}${projectId}/switch/`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'X-CSRFToken': useCookie('csrftoken').value ?? '',
        ...(import.meta.server ? useRequestHeaders(['cookie']) : {}),
      } as HeadersInit,
    })
    currentProjectId.value = data.id
    currentProject.value = data
  }

  const unselectProject = () => {
    currentProjectId.value = null
    currentProject.value = null
  }

  const createProject = async (payload: Partial<Project>): Promise<Project> => {
    return createItem(payload)
  }

  const updateProject = async (id: number, payload: Partial<Project>): Promise<Project | null> => {
    return await updateItem(id, payload)
  }

  const deleteProject = async (id: number): Promise<boolean> => {
    try {
      await deleteItem(id)
      if (currentProjectId.value === id) unselectProject()
      return true
    } catch {
      /* ignore */
      return false
    }
  }

  const switchProject = async (id: number) => {
    await selectProject(id)
    navigateTo(`/dashboard?id=${id}`)
  }

  const syncProjectFromUrl = () => {
    const route = useRoute()

    onMounted(() => {
      const projectIdFromUrl = route.query.id as number | undefined
      if (projectIdFromUrl && projectIdFromUrl !== currentProjectId.value) {
        selectProject(projectIdFromUrl)
      }
    })

    watch(
      () => route.query.id,
      (newVal) => {
        const id = newVal as number | undefined
        if (id && id !== currentProjectId.value) {
          selectProject(id)
        }
      },
    )

    return {
      projectIdFromUrl: computed(() => route.query.id as string | undefined),
    }
  }

  // initialize projects when the composable is used (non-blocking)
  fetchProjects().catch(() => {})

  return {
    currentProjectId,
    currentProject,
    projects: items,
    isProjectSelected: readonly(isProjectSelected),

    fetchProjects,
    fetchProjectById,
    selectProject,
    unselectProject,
    createProject,
    updateProject,
    deleteProject,
    switchProject,
    syncProjectFromUrl,
  }
}
