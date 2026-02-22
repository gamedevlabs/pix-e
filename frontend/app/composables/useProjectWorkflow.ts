import { ref, computed, readonly } from '#imports'
import { WorkflowApiEmulator } from '~/mock_data/mock_workflow'
import type { WorkflowInstance } from '~/mock_data/mock_workflow'
import type { StepStatus, WorkflowStep } from '~/utils/workflow'

// ─── Singleton emulator & state ───────────────────────────────────────────────
// Kept outside the composable function so all component instances share one store.

const api = new WorkflowApiEmulator()

const workflows = ref<WorkflowInstance[]>([])
const activeWorkflowId = ref<string | null>(null)
const loading = ref(false)

// The currently selected workflow instance
const workflow = computed<WorkflowInstance | null>(() => {
  if (!activeWorkflowId.value) return workflows.value[0] ?? null
  return (
    workflows.value.find((w) => w.id === activeWorkflowId.value) ?? workflows.value[0] ?? null
  )
})

// ─── Persistence helpers ──────────────────────────────────────────────────────

const STORAGE_KEY = (projectId: string | null) =>
  `workflow_activeId:${projectId ?? 'user'}`

function persistActiveId(projectId: string | null, id: string | null) {
  try {
    const key = STORAGE_KEY(projectId)
    if (id) localStorage.setItem(key, id)
    else localStorage.removeItem(key)
  } catch { /* ignore */ }
}

function getPersistedActiveId(projectId: string | null, list: WorkflowInstance[]): string | null {
  try {
    const persisted = localStorage.getItem(STORAGE_KEY(projectId))
    if (persisted && list.some((w) => w.id === persisted)) return persisted
  } catch { /* ignore */ }
  return null
}

function isInstanceComplete(w: WorkflowInstance): boolean {
  if (w.finished_at) return true
  const all = w.steps.flatMap((s) => s.substeps)
  return all.length > 0 && all.every((ss) => ss.status === 'complete')
}

function pickDefaultActiveId(list: WorkflowInstance[], projectId: string | null): string | null {
  if (!list.length) return null
  const persisted = getPersistedActiveId(projectId, list)
  if (persisted) return persisted
  // prefer first incomplete, fallback to first
  return (list.find((w) => !isInstanceComplete(w)) ?? list[0]!).id
}

// ─── Composable ───────────────────────────────────────────────────────────────

export const useProjectWorkflow = () => {

  // ── Loading ────────────────────────────────────────────────────────────────

  /**
   * Load (or seed) workflows for a project.
   * If the project has no saved workflows yet, the template is used to create them.
   * Pass `onboardingAlreadyDone: true` when creating a project that isn't the user's first.
   */
  const loadForProject = async (projectId: string, onboardingAlreadyDone = false) => {
    loading.value = true
    let list = await api.getWorkflowsByProjectId(projectId)
    if (!list.length) {
      list = await api.seedProject(projectId, onboardingAlreadyDone)
    }
    workflows.value = list
    activeWorkflowId.value = pickDefaultActiveId(list, projectId)
    persistActiveId(projectId, activeWorkflowId.value)
    loading.value = false
    return workflow.value
  }

  /** Load the standalone user-level onboarding workflow (no project required). */
  const loadForUser = async () => {
    loading.value = true
    const w = await api.getUserOnboardingWorkflow()
    workflows.value = w ? [w] : []
    activeWorkflowId.value = pickDefaultActiveId(workflows.value, null)
    persistActiveId(null, activeWorkflowId.value)
    loading.value = false
    return workflow.value
  }

  /**
   * Called after the user creates their very first project.
   * Marks the standalone onboarding workflow as fully complete and refreshes
   * the embedded snapshot inside the active project's workflow list.
   */
  const completeOnboarding = async (activeProjectId?: string) => {
    await api.completeOnboardingWorkflow()
    // If the user-level onboarding is currently loaded, refresh it
    if (workflows.value.some((w) => w.projectId === 'user')) {
      await loadForUser()
    }
    // If a project is active, reload so the embedded completed snapshot is updated
    if (activeProjectId) {
      await loadForProject(activeProjectId)
    }
  }

  // ── Selection ──────────────────────────────────────────────────────────────

  const selectWorkflow = async (id: string, projectId: string | null) => {
    activeWorkflowId.value = id
    persistActiveId(projectId, id)
    return workflow.value
  }

  // ── Computed getters ───────────────────────────────────────────────────────

  const getSteps = computed((): WorkflowStep[] => workflow.value?.steps ?? [])

  const getCurrentStep = computed(() => {
    const w = workflow.value
    if (!w) return null
    return w.steps[w.currentStepIndex] ?? null
  })

  const getProgress = computed(() => {
    const w = workflow.value
    if (!w) return 0
    const substeps = w.steps.flatMap((s) => s.substeps)
    if (!substeps.length) return 0
    const done = substeps.filter((ss) => ss.status === 'complete').length
    return Math.round((done / substeps.length) * 100)
  })

  const getCurrentStepProgress = computed(() => {
    const w = workflow.value
    if (!w) return 0
    const step = w.steps[w.currentStepIndex]
    if (!step?.substeps.length) return 0
    const done = step.substeps.filter((ss) => ss.status === 'complete').length
    return Math.round((done / step.substeps.length) * 100)
  })

  // ── Mutations ──────────────────────────────────────────────────────────────

  const saveActiveWorkflow = async () => {
    const w = workflow.value
    if (!w) return
    await api.saveWorkflow(w)
    const idx = workflows.value.findIndex((x) => x.id === w.id)
    if (idx !== -1) workflows.value[idx] = { ...w }
    workflows.value = [...workflows.value]
  }

  const setCurrentStepIndex = async (index: number) => {
    const w = workflow.value
    if (!w || index < 0 || index >= w.steps.length) return
    w.currentStepIndex = index
    for (let i = 0; i < w.steps.length; i++) {
      const s = w.steps[i]!
      if (s.status === 'complete') continue
      s.status = i === index ? 'active' : 'pending'
    }
    await saveActiveWorkflow()
  }

  const advanceStep = async () => {
    const w = workflow.value
    if (!w) return
    await setCurrentStepIndex(Math.min(w.currentStepIndex + 1, w.steps.length - 1))
  }

  const retreatStep = async () => {
    const w = workflow.value
    if (!w) return
    await setCurrentStepIndex(Math.max(w.currentStepIndex - 1, 0))
  }

  const toggleSubstep = async (stepId: string, substepId: string) => {
    const w = workflow.value
    if (!w) return

    const stepIndex = w.steps.findIndex((s) => s.id === stepId)
    if (stepIndex === -1) return
    const step = w.steps[stepIndex]!
    const ssIndex = step.substeps.findIndex((x) => x.id === substepId)
    if (ssIndex === -1) return
    const ss = step.substeps[ssIndex]!

    const now = new Date().toISOString()

    if (ss.status === 'complete') {
      // Uncomplete — revert to active
      ss.status = 'active'
      ss.finished_at = null
    } else {
      // Complete this substep AND all preceding substeps/steps that aren't done yet

      // 1. Complete all preceding steps fully
      for (let i = 0; i < stepIndex; i++) {
        const prevStep = w.steps[i]!
        if (prevStep.status === 'complete') continue
        for (const prevSs of prevStep.substeps) {
          if (prevSs.status !== 'complete') {
            prevSs.status = 'complete'
            prevSs.started_at = prevSs.started_at ?? now
            prevSs.finished_at = now
          }
        }
        prevStep.status = 'complete'
        prevStep.started_at = prevStep.started_at ?? now
        prevStep.finished_at = now
      }

      // 2. Complete all preceding substeps within the current step
      for (let i = 0; i < ssIndex; i++) {
        const prevSs = step.substeps[i]!
        if (prevSs.status !== 'complete') {
          prevSs.status = 'complete'
          prevSs.started_at = prevSs.started_at ?? now
          prevSs.finished_at = now
        }
      }

      // 3. Complete the target substep itself
      ss.status = 'complete'
      ss.started_at = ss.started_at ?? now
      ss.finished_at = now
      if (!step.started_at) step.started_at = now

      // 4. Activate the next substep if any
      const nextSs = step.substeps[ssIndex + 1]
      if (nextSs?.status === 'pending') {
        nextSs.status = 'active'
        nextSs.started_at = now
      }
    }

    // Recalculate step status
    const allDone = step.substeps.every((x) => x.status === 'complete')
    const anyProgress = step.substeps.some((x) => x.status === 'complete' || x.status === 'active')

    if (step.substeps.length === 0 || allDone) {
      step.status = 'complete'
      step.finished_at = now

      // Advance workflow to next step
      if (stepIndex < w.steps.length - 1) {
        const nextStep = w.steps[stepIndex + 1]!
        if (nextStep.status === 'pending') {
          nextStep.status = 'active'
          nextStep.started_at = nextStep.started_at ?? now
          if (nextStep.substeps[0]?.status === 'pending') {
            nextStep.substeps[0].status = 'active'
            nextStep.substeps[0].started_at = now
          }
        }
        w.currentStepIndex = stepIndex + 1
      }
    } else {
      step.status = anyProgress ? 'active' : 'pending'
    }

    await saveActiveWorkflow()
  }

  const finishCurrentStep = async () => {
    const w = workflow.value
    if (!w) return
    const idx = w.currentStepIndex
    const step = w.steps[idx]
    if (!step) return

    const now = new Date().toISOString()
    for (const ss of step.substeps) {
      ss.status = 'complete'
      ss.finished_at = ss.finished_at ?? now
      ss.started_at = ss.started_at ?? now
    }
    step.status = 'complete'
    step.finished_at = step.finished_at ?? now

    const nextIndex = idx + 1
    if (nextIndex < w.steps.length) {
      const next = w.steps[nextIndex]!
      next.status = 'active'
      next.started_at = next.started_at ?? now
      if (next.substeps[0]?.status === 'pending') {
        next.substeps[0].status = 'active'
        next.substeps[0].started_at = now
      }
      w.currentStepIndex = nextIndex
    } else {
      w.finished_at = now
      try {
        useToast().add({
          title: 'Workflow completed',
          description: 'You finished the last step!',
          color: 'success',
        })
      } catch { /* ignore */ }
    }

    await saveActiveWorkflow()
  }

  const getStepStatus = (stepId: string): StepStatus | null => {
    const s = workflow.value?.steps.find((x) => x.id === stepId)
    return s?.status ?? null
  }

  // ── Public API ─────────────────────────────────────────────────────────────

  return {
    // State (readonly)
    workflow: readonly(workflow),
    workflows: readonly(computed(() => workflows.value)),
    activeWorkflowId: readonly(computed(() => activeWorkflowId.value)),
    loading: readonly(loading),

    // Loading
    loadForProject,
    loadForUser,
    completeOnboarding,

    // Selection
    selectWorkflow,

    // Getters
    getSteps,
    getCurrentStep,
    getProgress,
    getCurrentStepProgress,
    getStepStatus,

    // Mutations
    setCurrentStepIndex,
    advanceStep,
    retreatStep,
    toggleSubstep,
    finishCurrentStep,
  }
}
