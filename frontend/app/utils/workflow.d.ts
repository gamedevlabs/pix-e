export const workflowStepStatuses = ['pending', 'active', 'complete'] as const
export type StepStatus = (typeof workflowStepStatuses)[number]

export interface Substep {
  id: string
  name: string
  description?: string
  status: StepStatus
  started_at?: string | null
  finished_at?: string | null
  timeSpentSeconds?: number
  route?: string
}

export interface WorkflowStep {
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

export interface ProjectWorkflow {
  id: string
  projectId: string
  started_at?: string | null
  finished_at?: string | null
  currentStepIndex: number
  steps: WorkflowStep[]
}
