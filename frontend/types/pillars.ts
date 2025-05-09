export type PillarDTO = {
  pillar_id: number
  title: string
  description: string
}

export type Pillar = {
  pillar_id: number
  title: string
  description: string
  llm_feedback: string
  display_open: boolean
}

export type GameDesign = {
  game_id: number
  description: string
}
export type LLMFeedback = {
  feedback: string
}