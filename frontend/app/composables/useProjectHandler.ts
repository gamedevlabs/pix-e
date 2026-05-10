import type { Project } from '~/utils/project'
import { ProjectApiEmulator } from '~/mock_data/mock_projects'

const mock_projects = new ProjectApiEmulator()

export const useProjectHandler = () => {
  // state
  const currentProjectId = useState<number | null>('project_currentProjectId', () => null)
  const currentProject = useState<Project | null>('project_currentProject', () => null)
  // initializer must be synchronous for useState; fetch projects explicitly below
  const projects = useState<Project[]>('project_projects', () => [])

  const isProjectSelected = computed(() => !!currentProjectId.value)

  const config = useRuntimeConfig()
  const API_URL = config.public.apiBase + '/api/projects/'
  const { createItem, fetchAll, fetchById } = useCrudWithAuthentication<Project>('api/projects/')

  // actions
  const fetchProjects = async (): Promise<Project[]> => {
    //const list = await mock_projects.getAll()
    const projectsList = await fetchAll()
    projects.value = projectsList
    return projectsList
  }

  const fetchProjectById = async (id: number): Promise<Project | null> => {
    return await fetchById(id)
  }

  const selectProject = async (projectOrId: number | Project) => {
    console.log("project", projectOrId)
    try {

      const data = await $fetch<Project>(`${API_URL}${projectOrId}/switch/`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value ?? '',
          ...(import.meta.server ? useRequestHeaders(['cookie']) : {}),
        } as HeadersInit,
      })

      //const p = await fetchProjectById(projectOrId)
      const p = data
      if (p) {
        currentProjectId.value = p.id
        currentProject.value = p
      } else {
        /*
        const now = new Date().toISOString()
        currentProjectId.value = projectOrId
        currentProject.value = {
          id: projectOrId,
          name: `Project ${projectOrId}`,
          description: '',
          genre: 'Unknown',
          targetPlatform: 'web',
          created_at: now,
          updated_at: now,
          icon: null,
        }

         */
      }
    } catch (err) {
      //error.value = err
      //errorToast(err)
      throw err
    }
  }

  const unselectProject = () => {
    currentProjectId.value = null
    currentProject.value = null
  }

  const createProject = async (payload: Partial<Project>): Promise<Project> => {
    //const created = await mock_projects.create(payload)
    const data = createItem(payload)
    projects.value = await mock_projects.getAll()
    return data
  }

  const updateProject = async (id: string, data: Partial<Project>): Promise<Project | null> => {
    const updated = await mock_projects.update(id, data)
    projects.value = await mock_projects.getAll()
    try {
      const toast = useToast()
      if (updated) {
        toast.add({ title: 'Project updated', description: updated.name, color: 'success' })
      } else {
        toast.add({
          title: 'Update failed',
          description: `Project ${id} not found`,
          color: 'warning',
        })
      }
    } catch {
      /* ignore */
    }
    return updated
  }

  const deleteProject = async (id: string): Promise<boolean> => {
    const deleted = await mock_projects.delete(id)
    projects.value = await mock_projects.getAll()
    try {
      const toast = useToast()
      if (deleted) {
        toast.add({ title: 'Project deleted', description: id, color: 'info' })
        if (currentProjectId.value === id) unselectProject()
      } else {
        toast.add({
          title: 'Delete failed',
          description: `Project ${id} not found`,
          color: 'warning',
        })
      }
    } catch {
      /* ignore */
    }
    return deleted
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
    projects,
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
