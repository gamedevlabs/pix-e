// TODO: Connect mock data to real backend (workflow-layer)

import type { StepStatus, Substep, WorkflowStep, ProjectWorkflow } from '~/utils/workflow'

// Exported helper to provide the mock steps for initialization or reset
export function getMockWorkflowSteps(): WorkflowStep[] {
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

// In-memory emulator for a single workflow per project
export class WorkflowApiEmulator {
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
      steps: getMockWorkflowSteps(),
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

// (no runtime instance exported; composables should instantiate their own emulators)
