// TODO: Connect mock data to real backend (workflow-layer)
//
// Architecture:
//   WORKFLOW_TEMPLATE   — single source of truth for all project phases/steps/substeps.
//                         Edit this to change the workflow for ALL projects at once.
//   ONBOARDING_TEMPLATE — standalone user-level workflow shown before any project exists.
//                         Guides the user to create their first project.
//   WorkflowApiEmulator — in-memory store. Instantiates fresh state from the templates
//                         for each project and persists mutations per project ID.

import type { StepStatus, Substep, WorkflowStep, ProjectWorkflow } from '~/utils/workflow'

// ─── Shared types ────────────────────────────────────────────────────────────

export type WorkflowScope = 'project' | 'user'

export interface WorkflowMeta {
  scope: WorkflowScope
  title: string
  /** Groups workflows into named phases shown in the slideover phase-picker. */
  folder: string
  /** Short description shown in the slideover below the workflow title. */
  description?: string
}

/** A workflow instance tied to a specific project (or the standalone user onboarding). */
export type WorkflowInstance = ProjectWorkflow & { meta: WorkflowMeta }

// ─── Template types ──────────────────────────────────────────────────────────

interface SubstepTemplate {
  id: string
  name: string
  description?: string
  route?: string
}

interface StepTemplate {
  id: string
  name: string
  description?: string
  route?: string
  substeps: SubstepTemplate[]
}

export interface PhaseTemplate {
  /** Unique key used as the workflow id suffix and meta.title. */
  id: string
  /** Display title shown in the phase picker. */
  title: string
  /** Folder / phase group shown in the slideover. */
  folder: string
  /** Short description displayed below the workflow title in the slideover. */
  description?: string
  /** Toast message shown when the user completes this workflow. */
  completionMessage?: string
  steps: StepTemplate[]
}

// ─── Project workflow template ────────────────────────────────────────────────
//
// This is the SINGLE source of truth. Adjust phases, steps and substeps here
// and every project will automatically get the updated structure on next load.

export const WORKFLOW_TEMPLATE: PhaseTemplate[] = [
  {
    id: 'user-onboarding',
    title: 'Getting Started',
    folder: 'Onboarding',
    description: 'Create your account, log in, and set up your first project to get going.',
    completionMessage:
      "You've completed the Getting Started workflow! Your first project is ready — open it and begin your design journey.",
    steps: [
      {
        id: 'user-onb-2',
        name: 'Create your first project',
        description: 'Set up a project so you can use the project workflows.',
        route: '/create',
        substeps: [
          { id: 'user-onb-2-0', name: 'Open the Create page', route: '/create', description: 'Start the process of setting up your first project.' },
          { id: 'user-onb-2-1', name: 'Project Information', route: '/create', description: 'Provide basic information for your new project.' },
          { id: 'user-onb-2-2', name: 'Project Details', route: '/create', description: 'Fill in specific details about what your project entails.' },
          { id: 'user-onb-2-3', name: 'Review Project Settings', route: '/create', description: 'Finalize and review your project configuration before creation.' },
        ],
      },
      {
        id: 'user-onb-3',
        name: 'Done',
        description: "You're ready to go!",
        route: '/dashboard',
        substeps: [],
      },
    ],
  },
  {
    id: 'onboarding',
    title: 'Have a Look Around',
    folder: 'Onboarding',
    description:
        'Get familiar with how the app is structured. This phase helps you understand where to find things and how the different modules connect.',
    completionMessage:
        "Nice exploration! You now have a basic understanding of the workspace. Continue with the Design Pillars phase to start shaping your game.",
    steps: [
      {
        id: 'onb-1',
        name: 'Understand the Interface',
        description:
            'Before creating anything, learn how to navigate the system and where key features are located.',
        route: '/dashboard',
        substeps: [
          {
            id: 'onb-1-1',
            name: 'Open any module through the sidebar',
            route: undefined,
            description:
                'The sidebar is your main navigation tool. Each module represents a different part of your design process. Opening modules helps you understand how the tool is structured and how workflows are separated.',
          },
          {
            id: 'onb-1-2',
            name: 'Explore the project settings',
            route: '/edit',
            description:
                'Project settings define global parameters of your project. This includes naming, structure, and configuration that affect all modules. Understanding this helps you see how everything is connected.',
          },
          {
            id: 'onb-1-3',
            name: 'Try the search functionality',
            route: '/dashboard',
            description:
                'The search bar allows you to quickly find elements across your project. This becomes especially important as your project grows in complexity.',
          },
        ],
      },
    ],
  },

  {
    id: 'pillars',
    title: 'Design Pillars',
    folder: 'Design & Validation',
    description:
        'Define the core ideas of your game. Design Pillars act as guiding principles that influence all later design decisions.',
    completionMessage:
        'Great work! Your design pillars now define the foundation of your game. Next, you can map how players will experience these ideas.',
    steps: [
      {
        id: 'pillars-1',
        name: 'Create your first pillar',
        description:
            'Start by defining a core idea that represents what your game is about.',
        route: '/pillars',
        substeps: [
          {
            id: 'pillars-1-1',
            name: 'Open Design Pillars',
            route: '/pillars',
            description:
                'This module is where you define your core design ideas. Each pillar represents a fundamental concept that should be reflected throughout your game.',
          },
          {
            id: 'pillars-1-2',
            name: 'Create a new pillar',
            route: '/pillars',
            description:
                'Create a pillar that represents a key aspect of your game (e.g., “Fast-paced combat” or “Emotional storytelling”). This will guide later design decisions.',
          },
        ],
      },
      {
        id: 'pillars-2',
        name: 'Validate your pillar with AI',
        description:
            'Use AI feedback to refine and strengthen your idea.',
        route: '/pillars',
        substeps: [
          {
            id: 'pillars-2-1',
            name: 'Generate feedback for your pillar',
            route: '/pillars',
            description:
                'The AI analyzes your pillar and provides feedback on clarity, completeness, and potential issues. This helps you identify weaknesses early.',
          },
          {
            id: 'pillars-2-2',
            name: 'Improve your pillar based on feedback',
            route: '/pillars',
            description:
                'Use the generated feedback to refine your pillar. This step helps you turn vague ideas into strong, actionable design principles.',
          },
        ],
      },
      {
        id: 'pillars-3',
        name: 'Expand your core idea',
        description:
            'Add more detail and explore how your idea could evolve.',
        route: '/pillars',
        substeps: [
          {
            id: 'pillars-3-1',
            name: 'Write a detailed idea and generate feedback',
            route: '/pillars',
            description:
                'Expand your pillar with additional features or variations. Then generate feedback again to validate if your idea remains consistent and strong.',
          },
        ],
      },
      {
        id: 'pillars-4',
        name: 'Understand AI analysis tools',
        description:
            'Learn how to interpret different types of AI feedback.',
        route: '/pillars',
        substeps: [
          {
            id: 'pillars-4-1',
            name: 'Check coverage',
            route: '/pillars',
            description:
                'Coverage shows how well your pillars describe your game. Missing coverage may indicate unclear or incomplete design areas.',
          },
          {
            id: 'pillars-4-2',
            name: 'Identify contradictions',
            route: '/pillars',
            description:
                'Contradictions highlight conflicts between your pillars. Resolving these ensures a more coherent design.',
          },
          {
            id: 'pillars-4-3',
            name: 'Explore suggested additions',
            route: '/pillars',
            description:
                'The AI suggests additional ideas or improvements that could strengthen your design. These are optional but useful inspirations.',
          },
        ],
      },
    ],
  },

  {
    id: 'player-experience',
    title: 'Player Experience',
    folder: 'Design & Validation',
    description:
        'Map how players move through your game. This phase helps you structure gameplay flow and interactions.',
    completionMessage:
        'Great! You’ve mapped out how players experience your game. Now you can validate whether this aligns with expectations.',
    steps: [
      {
        id: 'px-1',
        name: 'Create your first experience flow',
        description:
            'Build a chart that represents how players move through your game.',
        route: '/pxcharts',
        substeps: [
          {
            id: 'px-1-1',
            name: 'Open Charts page',
            route: '/pxcharts',
            description:
                'Charts represent player journeys. Each chart is a high-level structure of how players move through your game.',
          },
          {
            id: 'px-1-2',
            name: 'Create a new chart',
            route: '/pxcharts',
            description:
                'Create a chart to start mapping your player experience. This acts as a container for your gameplay flow.',
          },
          {
            id: 'px-1-3',
            name: 'Open your chart',
            route: '/pxcharts',
            description:
                'Opening the chart brings you into the canvas where you can visually structure player flow.',
          },
          {
            id: 'px-1-4',
            name: 'Add a container',
            route: '/pxcharts',
            description:
                'Containers represent stages or segments of gameplay (e.g., tutorial, combat, exploration).',
          },
          {
            id: 'px-1-5',
            name: 'Add another container',
            route: '/pxcharts',
            description:
                'Adding multiple containers allows you to define progression or different gameplay phases.',
          },
          {
            id: 'px-1-6',
            name: 'Connect containers',
            route: '/pxcharts',
            description:
                'Connections define how players move between stages. This creates a flow of the experience.',
          },
        ],
      },
      {
        id: 'px-2',
        name: 'Define gameplay building blocks',
        description:
            'Use nodes and components to describe what actually happens in your game.',
        route: '/pxnodes',
        substeps: [
          {
            id: 'px-2-1',
            name: 'Create a component definition',
            route: '/pxcomponentdefinitions',
            description:
                'Component Definitions describe reusable gameplay elements (e.g., combat, dialogue, puzzle mechanics). These are building blocks for your nodes.',
          },
          {
            id: 'px-2-2',
            name: 'Create your first node',
            route: '/pxnodes',
            description:
                'A node represents a specific gameplay moment or interaction. Think of it as a concrete instance in your player experience.',
          },
          {
            id: 'px-2-3',
            name: 'Add a component to your node',
            route: '/pxnodes',
            description:
                'Attaching components defines what happens in that moment (e.g., player fights, explores, interacts).',
          },
          {
            id: 'px-2-4',
            name: 'Place a node inside a chart',
            route: '/pxcharts',
            description:
                'Placing nodes into containers connects your gameplay elements to the overall player journey.',
          },
        ],
      },
    ],
  },

  {
    id: 'player-expectations',
    title: 'Player Expectations',
    folder: 'Design & Validation',
    description:
        'Validate how players might perceive your game using sentiment analysis and expectation modeling.',
    completionMessage:
        "Great validation work! You now understand how your design might be perceived by players.",
    steps: [
      {
        id: 'pe-1',
        name: 'Explore player expectations',
        description:
            'Understand how your design aligns with player perception.',
        route: '/player-expectations',
        substeps: [
          {
            id: 'pe-1-1',
            name: 'Open Player Expectations',
            route: '/player-expectations',
            description:
                'This module collects and analyzes how players might interpret your design based on your inputs.',
          },
          {
            id: 'pe-1-2',
            name: 'Review sentiment analysis',
            route: '/sentiments',
            description:
                'Sentiment analysis shows whether elements are perceived positively, negatively, or neutrally. This helps you detect mismatches between intention and perception.',
          },
        ],
      },
    ],
  },

  {
    id: 'movie-script-evaluator',
    title: 'Movie Script Evaluator',
    folder: 'Discover More',
    description:
        'Explore an additional tool for analyzing scripts and narratives in virtual production contexts.',
    completionMessage:
        "Nice! You've explored all major features of the platform.",
    steps: [
      {
        id: 'mse-1',
        name: 'Explore the evaluator',
        description:
            'Take a quick look at how scripts can be analyzed.',
        route: '/movie-script-evaluator',
        substeps: [
          {
            id: 'mse-1-1',
            name: 'Open Movie Script Evaluator',
            route: '/movie-script-evaluator',
            description:
                'This tool analyzes scripts and extracts structural and narrative insights. It’s useful for storytelling and virtual production workflows.',
          },
        ],
      },
    ],
  },
];


// ─── Instantiation helpers ────────────────────────────────────────────────────

function instantiateSubstep(t: SubstepTemplate, isFirst: boolean): Substep {
  const now = new Date().toISOString()
  return {
    id: t.id,
    name: t.name,
    description: t.description,
    route: t.route,
    status: isFirst ? 'active' : 'pending',
    started_at: isFirst ? now : null,
    finished_at: null,
    timeSpentSeconds: 0,
  }
}

function instantiateStep(t: StepTemplate, isFirst: boolean): WorkflowStep {
  const now = new Date().toISOString()
  return {
    id: t.id,
    name: t.name,
    description: t.description,
    route: t.route,
    orderIndex: 0, // will be set by caller
    status: isFirst ? 'active' : 'pending',
    started_at: isFirst ? now : null,
    finished_at: null,
    timeSpentSeconds: 0,
    substeps: t.substeps.map((s, i) => instantiateSubstep(s, isFirst && i === 0)),
  }
}

/** Instantiate a single phase template into a WorkflowInstance. */
function instantiatePhase(
  phase: PhaseTemplate,
  isFirstPhase: boolean,
): WorkflowInstance {
  const now = new Date().toISOString()
  return {
    id: `wf-user-${phase.id}`,
    projectId: 'user',
    started_at: now,
    finished_at: null,
    currentStepIndex: 0,
    meta: {
      scope: 'user',
      title: phase.title,
      folder: phase.folder,
      description: phase.description,
    },
    steps: phase.steps.map((s, i) => {
      const step = instantiateStep(s, isFirstPhase && i === 0)
      step.orderIndex = i
      return step
    }),
  }
}

/**
 * Create a fresh set of WorkflowInstances for a user from the template.
 */
export function createUserWorkflows(): WorkflowInstance[] {
  return WORKFLOW_TEMPLATE.map((phase, index) => {
    return instantiatePhase(phase, index === 0)
  })
}

// ─── In-memory emulator ───────────────────────────────────────────────────────

export class WorkflowApiEmulator {
  /** user id → list of phase workflow instances */
  private userWorkflows: Record<string, WorkflowInstance[]> = {}
  /** user id → active workflow id */
  private activeWorkflowIds: Record<string, string> = {}

  constructor() {
    // Seed the workflows for the default user.
    this.userWorkflows['default'] = createUserWorkflows()
  }

  // ── Active workflow id ─────────────────────────────────────────────────────

  getActiveWorkflowId(scopeKey: string): string | null {
    return this.activeWorkflowIds[scopeKey] ?? null
  }

  setActiveWorkflowId(scopeKey: string, id: string | null): void {
    if (id) {
      this.activeWorkflowIds[scopeKey] = id
    } else {
      const { [scopeKey]: _, ...rest } = this.activeWorkflowIds
      this.activeWorkflowIds = rest
    }
  }

  // ── User workflows ──────────────────────────────────────────────────────

  /** Return all phase workflows for the user. */
  async getUserWorkflows(userId: string = 'default'): Promise<WorkflowInstance[]> {
    const list = this.userWorkflows[userId]
    if (!list) {
      this.userWorkflows[userId] = createUserWorkflows()
      return JSON.parse(JSON.stringify(this.userWorkflows[userId]))
    }
    return JSON.parse(JSON.stringify(list))
  }

  async updateSubstepStatus(
    userId: string,
    workflowId: string,
    stepId: string,
    substepId: string,
    status: StepStatus,
  ): Promise<WorkflowInstance | null> {
    const list = this.userWorkflows[userId]
    if (!list) return null

    const wf = list.find((w) => w.id === workflowId)
    if (!wf) return null

    const step = wf.steps.find((s) => s.id === stepId)
    if (!step) return null

    const substep = step.substeps.find((ss) => ss.id === substepId)
    if (!substep) return null

    const now = new Date().toISOString()
    substep.status = status
    if (status === 'complete') {
      substep.finished_at = now
    } else if (status === 'active') {
      substep.started_at = now
    }

    // Update parent step status
    const allSubsteps = step.substeps
    if (allSubsteps.every((ss) => ss.status === 'complete')) {
      step.status = 'complete'
      step.finished_at = now
    } else if (allSubsteps.some((ss) => ss.status === 'active' || ss.status === 'complete')) {
      step.status = 'active'
      step.started_at = step.started_at ?? now
    }

    // Update workflow status if all steps complete
    if (wf.steps.every((s) => s.status === 'complete')) {
      wf.finished_at = now
    }

    return JSON.parse(JSON.stringify(wf))
  }

  /** Mark a specific workflow as complete. */
  async completeWorkflow(userId: string, workflowId: string): Promise<void> {
    const list = this.userWorkflows[userId]
    if (!list) return
    const index = list.findIndex((w) => w.id === workflowId)
    if (index !== -1 && list[index]) {
      list[index] = markPhaseComplete(list[index])
    }
  }
}

/** Mark every step and substep in a WorkflowInstance as complete. */
function markPhaseComplete(instance: WorkflowInstance): WorkflowInstance {
  const now = new Date().toISOString()
  return {
    ...instance,
    finished_at: now,
    currentStepIndex: instance.steps.length - 1,
    steps: instance.steps.map((step) => ({
      ...step,
      status: 'complete' as StepStatus,
      started_at: step.started_at ?? now,
      finished_at: now,
      substeps: step.substeps.map((ss) => ({
        ...ss,
        status: 'complete' as StepStatus,
        started_at: ss.started_at ?? now,
        finished_at: now,
      })),
    })),
  }
}
