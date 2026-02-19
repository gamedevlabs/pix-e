import { ref, computed, readonly } from '#imports'
import { WorkflowApiEmulator, getMockWorkflowSteps } from '~/mock_data/mock_workflow'
import type { MockWorkflow } from '~/mock_data/mock_workflow'
import type { StepStatus, WorkflowStep, ProjectWorkflow } from '~/utils/workflow'

// In-memory emulator (now supports multiple project workflows + a user workflow)
const api = new WorkflowApiEmulator()

// Shared state - moved outside the function to ensure singleton behavior
const workflows = ref<MockWorkflow[]>([])
const activeWorkflowId = ref<string | null>(null)
const workflow = computed<ProjectWorkflow | null>(() => {
  if (!activeWorkflowId.value) return workflows.value[0] ?? null
  return workflows.value.find((w) => w.id === activeWorkflowId.value) ?? workflows.value[0] ?? null
})
const loading = ref(false)

const scopeKeyForContext = (projectId: string | null) => {
  // For now we only support one mocked user in memory.
  return projectId ? `project:${projectId}` : 'user:default'
}

const storageKeyForActiveWorkflow = (projectId: string | null) => {
  return `workflow_activeWorkflowId:${scopeKeyForContext(projectId)}`
}

const isWorkflowCompleted = (w: ProjectWorkflow) => {
  // consider done if all substeps across all steps are complete and workflow has finished_at
  const allSubsteps = w.steps.flatMap((s) => s.substeps)
  const done = allSubsteps.length > 0 && allSubsteps.every((ss) => ss.status === 'complete')
  return done || !!w.finished_at
}

const getDefaultActiveWorkflowId = (list: MockWorkflow[], projectId: string | null) => {
  if (!list.length) return null

  // 1) use persisted choice if it exists and still exists in list
  try {
    const persisted = localStorage.getItem(storageKeyForActiveWorkflow(projectId))
    if (persisted && list.some((w) => w.id === persisted)) return persisted
  } catch {
    /* ignore */
  }

  // 2) if no project: default to onboarding if not completed
  if (!projectId) {
    const onboarding = list[0]
    if (onboarding && !isWorkflowCompleted(onboarding)) return onboarding.id
    return onboarding?.id ?? list[0]?.id ?? null
  }

  // 3) project: first incomplete workflow, else first
  const firstIncomplete = list.find((w) => !isWorkflowCompleted(w))
  return (firstIncomplete || list[0]).id
}

const persistActiveWorkflowId = (projectId: string | null, id: string | null) => {
  try {
    if (!id) localStorage.removeItem(storageKeyForActiveWorkflow(projectId))
    else localStorage.setItem(storageKeyForActiveWorkflow(projectId), id)
  } catch {
    /* ignore */
  }
}

export const useProjectWorkflow = () => {
  const loadForProject = async (projectId: string) => {
    loading.value = true
    const list = await api.getWorkflowsByProjectId(projectId)
    if (list.length) {
      workflows.value = list
    } else {
      // initialize a fresh workflow if missing
      const now = new Date().toISOString()
      const initial: MockWorkflow = {
        id: `wf-${projectId}-${Date.now()}`,
        projectId,
        started_at: now,
        finished_at: null,
        currentStepIndex: 0,
        steps: getMockWorkflowSteps(),
        meta: { scope: 'project', title: 'Getting Started', folder: 'Essentials' },
      }
      workflows.value = [await api.saveWorkflow(scopeKeyForContext(projectId), initial)]
    }

    // pick active workflow
    const defaultId = getDefaultActiveWorkflowId(workflows.value, projectId)
    activeWorkflowId.value = defaultId
    persistActiveWorkflowId(projectId, defaultId)
    loading.value = false
    return workflow.value
  }

  // Load the user-level onboarding workflow (no project id)
  const loadForUser = async () => {
    loading.value = true
    const w = await api.getUserOnboardingWorkflow('default')
    workflows.value = w ? [w] : []
    const defaultId = getDefaultActiveWorkflowId(workflows.value, null)
    activeWorkflowId.value = defaultId
    persistActiveWorkflowId(null, defaultId)
    loading.value = false
    return workflow.value
  }

  const selectWorkflow = async (id: string, projectId: string | null) => {
    activeWorkflowId.value = id
    persistActiveWorkflowId(projectId, id)
    return workflow.value
  }

  const getSteps = computed((): WorkflowStep[] => (workflow.value ? workflow.value.steps : []))

  const getCurrentStep = computed(() => {
    if (!workflow.value) return null
    return workflow.value.steps[workflow.value.currentStepIndex] ?? null
  })

  const getProgress = computed(() => {
    if (!workflow.value) return 0
    // compute progress as completed substeps / total substeps across all steps
    let total = 0
    let completed = 0
    for (const s of workflow.value.steps) {
      for (const ss of s.substeps) {
        total++
        if (ss.status === 'complete') completed++
      }
    }
    return total === 0 ? 0 : Math.round((completed / total) * 100)
  })

  const getCurrentStepProgress = computed(() => {
    if (!workflow.value) return 0
    const currentStep = workflow.value.steps[workflow.value.currentStepIndex]
    if (!currentStep || currentStep.substeps.length === 0) return 0

    const totalSubsteps = currentStep.substeps.length
    const completedSubsteps = currentStep.substeps.filter((ss) => ss.status === 'complete').length

    return Math.round((completedSubsteps / totalSubsteps) * 100)
  })

  // Expose the available workflows for the current context (additive)
  const getWorkflows = computed(() => workflows.value)
  const getActiveWorkflowId = computed(() => activeWorkflowId.value)

  const saveActiveWorkflow = async () => {
    const w = workflow.value
    if (!w) return
    const scopeKey = scopeKeyForContext(w.projectId === 'user' ? null : w.projectId)
    await api.saveWorkflow(scopeKey, w as MockWorkflow)
    // refresh list in memory
    const idx = workflows.value.findIndex((x) => x.id === w.id)
    if (idx !== -1) workflows.value[idx] = { ...(w as MockWorkflow) }
    workflows.value = [...workflows.value]
  }

  const setCurrentStepIndex = async (index: number) => {
    const w = workflow.value
    if (!w) return
    if (index < 0 || index >= w.steps.length) return
    w.currentStepIndex = index
    // update statuses: mark the active step; keep completed steps complete
    for (let i = 0; i < w.steps.length; i++) {
      const s = w.steps[i]
      if (!s) continue
      if (s.status === 'complete') continue
      s.status = i === index ? 'active' : 'pending'
    }
    await saveActiveWorkflow()
  }

  const advanceStep = async () => {
    const w = workflow.value
    if (!w) return
    const next = Math.min(w.currentStepIndex + 1, w.steps.length - 1)
    await setCurrentStepIndex(next)
  }

  const retreatStep = async () => {
    const w = workflow.value
    if (!w) return
    const prev = Math.max(w.currentStepIndex - 1, 0)
    await setCurrentStepIndex(prev)
  }

  const toggleSubstep = async (stepId: string, substepId: string) => {
    const w = workflow.value
    if (!w) return
    const step = w.steps.find((s) => s.id === stepId)
    if (!step) return
    const ss = step.substeps.find((x) => x.id === substepId)
    if (!ss) return

    const substepIndex = step.substeps.indexOf(ss)
    if (substepIndex === -1) return

    if (ss.status === 'complete') {
      // Uncomplete: set back to active
      ss.status = 'active'
      ss.finished_at = null
    } else if (ss.status === 'active') {
      // Complete current substep
      ss.status = 'complete'
      ss.finished_at = new Date().toISOString()
      if (!step.started_at) step.started_at = new Date().toISOString()

      // Set next substep to active if exists
      if (substepIndex < step.substeps.length - 1) {
        const nextSubstep = step.substeps[substepIndex + 1]
        if (nextSubstep && nextSubstep.status === 'pending') {
          nextSubstep.status = 'active'
          nextSubstep.started_at = new Date().toISOString()
        }
      }
    }

    // Update step status based on substeps
    if (step.substeps.length === 0) {
      // No substeps, step can be marked complete immediately
      step.status = 'complete'
      step.finished_at = new Date().toISOString()
    } else if (step.substeps.every((x) => x.status === 'complete')) {
      // All substeps complete, mark step complete
      step.status = 'complete'
      step.finished_at = new Date().toISOString()

      // Advance to next step and set its first substep to active
      const currentStepIndex = w.steps.findIndex((s) => s.id === stepId)
      if (currentStepIndex !== -1 && currentStepIndex < w.steps.length - 1) {
        const nextStep = w.steps[currentStepIndex + 1]
        if (nextStep) {
          nextStep.status = 'active'
          nextStep.started_at = new Date().toISOString()
          w.currentStepIndex = currentStepIndex + 1

          // Set first substep of next step to active
          if (
            nextStep.substeps.length > 0 &&
            nextStep.substeps[0] &&
            nextStep.substeps[0].status === 'pending'
          ) {
            nextStep.substeps[0].status = 'active'
            nextStep.substeps[0].started_at = new Date().toISOString()
          }
        }
      }
    } else if (step.substeps.some((x) => x.status === 'complete' || x.status === 'active')) {
      step.status = 'active'
    } else {
      step.status = 'pending'
    }

    await saveActiveWorkflow()
  }

  const resetWorkflow = async () => {
    const w = workflow.value
    if (!w) return
    w.steps = getMockWorkflowSteps()
    w.currentStepIndex = 0
    w.started_at = new Date().toISOString()
    w.finished_at = null
    await saveActiveWorkflow()
  }

  // Finish the currently active step: mark it and its substeps complete and advance to next step.
  const finishCurrentStep = async () => {
    const w = workflow.value
    if (!w) return
    const idx = w.currentStepIndex
    const step = w.steps[idx]
    if (!step) return

    const now = new Date().toISOString()
    // Mark all substeps complete
    for (const ss of step.substeps) {
      ss.status = 'complete'
      ss.finished_at = ss.finished_at || now
      if (!ss.started_at) ss.started_at = now
    }

    // Mark step complete
    step.status = 'complete'
    step.finished_at = step.finished_at || now

    // Advance to next step if exists
    const nextIndex = Math.min(idx + 1, w.steps.length - 1)
    if (nextIndex > idx) {
      const next = w.steps[nextIndex]
      if (next) {
        next.status = 'active'
        next.started_at = next.started_at || now
        // set its first substep active if any
        if (next.substeps.length > 0 && next.substeps[0] && next.substeps[0].status === 'pending') {
          next.substeps[0].status = 'active'
          next.substeps[0].started_at = next.substeps[0].started_at || now
        }
        w.currentStepIndex = nextIndex
      }
    } else {
      // last step finished
      w.currentStepIndex = idx
      w.finished_at = now
      try {
        const toast = useToast()
        toast.add({
          title: 'Workflow completed',
          description: 'You finished the last step!',
          color: 'success',
        })
      } catch (e) {
        void e
      }
    }

    await saveActiveWorkflow()
  }

  // Return the status of a step by id: 'pending'|'active'|'complete' or null if not found
  const getStepStatus = (stepId: string): StepStatus | null => {
    const w = workflow.value
    if (!w) return null
    const s = w.steps.find((x) => x.id === stepId)
    return s ? s.status : null
  }

  return {
    // Backward-compatible: `workflow` is still the active workflow
    workflow: readonly(workflow as unknown as { value: ProjectWorkflow | null }),
    // Additive: expose workflows + selection
    workflows: readonly(getWorkflows),
    activeWorkflowId: readonly(getActiveWorkflowId),
    loading: readonly(loading),
    loadForProject,
    loadForUser,
    selectWorkflow,
    getSteps,
    getCurrentStep,
    getProgress,
    getCurrentStepProgress,
    setCurrentStepIndex,
    advanceStep,
    retreatStep,
    toggleSubstep,
    resetWorkflow,
    finishCurrentStep,
    getStepStatus,
  }
}
