import { callStructured } from '../../../utils/openai'

export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  const { pillars, designIdea } = body as {
    pillars: Array<{ id: number; name: string; description: string }>
    designIdea?: string
  }

  if (!pillars || !Array.isArray(pillars) || pillars.length === 0) {
    throw createError({ statusCode: 400, statusMessage: 'Missing or empty pillars array' })
  }

  const context = designIdea?.trim() || 'No design idea provided yet.'
  const pillarsText = pillars.map((p, i) => `${i + 1}. ${p.name}: ${p.description}`).join('\n')

  const prompt = `Assume the role of a game design expert.
Evaluate if the following Game Design Pillars stand in contradiction towards each other. Use the Game Design Idea as context.

Game Design Idea: ${context}

Design Pillars: ${pillarsText}`

  return await callStructured(
    prompt,
    '{ "hasContradictions": boolean, "contradictions": [{ "pillarOneId": number, "pillarTwoId": number, "pillarOneTitle": string, "pillarTwoTitle": string, "reason": string }] }',
  )
})
