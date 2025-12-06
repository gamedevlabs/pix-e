// --- Types for node validation ---

type NodeCoherenceIssue = {
  title: string
  description: string
  severity: number
  issue_type:
    | 'title_description_mismatch'
    | 'component_value_contradiction'
    | 'component_irrelevance'
    | 'unclear_purpose'
    | 'component_conflict'
  related_components: string[]
}

type NodeValidationFeedback = {
  has_issues: boolean
  issues: NodeCoherenceIssue[]
  overall_coherence_score: number
  summary: string
}

// --- Types for node fix suggestions ---

type NodeChange = {
  field: 'name' | 'description'
  after: string
  reasoning: string
  issues_addressed: string[]
}

type ComponentChange = {
  component_id: string
  component_name: string
  current_value: string | number | boolean | null
  suggested_value: string | number | boolean | null
  reasoning: string
  issues_addressed: string[]
}

type ImprovedNodeResponse = {
  name: string
  description: string
  changes: NodeChange[]
  component_changes: ComponentChange[]
  overall_summary: string
  validation_issues_fixed: string[]
}

type FixNodeAPIResponse = {
  node_id: string
  original: {
    name: string
    description: string
    components: NodeComponentInfo[]
  }
  improved: ImprovedNodeResponse
  metadata: {
    execution_time_ms: number
    model_used: string | null
  }
}

type NodeComponentInfo = {
  component_id: string
  definition_name: string
  definition_type: string
  value: string | number | boolean | null
}

// Extended PxNode type with LLM feedback
interface PxNodeWithFeedback extends PxNode {
  llm_feedback?: NodeValidationFeedback | null
}
