import { ref, computed } from '#imports'
import { useProjectDataProvider, WORKFLOW_TEMPLATE, ONBOARDING_TEMPLATE } from '~/studyMock'
import type { WorkflowInstance } from '~/studyMock'
import type { WorkflowStep, StepStatus, Substep } from '~/utils/workflow'

// ─────────────────────────────────────────────────────────────────────────────
// Singleton state (kept outside composable so instances share one store)

// IMPORTANT: do NOT call useProjectDataProvider() at module top-level.
// That would call useRuntimeConfig/useNuxtApp before Nuxt is initialized.

const workflows = ref<WorkflowInstance[]>([])
const activeWorkflowId = ref<string | null>(null)
const viewedWorkflowId = ref<string | null>(null)
const loading = ref(false)
// Track which scope is currently loaded so we never overwrite in-memory
// state with a stale re-load from another call site.
const loadedScopeKey = ref<string | null>(null)

const workflow = computed<WorkflowInstance | null>(() => {
  const id = viewedWorkflowId.value ?? activeWorkflowId.value
  if (!id) return workflows.value[0] ?? null
  return workflows.value.find((w: WorkflowInstance) => w.id === id) ?? workflows.value[0] ?? null
})

const activeWorkflow = computed<WorkflowInstance | null>(() => {
  if (!activeWorkflowId.value) return workflows.value[0] ?? null
  return (
    workflows.value.find((w: WorkflowInstance) => w.id === activeWorkflowId.value) ??
    workflows.value[0] ??
    null
  )
})

const scopeKey = (projectId: string | null) => projectId ?? 'user'

function isInstanceComplete(w: WorkflowInstance): boolean {
  if (w.finished_at) return true
  const all = w.steps.flatMap((s: WorkflowStep) => s.substeps)
  return all.length > 0 && all.every((ss: Substep) => ss.status === 'complete')
}

function pickDefaultActiveId(list: WorkflowInstance[], projectId: string | null): string | null {
  if (!list.length) return null
  const provider = useProjectDataProvider()
  const stored = provider.getActiveWorkflowId(scopeKey(projectId))
  if (stored && list.some((w: WorkflowInstance) => w.id === stored)) return stored
  return (list.find((w: WorkflowInstance) => !isInstanceComplete(w)) ?? list[0]!).id
}

// Add a tiny helper to keep status transitions monotonic.
// pending -> active -> complete, and NEVER backwards.
function canUpgradeStatus(from: StepStatus, to: StepStatus): boolean {
  const rank: Record<StepStatus, number> = { pending: 0, active: 1, complete: 2 }
  return rank[to] >= rank[from]
}

function upgradeStatus<T extends { status: StepStatus }>(obj: T, to: StepStatus) {
  if (canUpgradeStatus(obj.status, to)) obj.status = to
}

function ensureSingleActiveWithinStep(step: WorkflowStep) {
  // If there are completed substeps, it's fine to have 0 active.
  // But if there are multiple active, keep the earliest active and downgrade others to pending.
  const activeIdxs: number[] = []
  for (let i = 0; i < step.substeps.length; i++) {
    if (step.substeps[i]!.status === 'active') activeIdxs.push(i)
  }
  if (activeIdxs.length <= 1) return

  const keep = activeIdxs[0]!
  for (const i of activeIdxs.slice(1)) {
    const ss = step.substeps[i]!
    // Only downgrade if it wasn't already complete (shouldn't happen, but safe).
    if (ss.status === 'active') ss.status = 'pending'
  }

  // If the kept active is after a pending earlier substep, we should activate the earliest pending instead.
  const earliestIncomplete = step.substeps.findIndex((ss) => ss.status !== 'complete')
  if (earliestIncomplete !== -1 && earliestIncomplete < keep) {
    step.substeps[keep]!.status = 'pending'
    if (step.substeps[earliestIncomplete]!.status === 'pending')
      step.substeps[earliestIncomplete]!.status = 'active'
  }
}

function normalizeWorkflowActiveState(w: WorkflowInstance) {
  // 1) Ensure only one active step (first non-complete step).
  const firstIncomplete = w.steps.findIndex((s) => s.status !== 'complete')
  for (let i = 0; i < w.steps.length; i++) {
    const step = w.steps[i]!
    if (step.status === 'complete') continue
    step.status = i === (firstIncomplete === -1 ? 0 : firstIncomplete) ? 'active' : 'pending'
  }

  // 2) Ensure each step has at most one active substep.
  for (const step of w.steps) {
    ensureSingleActiveWithinStep(step)

    // If step is active but no substep is active and there exists an incomplete substep,
    // activate its earliest incomplete substep.
    if (step.status === 'active') {
      const hasActive = step.substeps.some((ss) => ss.status === 'active')
      if (!hasActive) {
        const idx = step.substeps.findIndex((ss) => ss.status !== 'complete')
        if (idx !== -1 && step.substeps[idx]!.status === 'pending') {
          step.substeps[idx]!.status = 'active'
        }
      }
    }
  }

  // 3) Keep currentStepIndex aligned to active step.
  const activeIdx = w.steps.findIndex((s) => s.status === 'active')
  if (activeIdx !== -1) w.currentStepIndex = activeIdx
}

export const useProjectWorkflow = () => {
  const provider = useProjectDataProvider()

  // ── Loading ────────────────────────────────────────────────────────────────

  /**
   * Load (or seed) workflows for a project.
   * IDEMPOTENT: if the same project is already loaded in memory, this is a no-op
   * so that navigating between pages never wipes in-progress state.
   */
  const loadForProject = async (projectId: string, onboardingAlreadyDone = false) => {
    const key = scopeKey(projectId)

    // Already loaded for this scope — return current without touching the store.
    if (loadedScopeKey.value === key && workflows.value.length > 0) {
      return workflow.value
    }

    loading.value = true
    let list = await provider.getWorkflowsByProjectId(projectId)
    if (!list.length) {
      list = await provider.seedProjectWorkflows(projectId, onboardingAlreadyDone)
    }

    workflows.value = list
    loadedScopeKey.value = key

    // Only change activeWorkflowId if it isn't already valid for this list.
    if (
      !activeWorkflowId.value ||
      !list.some((w: WorkflowInstance) => w.id === activeWorkflowId.value)
    ) {
      activeWorkflowId.value = pickDefaultActiveId(list, projectId)
      provider.setActiveWorkflowId(key, activeWorkflowId.value)
    }

    // Clear viewed if it no longer exists in this list.
    if (
      viewedWorkflowId.value &&
      !list.some((w: WorkflowInstance) => w.id === viewedWorkflowId.value)
    ) {
      viewedWorkflowId.value = null
    }

    loading.value = false
    return workflow.value
  }

  /** Load the standalone user-level onboarding workflow (no project required). */
  const loadForUser = async () => {
    const key = scopeKey(null)

    if (loadedScopeKey.value === key && workflows.value.length > 0) {
      return workflow.value
    }

    loading.value = true
    const w = await provider.getUserOnboardingWorkflow()
    workflows.value = w ? [w] : []
    loadedScopeKey.value = key
    activeWorkflowId.value = pickDefaultActiveId(workflows.value, null)
    provider.setActiveWorkflowId(key, activeWorkflowId.value)
    loading.value = false
    return workflow.value
  }

  /**
   * Called after the user creates their very first project.
   * Marks the standalone onboarding workflow as fully complete and refreshes.
   */
  const completeOnboarding = async (activeProjectId?: string) => {
    await provider.completeOnboardingWorkflow()
    if (workflows.value.some((w: WorkflowInstance) => w.projectId === 'user')) {
      loadedScopeKey.value = null
      await loadForUser()
    }
    if (activeProjectId) {
      loadedScopeKey.value = null
      await loadForProject(activeProjectId)
    }
  }

  // ── Selection ──────────────────────────────────────────────────────────────

  const selectWorkflow = async (id: string, projectId: string | null) => {
    activeWorkflowId.value = id
    viewedWorkflowId.value = null
    provider.setActiveWorkflowId(scopeKey(projectId), id)
    return workflow.value
  }

  const viewWorkflow = async (id: string) => {
    viewedWorkflowId.value = id
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
    const substeps = w.steps.flatMap((s: WorkflowStep) => s.substeps)
    if (!substeps.length) return 0
    const done = substeps.filter((ss: Substep) => ss.status === 'complete').length
    return Math.round((done / substeps.length) * 100)
  })

  const getCurrentStepProgress = computed(() => {
    const w = workflow.value
    if (!w) return 0
    const step = w.steps[w.currentStepIndex]
    if (!step?.substeps.length) return 0
    const done = step.substeps.filter((ss: Substep) => ss.status === 'complete').length
    return Math.round((done / step.substeps.length) * 100)
  })

  /** Look up the completionMessage for a workflow instance from the templates. */
  function getCompletionMessage(w: WorkflowInstance): string {
    const phaseId = w.id.replace(/^wf-[^-]+-/, '')
    if (phaseId === ONBOARDING_TEMPLATE.id) {
      return ONBOARDING_TEMPLATE.completionMessage ?? 'Workflow complete!'
    }
    const phase = WORKFLOW_TEMPLATE.find((p) => p.id === phaseId)
    return phase?.completionMessage ?? 'Workflow complete!'
  }

  /**
   * Called whenever a workflow is marked finished.
   * Shows the completion toast and automatically switches to the next incomplete workflow.
   */
  function onWorkflowComplete(w: WorkflowInstance) {
    try {
      useToast().add({
        title: `🎉 "${w.meta.title}" complete!`,
        description: getCompletionMessage(w),
        color: 'success',
        duration: 8000,
      })
    } catch {
      /* ignore */
    }

    // Auto-advance to the next incomplete workflow in the list
    const currentIdx = workflows.value.findIndex((x: WorkflowInstance) => x.id === w.id)
    const next = workflows.value
      .slice(currentIdx + 1)
      .find((x: WorkflowInstance) => !isInstanceComplete(x))
    if (next) {
      activeWorkflowId.value = next.id
      viewedWorkflowId.value = null
      provider.setActiveWorkflowId(scopeKey(w.projectId === 'user' ? null : w.projectId), next.id)
    }
  }

  // ── Mutations ──────────────────────────────────────────────────────────────

  const saveActiveWorkflow = async () => {
    const w = activeWorkflow.value
    if (!w) return
    await provider.saveWorkflow(w)
    const idx = workflows.value.findIndex((x: WorkflowInstance) => x.id === w.id)
    if (idx !== -1) {
      workflows.value[idx] = { ...w }
    }
    workflows.value = [...workflows.value]
  }

  const setCurrentStepIndex = async (index: number) => {
    const w = activeWorkflow.value
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
    const w = activeWorkflow.value
    if (!w) return
    await setCurrentStepIndex(Math.min(w.currentStepIndex + 1, w.steps.length - 1))
  }

  const retreatStep = async () => {
    const w = activeWorkflow.value
    if (!w) return
    await setCurrentStepIndex(Math.max(w.currentStepIndex - 1, 0))
  }

  const toggleSubstep = async (stepId: string, substepId: string) => {
    const w = activeWorkflow.value
    if (!w) return

    const stepIndex = w.steps.findIndex((s: WorkflowStep) => s.id === stepId)
    if (stepIndex === -1) return
    const step = w.steps[stepIndex]!
    const ssIndex = step.substeps.findIndex((x: Substep) => x.id === substepId)
    if (ssIndex === -1) return
    const ss = step.substeps[ssIndex]!

    const now = new Date().toISOString()

    // If it's already complete, do nothing. Completion must be monotonic.
    if (ss.status === 'complete') {
      // Still normalize in case we previously created an invalid state.
      normalizeWorkflowActiveState(w)
      await saveActiveWorkflow()
      return
    }

    // 1. Complete all preceding steps
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

    // 3. Complete the target substep
    ss.status = 'complete'
    ss.started_at = ss.started_at ?? now
    ss.finished_at = now
    if (!step.started_at) step.started_at = now

    // 4. Activate next substep (only if it wouldn't regress it)
    const nextSs = step.substeps[ssIndex + 1]
    if (nextSs && nextSs.status === 'pending') {
      upgradeStatus(nextSs, 'active')
      nextSs.started_at = nextSs.started_at ?? now
    }

    const allDone = step.substeps.every((x: Substep) => x.status === 'complete')
    const anyProgress = step.substeps.some(
      (x: Substep) => x.status === 'complete' || x.status === 'active',
    )

    if (step.substeps.length === 0 || allDone) {
      step.status = 'complete'
      step.finished_at = now

      if (stepIndex < w.steps.length - 1) {
        const nextStep = w.steps[stepIndex + 1]!
        if (nextStep.status === 'pending') {
          upgradeStatus(nextStep, 'active')
          nextStep.started_at = nextStep.started_at ?? now
          if (nextStep.substeps[0]?.status === 'pending') {
            upgradeStatus(nextStep.substeps[0], 'active')
            nextStep.substeps[0].started_at = nextStep.substeps[0].started_at ?? now
          }
        }
        w.currentStepIndex = stepIndex + 1
      } else {
        // Last step — check if whole workflow is done
        const allWorkflowDone = w.steps
          .flatMap((s: WorkflowStep) => s.substeps)
          .every((ss: Substep) => ss.status === 'complete')
        if (allWorkflowDone && !w.finished_at) {
          w.finished_at = now
          onWorkflowComplete(w)
        }
      }
    } else {
      upgradeStatus(step, anyProgress ? 'active' : 'pending')
    }

    // Final normalization to guarantee no "double active" states.
    normalizeWorkflowActiveState(w)

    await saveActiveWorkflow()
  }

  const finishCurrentStep = async () => {
    const w = activeWorkflow.value
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
      const nextStep = w.steps[nextIndex]!
      w.currentStepIndex = nextIndex
      if (nextStep.status === 'pending') {
        nextStep.status = 'active'
        nextStep.started_at = nextStep.started_at ?? now
      }
      if (nextStep.substeps[0] && nextStep.substeps[0].status === 'pending') {
        nextStep.substeps[0].status = 'active'
        nextStep.substeps[0].started_at = nextStep.substeps[0].started_at ?? now
      }
    } else {
      if (!w.finished_at) {
        w.finished_at = now
        onWorkflowComplete(w)
      }
    }

    await saveActiveWorkflow()
  }

  const finishWorkflow = async () => {
    const w = activeWorkflow.value
    if (!w) return

    const now = new Date().toISOString()
    for (const step of w.steps) {
      step.started_at = step.started_at ?? now
      step.status = 'complete' as StepStatus
      step.finished_at = step.finished_at ?? now
      for (const ss of step.substeps) {
        ss.started_at = ss.started_at ?? now
        ss.status = 'complete' as StepStatus
        ss.finished_at = ss.finished_at ?? now
      }
    }

    w.finished_at = w.finished_at ?? now
    onWorkflowComplete(w)
    await saveActiveWorkflow()
  }

  const resetWorkflow = async () => {
    const w = activeWorkflow.value
    if (!w) return

    w.started_at = null
    w.finished_at = null
    w.currentStepIndex = 0

    for (let i = 0; i < w.steps.length; i++) {
      const step = w.steps[i]!
      step.started_at = null
      step.finished_at = null
      step.status = i === 0 ? 'active' : 'pending'

      for (let j = 0; j < step.substeps.length; j++) {
        const ss = step.substeps[j]!
        ss.started_at = null
        ss.finished_at = null
        ss.status = i === 0 && j === 0 ? 'active' : 'pending'
      }
    }

    await saveActiveWorkflow()
  }

  return {
    // state
    workflows,
    activeWorkflowId,
    workflow,
    loading,

    // loading
    loadForProject,
    loadForUser,
    completeOnboarding,

    // selection
    selectWorkflow,
    viewWorkflow,

    // getters
    getSteps,
    getCurrentStep,
    getProgress,
    getCurrentStepProgress,

    // mutations
    setCurrentStepIndex,
    advanceStep,
    retreatStep,
    toggleSubstep,
    finishCurrentStep,
    finishWorkflow,
    resetWorkflow,
  }
}
