import { ref, computed, readonly } from '#imports'
import {
  WorkflowApiEmulator,
  getMockWorkflowSteps,
  type StepStatus,
  type WorkflowStep,
  type ProjectWorkflow,
} from '~/mock_data/mock_workflow'

// In-memory emulator for a single workflow per project
const api = new WorkflowApiEmulator()

export const useProjectWorkflow = () => {
  const workflow = ref<ProjectWorkflow | null>(null)
  const loading = ref(false)

  const loadForProject = async (projectId: string) => {
    loading.value = true
    const w = await api.getByProjectId(projectId)
    if (w) {
      workflow.value = w
    } else {
      // initialize a fresh workflow if missing
      const now = new Date().toISOString()
      workflow.value = {
        id: `wf-${projectId}-${Date.now()}`,
        projectId,
        started_at: now,
        finished_at: null,
        currentStepIndex: 0,
        steps: getMockWorkflowSteps(),
      }
      await api.save(projectId, workflow.value)
    }
    loading.value = false
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
    await api.save(w.projectId, w)
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

    await api.save(w.projectId, w)
  }

  const resetWorkflow = async () => {
    const w = workflow.value
    if (!w) return
    w.steps = getMockWorkflowSteps()
    w.currentStepIndex = 0
    w.started_at = new Date().toISOString()
    w.finished_at = null
    await api.save(w.projectId, w)
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

    await api.save(w.projectId, w)
  }

  // Return the status of a step by id: 'pending'|'active'|'complete' or null if not found
  const getStepStatus = (stepId: string): StepStatus | null => {
    const w = workflow.value
    if (!w) return null
    const s = w.steps.find((x) => x.id === stepId)
    return s ? s.status : null
  }

  return {
    workflow: readonly(workflow),
    loading: readonly(loading),
    loadForProject,
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
