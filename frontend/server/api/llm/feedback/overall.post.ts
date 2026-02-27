import { callStructured } from '../../../utils/openai'

export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  const { pillars, designIdea } = body as { pillars: Array<{ id: number; name: string; description: string }>; designIdea: string }

  if (!pillars || !designIdea) {
    throw createError({ statusCode: 400, statusMessage: 'Missing pillars or designIdea' })
  }

  const pillarsText = pillars.map((p, i) => `${i + 1}. ${p.name}: ${p.description}`).join('\n')

  const coveragePrompt = `Assume the role of a game design expert.
Evaluate if the following Game Design Pillars are a good fit for the game idea, explain why.
Also check if the pillar contradicts the direction of the game idea.

Game Design Idea: ${designIdea}

Design Pillars: ${pillarsText}`

  const contradictionsPrompt = `Assume the role of a game design expert.
Evaluate if the following Game Design Pillars stand in contradiction towards each other. Use the Game Design Idea as context.

Game Design Idea: ${designIdea}

Design Pillars: ${pillarsText}`

  const additionsPrompt = `Assume the role of a game design expert.
Evaluate if the following Game Design Idea is sufficiently covered by the following Game Design Pillars.

Game Design Idea: ${designIdea}

Design Pillars: ${pillarsText}
If not, add new pillars to cover the missing aspects.`

  const [coverage, contradictions, proposedAdditions] = await Promise.all([
    callStructured<{ pillarFeedback: Array<{ pillarId: number; name: string; reasoning: string }> }>(
      coveragePrompt,
      '{ "pillarFeedback": [{ "pillarId": number, "name": string, "reasoning": string }] }',
    ),
    callStructured<{ hasContradictions: boolean; contradictions: Array<{ pillarOneId: number; pillarTwoId: number; pillarOneTitle: string; pillarTwoTitle: string; reason: string }> }>(
      contradictionsPrompt,
      '{ "hasContradictions": boolean, "contradictions": [{ "pillarOneId": number, "pillarTwoId": number, "pillarOneTitle": string, "pillarTwoTitle": string, "reason": string }] }',
    ),
    callStructured<{ additions: Array<{ pillarId: number; name: string; description: string }> }>(
      additionsPrompt,
      '{ "additions": [{ "pillarId": number, "name": string, "description": string }] }',
    ),
  ])

  return { coverage, contradictions, proposedAdditions }
})
