type PillarDTO = {
  pillarId: number
  name: string
  description: string
}

type ContradictionIssue = {
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
  proposedAdditions: PillarDTO[]
  ideaIssues: PillarDTO[]
}

type PillarContradictionsFeedback = {
  hasContradictions: boolean
  contradictions: ContradictionIssue[]
}

type PillarsInContextFeedback = {
  pillarFeedback: {
    name: string
    description: string
  }[]
  additionalFeedback: string
  proposedAdditions: PillarDTO[]
}


