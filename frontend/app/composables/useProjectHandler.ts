import type { Project } from '~/utils/project'

// Temporary in-memory API emulator for projects
class ProjectApiEmulator {
  private projects: Project[] = []

  constructor() {
    const now = new Date().toISOString()
    this.projects = [
      {
        id: 'pixe',
        name: 'pix:e',
        shortDescription: 'This project contains all the old data from the other pix:e devs.',
        genre: 'Tool',
        targetPlatform: 'web',
        created_at: '2024-01-01T10:00:00.000Z',
        updated_at: now,
        icon: null,
      },
      {
        id: '29673',
        name: 'Demo Project',
        shortDescription: 'An experimental narrative project with example scenes.',
        genre: 'Narrative, Adventure, Story-Driven',
        targetPlatform: 'desktop, web, console',
        created_at: '2024-06-15T08:30:00.000Z',
        updated_at: '2024-07-18T08:30:00.000Z',
        icon: null,
      },
      {
        id: '1648843',
        name: 'Mobile Game',
        shortDescription: 'Mock mobile-oriented project.',
        genre: 'Puzzle, Casual, Strategy',
        targetPlatform: 'mobile',
        created_at: '2025-02-10T12:00:00.000Z',
        updated_at: '2026-01-03T12:00:00.000Z',
        icon: null,
      },
    ]
  }

  async getAll(): Promise<Project[]> {
    return this.projects.map((p) => ({ ...p }))
  }

  async getById(id: string): Promise<Project | null> {
    const p = this.projects.find((x) => x.id === id)
    return p ? { ...p } : null
  }

  async create(data: Partial<Project>): Promise<Project> {
    const now = new Date().toISOString()
    const newProject: Project = {
      id: data.id || `${Date.now()}`,
      name: data.name || 'Untitled Project',
      shortDescription: data.shortDescription || '',
      genre: data.genre || 'Unknown',
      targetPlatform: (data.targetPlatform as Project['targetPlatform']) ?? 'web',
      created_at: (data.created_at as string) || now,
      updated_at: (data.updated_at as string) || now,
      // carry through optional icon (data URL or URL)
      icon: (data.icon as string | null) ?? null,
    }
    this.projects.push(newProject)
    return { ...newProject }
  }

  async update(id: string, data: Partial<Project>): Promise<Project | null> {
    const idx = this.projects.findIndex((x) => x.id === id)
    if (idx === -1) return null
    const existing = this.projects[idx]!
    // Build a fully-typed Project object, don't spread Partial<Project> over Project
    const updated: Project = {
      id: existing.id,
      name: data.name ?? existing.name,
      shortDescription: data.shortDescription ?? existing.shortDescription,
      genre: data.genre ?? existing.genre,
      targetPlatform: (data.targetPlatform as Project['targetPlatform']) ?? existing.targetPlatform,
      created_at: existing.created_at,
      updated_at: new Date().toISOString(),
      icon: (data.icon as string | null) ?? existing.icon ?? null,
    }
    this.projects[idx] = updated
    return { ...updated }
  }

  async delete(id: string): Promise<boolean> {
    const lenBefore = this.projects.length
    this.projects = this.projects.filter((x) => x.id !== id)
    return this.projects.length < lenBefore
  }
}

const api = new ProjectApiEmulator()

export const useProjectHandler = () => {
  // state
  const currentProjectId = useState<string | null>('project_currentProjectId', () => null)
  const currentProject = useState<Project | null>('project_currentProject', () => null)
  // initializer must be synchronous for useState; fetch projects explicitly below
  const projects = useState<Project[]>('project_projects', () => [])

  const isProjectSelected = computed(() => !!currentProjectId.value)

  // actions
  const fetchProjects = async (): Promise<Project[]> => {
    const list = await api.getAll()
    projects.value = list
    return list
  }

  const fetchProjectById = async (id: string): Promise<Project | null> => {
    return await api.getById(id)
  }

  const selectProject = async (projectOrId: string | Project) => {
    if (typeof projectOrId === 'string') {
      const p = await fetchProjectById(projectOrId)
      if (p) {
        currentProjectId.value = p.id
        currentProject.value = p
      } else {
        const now = new Date().toISOString()
        currentProjectId.value = projectOrId
        currentProject.value = {
          id: projectOrId,
          name: `Project ${projectOrId}`,
          shortDescription: '',
          genre: 'Unknown',
          targetPlatform: 'web',
          created_at: now,
          updated_at: now,
          icon: null,
        }
      }
    } else {
      currentProjectId.value = projectOrId.id
      currentProject.value = projectOrId
    }
  }

  const unselectProject = () => {
    currentProjectId.value = null
    currentProject.value = null
  }

  const createProject = async (data: Partial<Project>): Promise<Project> => {
    const created = await api.create(data)
    projects.value = await api.getAll()
    return created
  }

  const updateProject = async (id: string, data: Partial<Project>): Promise<Project | null> => {
    const updated = await api.update(id, data)
    projects.value = await api.getAll()
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
    const deleted = await api.delete(id)
    projects.value = await api.getAll()
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

  const switchProject = async (id: string) => {
    await selectProject(id)
    navigateTo(`/dashboard?id=${id}`)
  }

  const syncProjectFromUrl = () => {
    const route = useRoute()

    onMounted(() => {
      const projectIdFromUrl = route.query.id as string | undefined
      if (projectIdFromUrl && projectIdFromUrl !== currentProjectId.value) {
        selectProject(projectIdFromUrl)
      }
    })

    watch(
      () => route.query.id,
      (newVal) => {
        const id = newVal as string | undefined
        if (id && id !== currentProjectId.value) selectProject(id)
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
