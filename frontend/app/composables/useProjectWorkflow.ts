import { ref, computed, readonly } from '#imports'
import { WorkflowApiEmulator } from '~/mock_data/mock_workflow'
import type { WorkflowInstance } from '~/mock_data/mock_workflow'
import type { StepStatus } from '~/utils/workflow'

// ─── Singleton emulator & state ───────────────────────────────────────────────
// Kept outside the composable function so all component instances share one store.

const api = new WorkflowApiEmulator()

const workflows = ref<WorkflowInstance[]>([])
const activeWorkflowId = ref<string | null>(null)
const viewedWorkflowId = ref<string | null>(null) // preview only, does not change active state
const loading = ref(false)

// The currently selected workflow instance (viewed if set, otherwise active)
const workflow = computed<WorkflowInstance | null>(() => {
  const id = viewedWorkflowId.value ?? activeWorkflowId.value
  if (!id) return workflows.value[0] ?? null
  return workflows.value.find((w) => w.id === id) ?? workflows.value[0] ?? null
})

// The truly active workflow — always used for mutations, never the viewed/preview one
const activeWorkflow = computed<WorkflowInstance | null>(() => {
  if (!activeWorkflowId.value) return workflows.value[0] ?? null
  return workflows.value.find((w) => w.id === activeWorkflowId.value) ?? workflows.value[0] ?? null
})

// ─── Persistence helpers ──────────────────────────────────────────────────────

// Scope key used to namespace the active workflow id inside the emulator.
// Project workflows are keyed by projectId; user-level by 'user'.
const scopeKey = (projectId: string | null) => projectId ?? 'user'

function isInstanceComplete(w: WorkflowInstance): boolean {
  if (w.finished_at) return true
  const all = w.steps.flatMap((s) => s.substeps)
  return all.length > 0 && all.every((ss) => ss.status === 'complete')
}

function pickDefaultActiveId(list: WorkflowInstance[], projectId: string | null): string | null {
  if (!list.length) return null
  const stored = api.getActiveWorkflowId(scopeKey(projectId))
  if (stored && list.some((w) => w.id === stored)) return stored
  // prefer first incomplete, fallback to first
  return (list.find((w) => !isInstanceComplete(w)) ?? list[0]!).id
}

// ─── Composable ───────────────────────────────────────────────────────────────

export const useProjectWorkflow = () => {
  // ── Loading ────────────────────────────────────────────────────────────────

  /**
   * Load (or seed) workflows for the user.
   * This is now user-based and doesn't reset on a new project.
   */
  const loadForProject = async (_projectId?: string) => {
    loading.value = true
    const list = await api.getUserWorkflows('default')
    workflows.value = list
    activeWorkflowId.value = pickDefaultActiveId(list, 'user')
    api.setActiveWorkflowId(scopeKey(null), activeWorkflowId.value)
    loading.value = false
    return workflow.value
  }

  /** Load the user-level workflow. */
  const loadForUser = async () => {
    return loadForProject()
  }

  /**
   * Marks a workflow phase as complete.
   */
  const completeOnboarding = async () => {
    if (activeWorkflowId.value) {
      await api.completeWorkflow('default', activeWorkflowId.value)
      await loadForUser()
    }
  }

  // ── Mutations ──────────────────────────────────────────────────────────────

  const toggleSubstep = async (stepId: string, substepId: string) => {
    // IMPORTANT: mutations always apply to the *active* workflow instance
    const list = workflows.value
    const activeId = activeWorkflowId.value
    if (!activeId) return

    const wf = list.find((w) => w.id === activeId)
    if (!wf) return

    const step = wf.steps.find((s) => s.id === stepId)
    const substep = step?.substeps.find((ss) => ss.id === substepId)
    if (!substep) return

    const newStatus: StepStatus = substep.status === 'complete' ? 'active' : 'complete'

    const updated = await api.updateSubstepStatus(
      'default',
      activeId,
      stepId,
      substepId,
      newStatus
    )

    if (updated) {
      const idx = workflows.value.findIndex((w) => w.id === activeId)
      if (idx !== -1) {
        workflows.value[idx] = updated
      }
    }
  }

  /**
   * Preview a workflow phase in the UI without changing the active one.
   * This enables users to freely browse phases.
   */
  const viewWorkflow = async (id: string | null) => {
    viewedWorkflowId.value = id
  }

  return {
    // State
    workflows: readonly(workflows),
    activeWorkflowId: readonly(activeWorkflowId),
    viewedWorkflowId,
    workflow,
    activeWorkflow,
    loading: readonly(loading),

    // Actions
    loadForProject,
    loadForUser,
    toggleSubstep,
    completeOnboarding,
    viewWorkflow,

    // Selectors
    getProgress: computed(() => {
      // Overall progress should be calculated across ALL phases, regardless of what is viewed.
      const all = workflows.value.flatMap((w) => w.steps.flatMap((s) => s.substeps))
      if (all.length === 0) return 0
      const completed = all.filter((ss) => ss.status === 'complete').length
      return Math.round((completed / all.length) * 100)
    }),

    getCurrentStep: computed(() => {
      // Current step is derived from the *viewed* workflow so steps show when selecting a phase.
      const wf = workflow.value
      if (!wf) return null
      return wf.steps[wf.currentStepIndex] || wf.steps[0] || null
    }),

    getCurrentStepProgress: computed(() => {
      const wf = workflow.value
      const step = wf?.steps[wf?.currentStepIndex || 0]
      if (!step || !step.substeps.length) return 0
      const completed = step.substeps.filter((ss) => ss.status === 'complete').length
      return Math.round((completed / step.substeps.length) * 100)
    }),

    getSteps: computed(() => {
      // Steps list should follow the viewed workflow.
      return workflow.value?.steps || []
    }),

    allWorkflowsDone: computed(() => {
      return workflows.value.length > 0 && workflows.value.every((w) => w.finished_at !== null)
    }),

    setActiveWorkflow: (id: string) => {
      activeWorkflowId.value = id
      api.setActiveWorkflowId(scopeKey(null), id)
      // Do NOT force viewed workflow to active; leave user's manual selection intact.
    },

    setViewedWorkflow: (id: string | null) => {
      viewedWorkflowId.value = id
    },
  }
}
