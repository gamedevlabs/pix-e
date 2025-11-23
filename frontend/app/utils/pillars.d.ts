type PillarDTO = {
  pillarId: number
  name: string
  description: string
}

type CompletenessAnswer = {
  pillarId: number
  name: str
  reasoning: str
}

type ContradictionIssue = {
  pillarOneId: number
  pillarTwoId: number
  pillarOneTitle: string
  pillarTwoTitle: string
  reason: string
}

interface Pillar extends NamedEntity {
  id: number
  name: string
  description: string
  llm_feedback: PillarFeedback | null
}

type GameDesign = {
  game_id: number
  description: string
}

type PillarFeedback = {
  hasStructureIssue: boolean
  structuralIssues: {
    title: string
    description: string
    severity: number
  }[]
  content_feedback: string
}

type PillarCompletenessFeedback = {
  pillarFeedback: CompletenessAnswer[]
}

type PillarContradictionsFeedback = {
  contradictions: ContradictionIssue[]
}

type PillarAdditionsFeedback = {
  additions: PillarDTO[]
}

type PillarsInContextFeedback = {
  coverage: PillarCompletenessFeedback
  contradictions: PillarContradictionsFeedback
  proposedAdditions: PillarAdditionsFeedback
}

type ContextInPillarsFeedback = {
  rating: number
  feedback: string
}

// --- Types for improved pillar with explanations ---

type PillarChange = {
  field: 'name' | 'description'
  after: string
  reasoning: string
  issues_addressed: string[]
}

type ImprovedPillarResponse = {
  name: string
  description: string
  changes: PillarChange[]
  overall_summary: string
  validation_issues_fixed: string[]
}

type FixPillarAPIResponse = {
  pillar_id: number
  original: {
    name: string
    description: string
  }
  improved: ImprovedPillarResponse
  metadata: {
    execution_time_ms: number
    model_used: string | null
  }
}

type StructuralIssue = {
  title: string
  description: string
  severity: number
}

// --- Types for new agentic pillar evaluation ---

type ConceptFitResponse = {
  hasGaps: boolean
  pillarFeedback: CompletenessAnswer[]
  missingAspects: string[]
}

type ContradictionsResponse = {
  hasContradictions: boolean
  contradictions: ContradictionIssue[]
}

type ResolutionSuggestion = {
  pillarOneId: number
  pillarTwoId: number
  pillarOneTitle: string
  pillarTwoTitle: string
  resolutionStrategy: string
  suggestedChanges: string[]
  alternativeApproach: string
}

type ContradictionResolutionResponse = {
  resolutions: ResolutionSuggestion[]
  overallRecommendation: string
}

type EvaluateAllMetadata = {
  execution_time_ms: number
  agents_run: string[]
  all_succeeded: boolean
}

type EvaluateAllResponse = {
  concept_fit: ConceptFitResponse | null
  contradictions: ContradictionsResponse | null
  additions: PillarAdditionsFeedback | null
  resolution: ContradictionResolutionResponse | null
  metadata: EvaluateAllMetadata
}
