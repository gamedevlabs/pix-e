import { callStructured } from '../../../utils/openai'

export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  const { pillars, designIdea } = body as { pillars: Array<{ id: number; name: string; description: string }>; designIdea: string }

  if (!pillars || !designIdea) {
    throw createError({ statusCode: 400, statusMessage: 'Missing pillars or designIdea' })
  }

  const pillarsText = pillars.map((p, i) => `${i + 1}. ${p.name}: ${p.description}`).join('\n')

  const prompt = `Assume the role of a game design expert.
Evaluate if the following Game Design Idea is sufficiently covered by the following Game Design Pillars.

Game Design Idea: ${designIdea}

Design Pillars: ${pillarsText}
If not, add new pillars to cover the missing aspects.`

  return await callStructured(
    prompt,
    '{ "additions": [{ "pillarId": number, "name": string, "description": string }] }',
  )
})
