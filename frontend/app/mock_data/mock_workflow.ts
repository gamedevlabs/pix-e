// TODO: Connect mock data to real backend (workflow-layer)

import type { StepStatus, Substep, WorkflowStep, ProjectWorkflow } from '~/utils/workflow'

// Minimal additive metadata for grouping/selecting workflows in UI.
// Kept local to mock layer so we don't rewrite the existing schema.
export type WorkflowScope = 'project' | 'user'
export interface WorkflowMeta {
  scope: WorkflowScope
  title: string
  folder?: string
}
export type MockWorkflow = ProjectWorkflow & { meta?: WorkflowMeta }

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
      status: 'active',
      started_at: now,
      finished_at: now,
      timeSpentSeconds: 0,
      substeps: [
        mkSub('s1-1', 'Project Information', 'active', '/create'),
        mkSub('s1-2', 'Project Details', 'pending', '/create'),
        mkSub('s1-3', 'Review', 'pending', '/create'),
      ],
      route: '/create',
    },
    {
      id: 's-2',
      name: 'Game Design Pillars',
      description: 'This is the foundation of your game design',
      orderIndex: 1,
      status: 'pending',
      started_at: null,
      finished_at: null,
      timeSpentSeconds: 0,
      substeps: [
        mkSub('s2-1', 'Create a new pillar', 'pending', '/pillars'),
        mkSub('s2-2', 'Generate some LLM feedback for your pillar', 'pending', '/pillars'),
        mkSub('s2-3', 'Checkout LLM Coverage, Contradictions and Additions', 'pending', '/pillars'),
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

// User-level onboarding steps (doesn't require a project id)
export function getMockOnboardingWorkflowSteps(): WorkflowStep[] {
  const { now, mkSub } = mkSubFactory()
  return [
    {
      id: 'onb-1',
      name: 'Welcome',
      description: 'A quick tour to get you started.',
      orderIndex: 0,
      status: 'active',
      started_at: now,
      finished_at: null,
      timeSpentSeconds: 0,
      substeps: [mkSub('onb1-1', 'Learn the basics', 'active', '/dashboard')],
      route: '/dashboard',
    },
    {
      id: 'onb-2',
      name: 'Create your first project',
      description: 'Set up a project so you can use the project workflows.',
      orderIndex: 1,
      status: 'pending',
      started_at: null,
      finished_at: null,
      timeSpentSeconds: 0,
      substeps: [
        mkSub('onb2-1', 'Open the create project flow', 'pending', '/create'),
        mkSub('onb2-2', 'Finish project creation', 'pending', '/create'),
      ],
      route: '/create',
    },
    {
      id: 'onb-3',
      name: 'Done',
      description: 'You’re ready to go.',
      orderIndex: 2,
      status: 'pending',
      started_at: null,
      finished_at: null,
      timeSpentSeconds: 0,
      substeps: [],
      route: '/dashboard',
    },
  ]
}

// --- Additional module-specific workflows (minimal additional mock data) ---
const mkSubFactory = () => {
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
  return { now, mkSub }
}

export function getMockToolingDiscoverySteps(): WorkflowStep[] {
  const { now, mkSub } = mkSubFactory()
  return [
    {
      id: 'setup-1',
      name: 'Getting oriented',
      description: 'Learn where things are and what each module does.',
      orderIndex: 0,
      status: 'active',
      started_at: now,
      finished_at: null,
      timeSpentSeconds: 0,
      substeps: [
        mkSub('setup1-1', 'Open the dashboard and pick a project', 'active', '/dashboard'),
        mkSub('setup1-2', 'Explore navigation (sidebar + search)', 'pending', '/dashboard'),
      ],
      route: '/dashboard',
    },
    {
      id: 'setup-2',
      name: 'Create your first project',
      description: 'Set up a project so workflows can track progress.',
      orderIndex: 1,
      status: 'pending',
      started_at: null,
      finished_at: null,
      timeSpentSeconds: 0,
      substeps: [
        mkSub('setup2-1', 'Open the create project flow', 'pending', '/create'),
        mkSub('setup2-2', 'Fill out basic project information', 'pending', '/create'),
        mkSub('setup2-3', 'Finish & review', 'pending', '/create'),
      ],
      route: '/create',
    },
  ]
}

export function getMockPillarsWorkflowSteps(): WorkflowStep[] {
  const { now, mkSub } = mkSubFactory()
  return [
    {
      id: 'pillars-1',
      name: 'Create your first pillar',
      description: 'Add a pillar and learn how the editor works.',
      orderIndex: 0,
      status: 'active',
      started_at: now,
      finished_at: null,
      timeSpentSeconds: 0,
      substeps: [
        mkSub('pillars1-1', 'Open Pillars', 'active', '/pillars'),
        mkSub('pillars1-2', 'Create a new pillar', 'pending', '/pillars'),
        mkSub('pillars1-3', 'Refine wording and save', 'pending', '/pillars'),
      ],
      route: '/pillars',
    },
    {
      id: 'pillars-2',
      name: 'Get LLM feedback',
      description: 'Generate feedback and learn how to interpret it.',
      orderIndex: 1,
      status: 'pending',
      started_at: null,
      finished_at: null,
      timeSpentSeconds: 0,
      substeps: [
        mkSub('pillars2-1', 'Generate LLM feedback for a pillar', 'pending', '/pillars'),
        mkSub('pillars2-2', 'Check coverage / contradictions / additions', 'pending', '/pillars'),
      ],
      route: '/pillars',
    },
  ]
}

export function getMockPlayerExperienceWorkflowSteps(): WorkflowStep[] {
  const { now, mkSub } = mkSubFactory()
  return [
    {
      id: 'px-1',
      name: 'Create a pxChart',
      description: 'Build your first chart and understand the canvas.',
      orderIndex: 0,
      status: 'active',
      started_at: now,
      finished_at: null,
      timeSpentSeconds: 0,
      substeps: [
        mkSub('px1-1', 'Open Player Experience Charts', 'active', '/pxcharts'),
        mkSub('px1-2', 'Create your first chart', 'pending', '/pxcharts'),
      ],
      route: '/pxcharts',
    },
    {
      id: 'px-2',
      name: 'Build a small graph',
      description: 'Add nodes, connect them, and attach components.',
      orderIndex: 1,
      status: 'pending',
      started_at: null,
      finished_at: null,
      timeSpentSeconds: 0,
      substeps: [
        mkSub('px2-1', 'Create a node', 'pending', '/pxnodes'),
        mkSub('px2-2', 'Create a component definition', 'pending', '/pxcomponentdefinitions'),
        mkSub('px2-3', 'Attach components to a node', 'pending', '/pxnodes'),
        mkSub('px2-4', 'Connect nodes in the chart', 'pending', '/pxnodes'),
      ],
      route: '/pxnodes',
    },
  ]
}

export function getMockPlayerExpectationsWorkflowSteps(): WorkflowStep[] {
  const { now, mkSub } = mkSubFactory()
  return [
    {
      id: 'pe-1',
      name: 'Enter expectations data',
      description: 'Populate the table and learn the workflow.',
      orderIndex: 0,
      status: 'active',
      started_at: now,
      finished_at: null,
      timeSpentSeconds: 0,
      substeps: [
        mkSub('pe1-1', 'Open Player Expectations', 'active', '/player-expectations'),
        mkSub('pe1-2', 'Add a few expectation records', 'pending', '/player-expectations'),
      ],
      route: '/player-expectations',
    },
    {
      id: 'pe-2',
      name: 'Review sentiment analysis',
      description: 'Interpret sentiment and annotations.',
      orderIndex: 1,
      status: 'pending',
      started_at: null,
      finished_at: null,
      timeSpentSeconds: 0,
      substeps: [mkSub('pe2-1', 'Open Sentiments', 'pending', '/sentiments')],
      route: '/sentiments',
    },
  ]
}

export function getMockMovieScriptEvaluatorWorkflowSteps(): WorkflowStep[] {
  const { now, mkSub } = mkSubFactory()
  return [
    {
      id: 'mse-1',
      name: 'Run your first evaluation',
      description: 'Try the standalone evaluator and understand output.',
      orderIndex: 0,
      status: 'active',
      started_at: now,
      finished_at: null,
      timeSpentSeconds: 0,
      substeps: [
        mkSub('mse1-1', 'Open Movie Script Evaluator', 'active', '/movie-script-evaluator'),
        mkSub(
          'mse1-2',
          'Create an evaluation and review results',
          'pending',
          '/movie-script-evaluator',
        ),
      ],
      route: '/movie-script-evaluator',
    },
  ]
}

// In-memory emulator for workflows (multiple per project) + a user workflow
export class WorkflowApiEmulator {
  private projectWorkflows: Record<string, MockWorkflow[]> = {}
  private userWorkflows: Record<string, MockWorkflow> = {}

  constructor() {
    const now = new Date().toISOString()

    // Seed user onboarding workflow (single, global for mock)
    this.userWorkflows['default'] = {
      id: 'wf-user-onboarding',
      projectId: 'user',
      started_at: now,
      finished_at: null,
      currentStepIndex: 0,
      steps: getMockOnboardingWorkflowSteps(),
      meta: { scope: 'user', title: 'Getting Started', folder: 'Onboarding' },
    }

    // Seed example workflows for project "pixe" (minimal set; no duplicates)
    this.projectWorkflows['pixe'] = [
      {
        id: 'wf-pixe-getting-oriented',
        projectId: 'pixe',
        started_at: now,
        finished_at: null,
        currentStepIndex: 0,
        steps: getMockToolingDiscoverySteps(),
        // Folder name kept aligned with the new structure requested by UI.
        meta: { scope: 'project', title: 'Getting Oriented', folder: 'Onboarding' },
      },
      {
        id: 'wf-pixe-pillars',
        projectId: 'pixe',
        started_at: now,
        finished_at: null,
        currentStepIndex: 0,
        steps: getMockPillarsWorkflowSteps(),
        meta: { scope: 'project', title: 'Pillars', folder: 'Concept & Design' },
      },
      {
        id: 'wf-pixe-player-experience',
        projectId: 'pixe',
        started_at: now,
        finished_at: null,
        currentStepIndex: 0,
        steps: getMockPlayerExperienceWorkflowSteps(),
        meta: { scope: 'project', title: 'Player Experience', folder: 'Concept & Design' },
      },
      {
        id: 'wf-pixe-player-expectations',
        projectId: 'pixe',
        started_at: now,
        finished_at: null,
        currentStepIndex: 0,
        steps: getMockPlayerExpectationsWorkflowSteps(),
        meta: { scope: 'project', title: 'Player Expectations', folder: 'Validation' },
      },
      {
        id: 'wf-pixe-movie-script-evaluator',
        projectId: 'pixe',
        started_at: now,
        finished_at: null,
        currentStepIndex: 0,
        steps: getMockMovieScriptEvaluatorWorkflowSteps(),
        meta: { scope: 'project', title: 'Movie Script Evaluator', folder: 'Discover' },
      },
    ]
  }

  // Backward-compatible: return the first workflow for a project.
  async getByProjectId(projectId: string): Promise<ProjectWorkflow | null> {
    const list = this.projectWorkflows[projectId]
    const w = list && list.length ? list[0] : null
    return w ? JSON.parse(JSON.stringify(w)) : null
  }

  async getWorkflowsByProjectId(projectId: string): Promise<MockWorkflow[]> {
    const list = this.projectWorkflows[projectId] || []
    return JSON.parse(JSON.stringify(list))
  }

  async getUserOnboardingWorkflow(userId = 'default'): Promise<MockWorkflow | null> {
    const w = this.userWorkflows[userId]
    return w ? JSON.parse(JSON.stringify(w)) : null
  }

  async saveWorkflow(scopeKey: string, workflow: MockWorkflow): Promise<MockWorkflow> {
    if (scopeKey.startsWith('user:')) {
      const userId = scopeKey.slice('user:'.length) || 'default'
      this.userWorkflows[userId] = JSON.parse(JSON.stringify(workflow))
      return JSON.parse(JSON.stringify(this.userWorkflows[userId]))
    }

    if (scopeKey.startsWith('project:')) {
      const projectId = scopeKey.slice('project:'.length)
      const list = this.projectWorkflows[projectId] || []
      const idx = list.findIndex((w) => w.id === workflow.id)
      if (idx === -1) list.push(workflow)
      else list[idx] = workflow
      this.projectWorkflows[projectId] = JSON.parse(JSON.stringify(list))
      return JSON.parse(JSON.stringify(workflow))
    }

    // fallback: treat as projectId
    const projectId = scopeKey
    const list = this.projectWorkflows[projectId] || []
    const idx = list.findIndex((w) => w.id === workflow.id)
    if (idx === -1) list.push(workflow)
    else list[idx] = workflow
    this.projectWorkflows[projectId] = JSON.parse(JSON.stringify(list))
    return JSON.parse(JSON.stringify(workflow))
  }
}

// (no runtime instance exported; composables should instantiate their own emulators)
