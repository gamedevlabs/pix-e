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
    id: 'onboarding',
    title: 'Have a Look Around',
    folder: 'Onboarding',
    completionMessage: "Nice exploration! You can continue with the Design Pillars phase whenever you're ready.",
    steps: [
      {
        id: 'onb-1',
        name: 'Getting oriented',
        description: 'Learn where things are and what each module does.',
        route: '/dashboard',
        substeps: [
          { id: 'onb-1-1', name: 'Inspect the sidebar and open any module', route: '/dashboard' },
          { id: 'onb-1-2', name: 'Have a look at the project Settings', route: '/edit' },
          { id: 'onb-1-3', name: 'Use the Search Bar to find the Dashboard', route: '/dashboard' },
        ],
      },
    ],
  },
  {
    id: 'pillars',
    title: 'Design Pillars',
    folder: 'Concept & Design',
    completionMessage: "Great work on your Design Pillars! Your pillars are shaping the vision. Check out Player Experience next to start mapping the journey.",
    steps: [
      {
        id: 'pillars-1',
        name: 'Create your first pillar',
        description: 'Add a pillar and learn how the editor works.',
        route: '/pillars',
        substeps: [
          { id: 'pillars-1-1', name: 'Open Design Pillars', route: '/pillars' },
          { id: 'pillars-1-2', name: 'Create a new pillar', route: '/pillars' },
          { id: 'pillars-1-3', name: 'Generate LLM feedback for your first pillar', route: '/pillars' },
        ],
      },
      {
        id: 'pillars-2',
        name: 'Utilize LLM for Feedback',
        description: 'Generate feedback and learn how to interpret it.',
        route: '/pillars',
        substeps: [
          { id: 'pillars-2-1', name: 'Coverage', route: '/pillars' },
          { id: 'pillars-2-2', name: 'Contradictions', route: '/pillars' },
          { id: 'pillars-2-3', name: 'Additions', route: '/pillars' },
        ],
      },
    ],
  },
  {
    id: 'player-experience',
    title: 'Player Experience',
    folder: 'Concept & Design',
    completionMessage: "Player Experience complete! Your PX chart and node graph are looking solid. Head over to Player Expectations to validate your design.",
    steps: [
      {
        id: 'px-1',
        name: 'Create your first chart',
        description: 'Build your first chart and understand the canvas.',
        route: '/pxcharts',
        substeps: [
          { id: 'px-1-1', name: 'Open Charts page', route: '/pxcharts' },
          { id: 'px-1-2', name: 'Create a new chart', route: '/pxcharts' },
          { id: 'px-1-3', name: 'Open chart by clicking on its name', route: '/pxcharts' },
          { id: 'px-1-4', name: 'Add a new container via the Add Icon', route: '/pxcharts' },
          { id: 'px-1-5', name: 'Add another container', route: '/pxcharts' },
          { id: 'px-1-6', name: 'Connect both containers', route: '/pxcharts' },
        ],
      },
      {
        id: 'px-2',
        name: 'Setup your first node',
        description: 'Add nodes, connect them, and attach components.',
        route: '/pxnodes',
        substeps: [
          { id: 'px-2-1', name: 'Add a Component Definition', route: '/pxcomponentdefinitions' },
          { id: 'px-2-2', name: 'Create your first node', route: '/pxnodes' },
          { id: 'px-2-3', name: 'Add a component to your new node', route: '/pxnodes' },
          { id: 'px-2-4', name: 'Open a chart and add a node to any container', route: '/pxcharts' },
        ],
      },
    ],
  },
  {
    id: 'player-expectations',
    title: 'Player Expectations',
    folder: 'Validation',
    completionMessage: "Validation done! You've captured and reviewed your player expectations. Why not explore the Movie Script Evaluator next?",
    steps: [
      {
        id: 'pe-1',
        name: 'Check out Player Expectations',
        description: 'Open the page and inspect the sentiment analysis.',
        route: '/player-expectations',
        substeps: [
          { id: 'pe-1-1', name: 'Open Player Expectations Page', route: '/player-expectations' },
          { id: 'pe-1-2', name: 'Inspect Sentiment Analysis', route: '/sentiments' },
        ],
      },
    ],
  },
  {
    id: 'movie-script-evaluator',
    title: 'Movie Script Evaluator',
    folder: 'Discover',
    completionMessage: "You've completed the Movie Script Evaluator workflow! You're now fully equipped to evaluate scripts for virtual production. 🎉",
    steps: [
      {
        id: 'mse-1',
        name: 'Run your first evaluation',
        description: 'Try the standalone evaluator and understand the output.',
        route: '/movie-script-evaluator',
        substeps: [
          {
            id: 'mse-1-1',
            name: 'Open Movie Script Evaluator',
            route: '/movie-script-evaluator',
          },
          {
            id: 'mse-1-2',
            name: 'Create an evaluation and review results',
            route: '/movie-script-evaluator',
          },
        ],
      },
    ],
  },
]

// ─── Standalone onboarding template ──────────────────────────────────────────
//
// Shown to a user who has no projects yet.
// Once the user creates their first project this is marked complete,
// and subsequent projects skip it (the onboarding phase is pre-completed).

export const ONBOARDING_TEMPLATE: PhaseTemplate = {
  id: 'user-onboarding',
  title: 'Getting Started',
  folder: 'Onboarding',
  completionMessage: "You've completed the Getting Started workflow! Your first project is ready — open it and begin your design journey.",
  steps: [
    {
      id: 'user-onb-1',
      name: 'Create Account and Log In',
      description: 'Sign up for a free account and log in to pix:e.',
      route: '/login',
      substeps: [
        { id: 'user-onb-1-1', name: 'Open the login page', route: '/login' },
        { id: 'user-onb-1-2', name: 'Create an account or log in', route: '/login' },
      ],
    },
    {
      id: 'user-onb-2',
      name: 'Create your first project',
      description: 'Set up a project so you can use the project workflows.',
      route: '/create',
      substeps: [
        { id: 'user-onb-2-1', name: 'Project Information', route: '/create' },
        { id: 'user-onb-2-2', name: 'Project Details', route: '/create' },
        { id: 'user-onb-2-3', name: 'Review Project Settings', route: '/create' },
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
}

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

/** Instantiate a single phase template into a WorkflowInstance for a given project. */
function instantiatePhase(
  phase: PhaseTemplate,
  projectId: string,
  isFirstPhase: boolean,
): WorkflowInstance {
  const now = new Date().toISOString()
  return {
    id: `wf-${projectId}-${phase.id}`,
    projectId,
    started_at: now,
    finished_at: null,
    currentStepIndex: 0,
    meta: { scope: 'project', title: phase.title, folder: phase.folder },
    steps: phase.steps.map((s, i) => {
      const step = instantiateStep(s, isFirstPhase && i === 0)
      step.orderIndex = i
      return step
    }),
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

/**
 * Create a fresh set of WorkflowInstances for a project from the template.
 * The completed user-onboarding workflow is always prepended as the first entry
 * so it remains visible in the project's phase picker (marked done).
 */
export function createProjectWorkflows(
  projectId: string,
  onboardingAlreadyDone: boolean,
  completedUserOnboarding?: WorkflowInstance,
): WorkflowInstance[] {
  // Build the project-level phase instances
  const phaseInstances = WORKFLOW_TEMPLATE.map((phase, index) => {
    const isFirstPhase = index === 0
    const instance = instantiatePhase(phase, projectId, isFirstPhase && !onboardingAlreadyDone)
    if (isFirstPhase && onboardingAlreadyDone) {
      return markPhaseComplete(instance)
    }
    return instance
  })

  // Prepend the completed user-onboarding snapshot so it always shows as the first phase
  if (completedUserOnboarding) {
    // Re-id it for this project so it doesn't clash across projects
    const snapshot: WorkflowInstance = {
      ...JSON.parse(JSON.stringify(completedUserOnboarding)),
      id: `wf-${projectId}-user-onboarding`,
      projectId,
    }
    return [snapshot, ...phaseInstances]
  }

  return phaseInstances
}

/** Create a fresh standalone onboarding WorkflowInstance for the user. */
export function createOnboardingWorkflow(): WorkflowInstance {
  const now = new Date().toISOString()
  return {
    id: 'wf-user-onboarding',
    projectId: 'user',
    started_at: now,
    finished_at: null,
    currentStepIndex: 0,
    meta: { scope: 'user', title: ONBOARDING_TEMPLATE.title, folder: ONBOARDING_TEMPLATE.folder },
    steps: ONBOARDING_TEMPLATE.steps.map((s, i) => {
      const step = instantiateStep(s, i === 0)
      step.orderIndex = i
      return step
    }),
  }
}

// ─── In-memory emulator ───────────────────────────────────────────────────────

export class WorkflowApiEmulator {
  /** project id → list of phase workflow instances */
  private projectWorkflows: Record<string, WorkflowInstance[]> = {}
  /** user id → standalone onboarding instance */
  private userWorkflows: Record<string, WorkflowInstance> = {}
  /** project id (or 'user') → active workflow id */
  private activeWorkflowIds: Record<string, string> = {}

  constructor() {
    // Seed the standalone onboarding workflow for the default user.
    this.userWorkflows['default'] = createOnboardingWorkflow()
  }

  // ── Active workflow id ─────────────────────────────────────────────────────

  getActiveWorkflowId(scopeKey: string): string | null {
    return this.activeWorkflowIds[scopeKey] ?? null
  }

  setActiveWorkflowId(scopeKey: string, id: string | null): void {
    if (id) this.activeWorkflowIds[scopeKey] = id
    else delete this.activeWorkflowIds[scopeKey]
  }

  // ── Project workflows ──────────────────────────────────────────────────────

  /** Return all phase workflows for a project, or an empty array if none exist yet. */
  async getWorkflowsByProjectId(projectId: string): Promise<WorkflowInstance[]> {
    const list = this.projectWorkflows[projectId]
    return list ? JSON.parse(JSON.stringify(list)) : []
  }

  /**
   * Seed a project with a full set of workflows from the template.
   * Pass `onboardingAlreadyDone: true` for projects created after the first one.
   * Always prepends the current (completed) user-onboarding as the first phase.
   */
  async seedProject(projectId: string, onboardingAlreadyDone: boolean): Promise<WorkflowInstance[]> {
    const completedOnboarding = this.userWorkflows['default']
      ? markPhaseComplete(JSON.parse(JSON.stringify(this.userWorkflows['default'])))
      : undefined
    const instances = createProjectWorkflows(projectId, onboardingAlreadyDone, completedOnboarding)
    this.projectWorkflows[projectId] = JSON.parse(JSON.stringify(instances))
    return JSON.parse(JSON.stringify(instances))
  }

  /** Persist a single workflow instance (upsert by id). */
  async saveWorkflow(workflow: WorkflowInstance): Promise<WorkflowInstance> {
    if (workflow.projectId === 'user') {
      this.userWorkflows['default'] = JSON.parse(JSON.stringify(workflow))
      return JSON.parse(JSON.stringify(workflow))
    }

    const list = this.projectWorkflows[workflow.projectId] ?? []
    const idx = list.findIndex((w) => w.id === workflow.id)
    if (idx === -1) list.push(workflow)
    else list[idx] = workflow
    this.projectWorkflows[workflow.projectId] = JSON.parse(JSON.stringify(list))
    return JSON.parse(JSON.stringify(workflow))
  }

  // ── User onboarding workflow ───────────────────────────────────────────────

  async getUserOnboardingWorkflow(userId = 'default'): Promise<WorkflowInstance | null> {
    const w = this.userWorkflows[userId]
    return w ? JSON.parse(JSON.stringify(w)) : null
  }

  /** Mark the standalone onboarding workflow as fully complete. */
  async completeOnboardingWorkflow(userId = 'default'): Promise<void> {
    const w = this.userWorkflows[userId]
    if (!w) return
    const completed = markPhaseComplete(w)
    this.userWorkflows[userId] = completed

    // Refresh the embedded snapshot in every project that was already seeded
    for (const [projectId, list] of Object.entries(this.projectWorkflows)) {
      const snapshotId = `wf-${projectId}-user-onboarding`
      const idx = list.findIndex((x) => x.id === snapshotId)
      const fresh: WorkflowInstance = {
        ...JSON.parse(JSON.stringify(completed)),
        id: snapshotId,
        projectId,
      }
      if (idx !== -1) {
        list[idx] = fresh
      } else {
        list.unshift(fresh)
      }
    }
  }

  /** Returns true if the user has at least one project seeded (i.e. has created a project). */
  hasAnyProject(): boolean {
    return Object.keys(this.projectWorkflows).length > 0
  }
}
