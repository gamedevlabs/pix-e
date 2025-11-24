// SPARC V2 evaluation types (router-based)

type SPARCV2Status = 'well_defined' | 'needs_work' | 'not_provided'

type SPARCV2OverallStatus = 'ready' | 'nearly_ready' | 'needs_work'

// Individual aspect result from V2 evaluation
type SimplifiedAspectResponse = {
  aspect_name: string
  status: SPARCV2Status
  reasoning: string
  suggestions: string[]
}

// Synthesis result
type SPARCSynthesis = {
  overall_status: SPARCV2OverallStatus
  overall_reasoning: string
  strongest_aspects: string[]
  weakest_aspects: string[]
  critical_gaps: string[]
  next_steps: string[]
  consistency_notes?: string
}

// Agent execution detail
type AgentExecutionDetail = {
  agent_name: string
  execution_time_ms: number
  total_tokens: number
  prompt_tokens: number
  completion_tokens: number
  success: boolean
}

// Full V2 response
type SPARCV2Response = {
  aspect_results: Record<string, SimplifiedAspectResponse>
  synthesis: SPARCSynthesis | null
  mode: string
  model_id: string
  execution_time_ms: number
  total_tokens: number
  estimated_cost_eur: number
  agent_execution_details: AgentExecutionDetail[]
}

// Aspect names for V2
type SPARCV2AspectName =
  | 'player_experience'
  | 'theme'
  | 'purpose'
  | 'gameplay'
  | 'goals_challenges_rewards'
  | 'place'
  | 'story_narrative'
  | 'unique_features'
  | 'art_direction'
  | 'opportunities_risks'
