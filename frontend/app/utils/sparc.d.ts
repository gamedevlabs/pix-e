// SPARC evaluation types

type SPARCEvaluationMode = 'monolithic' | 'quick_scan' | 'deep_dive' | 'interactive'

type SPARCReadinessStatus = 'Ready' | 'Nearly Ready' | 'Needs Work' | 'Not Ready'

// Individual aspect result from agentic mode
// Each aspect has its own schema, but they all share these common fields
type SPARCAspectResult = {
  score: number
  suggestions: string[]
  issues?: string[]
  missing_elements?: string[]
  missing_theme_elements?: string[]
  [key: string]: unknown
}

// Aggregated quick scan response
type SPARCQuickScanResponse = {
  readiness_score: number
  readiness_status: SPARCReadinessStatus
  aspect_scores: {
    aspect: string
    score: number
  }[]
  strongest_aspects: string[]
  weakest_aspects: string[]
  critical_gaps: string[]
  estimated_time_to_ready: string
  next_steps: string[]

  // Individual aspect results
  player_experience?: SPARCAspectResult
  theme?: SPARCAspectResult
  gameplay?: SPARCAspectResult
  place?: SPARCAspectResult
  unique_features?: SPARCAspectResult
  story_narrative?: SPARCAspectResult
  goals_challenges_rewards?: SPARCAspectResult
  art_direction?: SPARCAspectResult
  purpose?: SPARCAspectResult
  opportunities_risks?: SPARCAspectResult
}

// Monolithic response
type SPARCMonolithicResponse = {
  overall_assessment: string
  aspects_evaluated: {
    aspect_name: string
    assessment: string
  }[]
  missing_aspects: string[]
  suggestions: string[]
  additional_details: string[]
  readiness_verdict: string
}

// Game concept
type GameConcept = {
  id: number
  user: number
  content: string
  is_current: boolean
  last_sparc_evaluation: number | null
  created_at: string
  updated_at: string
}

// SPARC Evaluation (from database)
type SPARCEvaluation = {
  id: number
  game_text: string
  context: string
  mode: SPARCEvaluationMode
  model_id: string
  execution_time_ms: number
  total_tokens: number
  estimated_cost_eur: string
  aspect_results: SPARCEvaluationResult[]
  created_at: string
  updated_at: string
}

// SPARC Evaluation Result (individual aspect from database)
type SPARCEvaluationResult = {
  id: number
  aspect: string
  score: number | null
  agent_name: string
  model_used: string
  execution_time_ms: number | null
  result_data: SPARCAspectResult | SPARCMonolithicResponse | SPARCQuickScanResponse
  created_at: string
}
