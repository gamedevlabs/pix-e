import type { Project, ProjectTargetPlatform } from '~/utils/project.d'

/**
 * Owns the state and behaviour behind the Settings page:
 * loading the project from the URL, tracking unsaved changes,
 * saving back through `useProjectHandler`, and cancellation.
 *
 * The page is a thin shell that wires this composable to the card components.
 */
export function useProjectSettings() {
  const { updateProject, fetchProjectById, syncProjectFromUrl, selectProject } = useProjectHandler()
  const router = useRouter()
  const route = useRoute()
  const toast = useToast()

  syncProjectFromUrl()

  const projectId = computed(() => route.query.id as number | undefined)

  const formData = reactive({
    name: '',
    description: '',
    genres: [] as string[],
    target_platforms: [] as ProjectTargetPlatform[],
    icon: null as string | null,
  })

  const isLoading = ref(false)
  const isSaving = ref(false)
  const originalProject = ref<Project | null>(null)

  const hasChanges = computed(() => {
    if (!originalProject.value) return false

    const originalGenres = originalProject.value.genres
    const originalPlatforms = Array.isArray(originalProject.value.target_platforms)
      ? originalProject.value.target_platforms
      : [originalProject.value.target_platforms]

    const nameChanged = formData.name !== originalProject.value.name
    const descChanged = formData.description !== originalProject.value.description
    const genresChanged =
      JSON.stringify([...formData.genres].sort()) !== JSON.stringify([...originalGenres].sort())
    const platformsChanged =
      JSON.stringify([...formData.target_platforms].sort()) !==
      JSON.stringify([...originalPlatforms].sort())
    const iconChanged = formData.icon !== originalProject.value.icon

    return nameChanged || descChanged || genresChanged || platformsChanged || iconChanged
  })

  async function loadProject() {
    if (!projectId.value) {
      toast.add({
        title: 'No Project Selected',
        description: 'Please select a project to edit',
        color: 'error',
      })
      await router.push('/')
      return
    }

    isLoading.value = true
    try {
      const project = await fetchProjectById(projectId.value)
      if (!project) {
        toast.add({
          title: 'Project Not Found',
          description: `Project ${projectId.value} does not exist`,
          color: 'error',
        })
        await router.push('/')
        return
      }

      originalProject.value = project
      formData.name = project.name
      formData.description = project.description
      formData.genres = project.genres
      formData.target_platforms = (
        Array.isArray(project.target_platforms) ? project.target_platforms : [project.target_platforms]
      ) as ProjectTargetPlatform[]
      formData.icon = project.icon || null
    } catch (err) {
      toast.add({
        title: 'Error Loading Project',
        description: 'Failed to load project data',
        color: 'error',
      })
      console.log(err)
      await router.push('/')
    } finally {
      isLoading.value = false
    }
  }

  function handleCancel() {
    if (hasChanges.value) {
      const confirmed = confirm('You have unsaved changes. Are you sure you want to cancel?')
      if (!confirmed) return
    }
    router.push(`/dashboard?id=${projectId.value}`)
  }

  async function handleSubmit() {
    if (!projectId.value) return

    isSaving.value = true
    try {
      const updatedProject = await updateProject(projectId.value, {
        name: formData.name,
        description: formData.description,
        genres: formData.genres,
        target_platforms: formData.target_platforms,
        //icon: formData.icon,
      })

      if (updatedProject) {
        originalProject.value = updatedProject
        // Refresh the sidebar's current project so name/icon updates appear instantly.
        // updateProject already shows a success toast — don't double-toast.
        await selectProject(updatedProject.id)
      }
    } catch (err) {
      toast.add({
        title: 'Error Saving Project',
        description: 'Failed to save project settings',
        color: 'error',
      })
      console.log("error", err)
    } finally {
      isSaving.value = false
    }
  }

  onMounted(() => {
    loadProject()
  })

  watch(
    () => route.query.id,
    () => {
      loadProject()
    },
  )

  return {
    formData,
    originalProject,
    isLoading,
    isSaving,
    hasChanges,
    handleCancel,
    handleSubmit,
  }
}
