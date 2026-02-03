import { ref, computed, readonly } from '#imports'

// Simple workflow types local to composable
export type StepStatus = 'pending' | 'active' | 'complete'
export type Substep = {
  id: string
  name: string
  description?: string
  status: StepStatus
  started_at?: string | null
  finished_at?: string | null
  timeSpentSeconds?: number
  route?: string
}

export type WorkflowStep = {
  id: string
  name: string
  description?: string
  orderIndex: number
  status: StepStatus
  started_at?: string | null
  finished_at?: string | null
  timeSpentSeconds?: number
  substeps: Substep[]
  route?: string
}

export type ProjectWorkflow = {
  id: string
  projectId: string
  started_at?: string | null
  finished_at?: string | null
  currentStepIndex: number
  steps: WorkflowStep[]
}

// In-memory emulator for a single workflow per project
class WorkflowApiEmulator {
  private workflows: Record<string, ProjectWorkflow> = {}

  constructor() {
    const now = new Date().toISOString()
    // seed example workflow for project "pixe"
    this.workflows['pixe'] = {
      id: 'wf-pixe-1',
      projectId: 'pixe',
      started_at: now,
      finished_at: null,
      currentStepIndex: 1,
      steps: _mockWorkflowSteps(),
    }
  }

  async getByProjectId(projectId: string): Promise<ProjectWorkflow | null> {
    const w = this.workflows[projectId]
    return w ? JSON.parse(JSON.stringify(w)) : null
  }

  async save(projectId: string, workflow: ProjectWorkflow): Promise<ProjectWorkflow> {
    this.workflows[projectId] = JSON.parse(JSON.stringify(workflow))
    return JSON.parse(JSON.stringify(this.workflows[projectId]))
  }
}

const api = new WorkflowApiEmulator()

// TODO: Connect mock data to real backend (workflow-layer)
function _mockWorkflowSteps(): WorkflowStep[] {
  const now = new Date().toISOString()
  const mkSub = (
    id: string,
    name: string,
    status: StepStatus = 'pending',
    route?: string,
  ): Substep => ({
    id,
    name,
    status,
    started_at: status === 'active' ? now : null,
    finished_at: null,
    timeSpentSeconds: 0,
    route,
  })

  return [
    {
      id: 's-1',
      name: 'Create Project',
      description: 'Set up your own project',
      orderIndex: 0,
      status: 'complete',
      started_at: now,
      finished_at: now,
      timeSpentSeconds: 0,
      substeps: [
        mkSub('s1-1', 'Project Information', 'complete', '/create'),
        mkSub('s1-2', 'Project Details', 'complete', '/create'),
        mkSub('s1-3', 'Review', 'complete', '/create'),
      ],
      route: '/create',
    },
    {
      id: 's-2',
      name: 'Game Design Pillars',
      description: 'This is the foundation of your game design',
      orderIndex: 1,
      status: 'active',
      started_at: null,
      finished_at: null,
      timeSpentSeconds: 0,
      substeps: [
        mkSub('s2-1', 'Create a new pillar', 'complete', '/pillars'),
        mkSub('s2-2', 'Generate some LLM feedback for your pillar', 'complete', '/pillars'),
        mkSub('s2-3', 'Checkout LLM Coverage, Contradictions and Additions', 'active', '/pillars'),
      ],
      route: '/pillars',
    },
    {
      id: 's-3',
      name: 'Player Experience',
      description: 'Build your first pxChart!',
      orderIndex: 2,
      status: 'pending',
      started_at: now,
      finished_at: null,
      timeSpentSeconds: 0,
      substeps: [
        mkSub('s3-1', 'Create your first Chart!', 'pending', '/pxcharts'),
        mkSub('s3-2', 'Setup a new Node and Add it to the graph', 'pending', '/pxnodes'),
        mkSub(
          's3-3',
          'Create some Component Definitions and add them to a node',
          'pending',
          '/pxcomponentdefinitions',
        ),
        mkSub(
          's3-4',
          'Setup an second node, add it to the graph and connect the two nodes',
          'pending',
          '/pxnodes',
        ),
      ],
      route: '/pxcharts',
    },
    {
      id: 's-4',
      name: 'Player Expectations',
      description: 'What does your target group want?',
      orderIndex: 3,
      status: 'pending',
      started_at: null,
      finished_at: null,
      timeSpentSeconds: 0,
      substeps: [
        mkSub('s4-1', 'Add some data to the expectations table', 'pending', '/player-expectations'),
        mkSub('s4-2', 'Check out the Sentiment Analysis', 'pending', '/sentiments'),
      ],
      route: '/player-expectations',
    },
    {
      id: 's-5',
      name: 'Finished',
      description: 'Well done!',
      orderIndex: 4,
      status: 'pending',
      started_at: null,
      finished_at: null,
      timeSpentSeconds: 0,
      substeps: [],
      route: '/dashboard',
    },
  ]
}

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
        steps: _mockWorkflowSteps(),
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
    if (!workflow.value) return
    if (index < 0 || index >= workflow.value.steps.length) return
    workflow.value.currentStepIndex = index
    // update statuses: mark the active step; keep completed steps complete
    for (let i = 0; i < workflow.value.steps.length; i++) {
      if (workflow.value.steps[i].status === 'complete') continue
      workflow.value.steps[i].status = i === index ? 'active' : 'pending'
    }
    await api.save(workflow.value.projectId, workflow.value)
  }

  const advanceStep = async () => {
    if (!workflow.value) return
    const next = Math.min(workflow.value.currentStepIndex + 1, workflow.value.steps.length - 1)
    await setCurrentStepIndex(next)
  }

  const retreatStep = async () => {
    if (!workflow.value) return
    const prev = Math.max(workflow.value.currentStepIndex - 1, 0)
    await setCurrentStepIndex(prev)
  }

  const toggleSubstep = async (stepId: string, substepId: string) => {
    if (!workflow.value) return
    const step = workflow.value.steps.find((s) => s.id === stepId)
    if (!step) return
    const ss = step.substeps.find((x) => x.id === substepId)
    if (!ss) return

    const substepIndex = step.substeps.findIndex((x) => x.id === substepId)

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
        if (nextSubstep.status === 'pending') {
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
      const currentStepIndex = workflow.value.steps.findIndex((s) => s.id === stepId)
      if (currentStepIndex < workflow.value.steps.length - 1) {
        const nextStep = workflow.value.steps[currentStepIndex + 1]
        nextStep.status = 'active'
        nextStep.started_at = new Date().toISOString()
        workflow.value.currentStepIndex = currentStepIndex + 1

        // Set first substep of next step to active
        if (nextStep.substeps.length > 0 && nextStep.substeps[0].status === 'pending') {
          nextStep.substeps[0].status = 'active'
          nextStep.substeps[0].started_at = new Date().toISOString()
        }
      }
    } else if (step.substeps.some((x) => x.status === 'complete' || x.status === 'active')) {
      step.status = 'active'
    } else {
      step.status = 'pending'
    }

    await api.save(workflow.value.projectId, workflow.value)
  }

  const resetWorkflow = async () => {
    if (!workflow.value) return
    workflow.value.steps = _mockWorkflowSteps()
    workflow.value.currentStepIndex = 0
    workflow.value.started_at = new Date().toISOString()
    workflow.value.finished_at = null
    await api.save(workflow.value.projectId, workflow.value)
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
  }
}
