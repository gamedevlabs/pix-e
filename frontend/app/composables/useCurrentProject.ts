export interface Project {
  id: string
  title: string
  description?: string
  createdAt?: Date
  updatedAt?: Date
}

/**
 * Composable to manage the current project context and project operations
 * This will be replaced with actual backend data later
 */
export const useCurrentProject = () => {
  // Current selected project state
  const currentProjectId = useState<string | null>('currentProjectId', () => null)
  const currentProjectTitle = useState<string>('currentProjectTitle', () => '')
  const currentProject = useState<Project | null>('currentProject', () => null)

  // Mock projects list - will be replaced with backend data
  const projects = useState<Project[]>('projects', () => [
    {
      id: 'demo',
      title: 'Demo Project',
      description: 'This is the standard project using the dev database.',
      createdAt: new Date('2024-01-01'),
      updatedAt: new Date(),
    },
  ])

  /**
   * Check if a project is currently selected
   */
  const isProjectSelected = computed(() => currentProjectId.value !== null)

  /**
   * Set the current project context
   */
  const setCurrentProject = (projectIdOrProject: string | Project, title?: string) => {
    if (typeof projectIdOrProject === 'string') {
      // Find project by ID
      const project = projects.value.find((p) => p.id === projectIdOrProject)
      if (project) {
        currentProjectId.value = project.id
        currentProjectTitle.value = project.title
        currentProject.value = project
      } else {
        // Fallback for unknown project IDs
        currentProjectId.value = projectIdOrProject
        currentProjectTitle.value = title || `Project ${projectIdOrProject}`
        currentProject.value = {
          id: projectIdOrProject,
          title: title || `Project ${projectIdOrProject}`,
        }
      }
    } else {
      // Set project object directly
      currentProjectId.value = projectIdOrProject.id
      currentProjectTitle.value = projectIdOrProject.title
      currentProject.value = projectIdOrProject
    }
  }

  /**
   * Clear the current project selection
   */
  const clearCurrentProject = () => {
    currentProjectId.value = null
    currentProjectTitle.value = ''
    currentProject.value = null
  }

  /**
   * Get all projects - MOCK
   * TODO: Replace with actual backend API call
   */
  const fetchProjects = async () => {
    // Mock implementation - will be replaced with actual API call
    return projects.value
  }

  /**
   * Get a specific project by ID - MOCK
   * TODO: Replace with actual backend API call
   */
  const fetchProjectById = async (id: string): Promise<Project | null> => {
    // Mock implementation - will be replaced with actual API call
    return projects.value.find((p) => p.id === id) || null
  }

  /**
   * Create a new project - MOCK
   * TODO: Replace with actual backend API call
   */
  const createProject = async (_projectData: Partial<Project>): Promise<void> => {
    // Mock implementation - just show a toast notification
    const toast = useToast()
    toast.add({
      title: 'Feature Not Available',
      description: 'Project creation is not implemented yet.',
      color: 'warning',
    })

    // TODO: Implement actual backend call
    // const newProject = await $fetch('/api/projects', {
    //   method: 'POST',
    //   body: projectData
    // })
    // projects.value.push(newProject)
  }

  /**
   * Update an existing project - MOCK
   * TODO: Replace with actual backend API call
   */
  const updateProject = async (_id: string, _projectData: Partial<Project>): Promise<void> => {
    // Mock implementation
    const toast = useToast()
    toast.add({
      title: 'Feature Not Available',
      description: 'Project update is not implemented yet.',
      color: 'warning',
    })

    // TODO: Implement actual backend call
    // await $fetch(`/api/projects/${id}`, {
    //   method: 'PATCH',
    //   body: projectData
    // })
  }

  /**
   * Delete a project - MOCK
   * TODO: Replace with actual backend API call
   */
  const deleteProject = async (_id: string): Promise<void> => {
    // Mock implementation
    const toast = useToast()
    toast.add({
      title: 'Feature Not Available',
      description: 'Project deletion is not implemented yet.',
      color: 'warning',
    })

    // TODO: Implement actual backend call
    // await $fetch(`/api/projects/${id}`, {
    //   method: 'DELETE'
    // })
    // projects.value = projects.value.filter(p => p.id !== id)
  }

  /**
   * Switch to a different project
   */
  const switchProject = async (projectId: string) => {
    const project = await fetchProjectById(projectId)
    if (project) {
      setCurrentProject(project)
      // Navigate to dashboard with project ID in URL
      navigateTo(`/dashboard?id=${projectId}`)
    }
  }

  /**
   * Sync project context with URL query parameters
   * Use this in any page that needs to maintain project context
   */
  const syncProjectFromUrl = () => {
    const route = useRoute()

    // Initialize project from URL on mount
    onMounted(() => {
      const projectIdFromUrl = route.query.id as string
      if (projectIdFromUrl && projectIdFromUrl !== currentProjectId.value) {
        setCurrentProject(projectIdFromUrl)
      }
    })

    // Watch for URL changes (browser back/forward)
    watch(
      () => route.query.id,
      (newProjectId) => {
        if (newProjectId && newProjectId !== currentProjectId.value) {
          setCurrentProject(newProjectId as string)
        }
      },
    )

    return {
      projectIdFromUrl: computed(() => route.query.id as string | undefined),
    }
  }

  return {
    // State
    currentProjectId,
    currentProjectTitle,
    currentProject,
    projects,
    isProjectSelected: readonly(isProjectSelected),

    // Methods
    setCurrentProject,
    clearCurrentProject,
    fetchProjects,
    fetchProjectById,
    createProject,
    updateProject,
    deleteProject,
    switchProject,
    syncProjectFromUrl,
  }
}
