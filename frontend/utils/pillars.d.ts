type PillarDTO = {
  pillar_id: number
  title: string
  description: string
}

type Pillar = {
  pillar_id: number
  title: string
  description: string
  llm_feedback: string
  display_open: boolean
}

type GameDesign = {
  game_id: number
  description: string
}
type LLMFeedback = {
  feedback: string
}

type PillarFeedback = {
  hasStructureIssue: boolean
  structuralIssues: {
    description: string
    severity: number
  }[]
  content_feedback: string
}
