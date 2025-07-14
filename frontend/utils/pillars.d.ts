type PillarDTO = {
  id: number
  name: string
  description: string
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

type PillarsInContextFeedback = {
  pillarFeedback: {
    name: string,
    description: string,
  }[]
  additionalFeedback: string
  proposedAdditions: {
    name: string
    description: string
  }[]
}
