import type { Project, ProjectTargetPlatform } from '~/utils/project.d'

/**
 * Owns all state and behaviour behind the Create Project wizard:
 * form data, validation, step navigation, icon upload, duplication and submit.
 * The page is left as a thin shell that wires this composable into the template.
 */
export function useCreateProjectProcess() {
  const { createProject, switchProject, fetchProjectById } = useProjectHandler()
  const { close: closeSlideover } = useWorkflowSlideover()
  const { loadForUser, toggleSubstep, completeOnboarding } = useProjectWorkflow()

  const router = useRouter()
  const route = useRoute()
  const toast = useToast()

  // ─── Wizard state ──────────────────────────────────────────────────────────
  const currentStep = ref(1)
  const totalSteps = 3
  const submitting = ref(false)

  const steps = [
    { number: 1, title: 'Basic Info', description: 'Name and description' },
    { number: 2, title: 'Project Details', description: 'Genre and platform' },
    { number: 3, title: 'Review', description: 'Confirm and create' },
  ]

  // ─── Form ──────────────────────────────────────────────────────────────────
  const form = reactive({
    name: '',
    shortDescription: '',
    genres: [] as string[],
    targetPlatform: [] as ProjectTargetPlatform[],
    icon: null as string | null,
  })

  const errors = reactive({
    name: '',
    shortDescription: '',
    genres: '',
    targetPlatform: '',
  })

  // ─── Icon upload ───────────────────────────────────────────────────────────
  const uploadedFile = ref<File | null>(null)
  const previewUrl = ref<string | null>(null)
  const isUploadModalOpen = ref(false)

  // ─── Duplication ───────────────────────────────────────────────────────────
  const duplicateId = computed(() => route.query.duplicate as number | undefined)
  const isDuplicating = ref(false)

  // ─── Computed ──────────────────────────────────────────────────────────────
  const canGoNext = computed(() => {
    if (currentStep.value === 1) return form.name && form.name.trim().length > 0
    if (currentStep.value === 2) return form.genres.length > 0 && form.targetPlatform.length > 0
    return true
  })

  const isFirstStep = computed(() => currentStep.value === 1)
  const isLastStep = computed(() => currentStep.value === totalSteps)

  // Avatar initials shown when no icon image is set; '?' is the empty fallback.
  const avatarText = computed(() => {
    if (previewUrl.value || form.icon) return undefined
    const n = form.name?.trim()
    if (!n) return '?'
    const parts = n.split(/\s+/).filter(Boolean)
    if (parts.length === 0) return '?'
    if (parts.length === 1) return parts[0]?.slice(0, 2).toUpperCase() || '?'
    return ((parts[0]?.[0] || '') + (parts[1]?.[0] || '')).toUpperCase() || '?'
  })

  // ─── Validation ────────────────────────────────────────────────────────────
  function validateStep(step: number): boolean {
    errors.name = ''
    errors.shortDescription = ''
    errors.genres = ''
    errors.targetPlatform = ''

    if (step === 1) {
      if (!form.name || form.name.trim().length === 0) {
        errors.name = 'Project name is required'
        return false
      }
      if (form.name.trim().length < 3) {
        errors.name = 'Project name must be at least 3 characters'
        return false
      }
    }

    if (step === 2) {
      if (form.genres.length === 0) {
        errors.genres = 'At least one genre is required'
        return false
      }
      if (form.targetPlatform.length === 0) {
        errors.targetPlatform = 'At least one target platform is required'
        return false
      }
    }

    return true
  }

  // ─── Navigation ────────────────────────────────────────────────────────────
  function nextStep() {
    if (!validateStep(currentStep.value)) return
    if (currentStep.value < totalSteps) {
      currentStep.value++
      // Mark the matching onboarding substep complete when the user advances.
      if (currentStep.value === 2) {
        toggleSubstep('user-onb-2', 'user-onb-2-1')
      } else if (currentStep.value === 3) {
        toggleSubstep('user-onb-2', 'user-onb-2-2')
      }
    }
  }

  function previousStep() {
    if (currentStep.value > 1) currentStep.value--
  }

  function goToStep(step: number) {
    currentStep.value = step
  }

  function cancel() {
    router.push('/')
  }

  // ─── Duplication ───────────────────────────────────────────────────────────
  async function loadProjectForDuplication() {
    if (!duplicateId.value) return

    isDuplicating.value = true
    try {
      const project = await fetchProjectById(duplicateId.value)
      if (!project) {
        toast.add({
          title: 'Project Not Found',
          description: 'Could not find the project to duplicate',
          color: 'error',
        })
        router.push('/create')
        return
      }

      form.name = `${project.name} (Copy)`
      form.shortDescription = project.description
      form.genres = project.genres
      form.targetPlatform = (
        Array.isArray(project.target_platforms) ? project.target_platforms : [project.target_platforms]
      ) as ProjectTargetPlatform[]
      form.icon = project.icon || null

      // Skip directly to Review when duplicating.
      currentStep.value = 3

      toast.add({
        title: 'Duplicating Project',
        description: `Review and create a copy of "${project.name}"`,
        color: 'primary',
      })
    } catch {
      toast.add({
        title: 'Error',
        description: 'Failed to load project for duplication',
        color: 'error',
      })
      router.push('/create')
    } finally {
      isDuplicating.value = false
    }
  }

  // ─── Submit ────────────────────────────────────────────────────────────────
  function fileToDataUrl(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = (e) => resolve(e.target?.result as string)
      reader.onerror = (e) => reject(e)
      reader.readAsDataURL(file)
    })
  }

  async function createNewProject() {
    if (!validateStep(currentStep.value)) return

    submitting.value = true

    // Step 1: only the actual project creation should surface a "creation failed" toast.
    let created: Project
    try {
      let iconToSend: string | null = null
      if (uploadedFile.value) {
        try {
          iconToSend = await fileToDataUrl(uploadedFile.value)
        } catch {
          iconToSend = null
        }
      } else if (form.icon) {
        iconToSend = form.icon
      }

      created = await createProject({
        name: form.name!.trim(),
        description: form.shortDescription?.trim() ?? '',
        genres: form.genres,
        target_platforms: form.targetPlatform as Project['target_platforms'],
        is_current: true,
        icon: iconToSend,
      })
    } catch {
      toast.add({
        title: 'Error',
        description: 'Failed to create project. Please try again.',
        color: 'error',
        icon: 'i-heroicons-x-circle',
      })
      submitting.value = false
      return
    }

    // Step 2: project exists. Everything below is best-effort — we don't want a
    // navigation hiccup or workflow housekeeping issue to look like a creation failure.
    toast.add({
      title: 'Success!',
      description: `Project "${created.name}" has been created`,
      color: 'success',
      icon: 'i-heroicons-check-circle',
    })

    try {
      await toggleSubstep('user-onb-2', 'user-onb-2-3')
      await completeOnboarding()
    } catch (e) {
      console.warn('Failed to complete onboarding workflow:', e)
    }

    try {
      await switchProject(created.id)
      closeSlideover()
    } catch (e) {
      console.warn('Failed to navigate to new project:', e)
      submitting.value = false
    }
  }

  // ─── Lifecycle ─────────────────────────────────────────────────────────────
  watch(uploadedFile, (file, prev) => {
    if (prev && previewUrl.value) {
      try {
        URL.revokeObjectURL(previewUrl.value)
      } catch {
        // Ignore: URL may already be revoked.
      }
    }
    if (file) {
      previewUrl.value = URL.createObjectURL(file)
      isUploadModalOpen.value = false
    } else {
      previewUrl.value = null
    }
  })

  onMounted(async () => {
    // Activate the first substep ("Project Information") when the page opens.
    await loadForUser()
    if (duplicateId.value) loadProjectForDuplication()
  })

  onUnmounted(() => {
    if (previewUrl.value) {
      try {
        URL.revokeObjectURL(previewUrl.value)
      } catch {
        // Ignore: URL may already be revoked.
      }
    }
  })

  return {
    // state
    form,
    errors,
    currentStep,
    totalSteps,
    steps,
    submitting,
    isDuplicating,
    uploadedFile,
    previewUrl,
    isUploadModalOpen,
    // computed
    canGoNext,
    isFirstStep,
    isLastStep,
    avatarText,
    // actions
    nextStep,
    previousStep,
    goToStep,
    cancel,
    createNewProject,
  }
}
