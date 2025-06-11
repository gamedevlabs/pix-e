type PillarDTO = {
  id: number
  title: string
  description: string
}

interface Pillar extends NamedEntity {
  id: number
  name: string
  description: string
  llm_feedback: PillarFeedback
}

type GameDesign = {
  game_id: number
  description: string
}

type PillarFeedback = {
  hasStructureIssue: boolean
  structuralIssues: {
    description: string
    severity: number
  }[]
  content_feedback: string
}
