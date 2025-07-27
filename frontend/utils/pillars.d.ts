type PillarDTO = {
  pillarId: number
  name: string
  description: string
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
  pillarFeedback: PillarDTO[]
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


