import { callStructured } from '../../../utils/openai'

export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  const { pillars, context } = body as { pillars: Array<{ id: number; name: string; description: string }>; context: string }

  if (!pillars || !context) {
    throw createError({ statusCode: 400, statusMessage: 'Missing pillars or context' })
  }

  const pillarsText = pillars.map((p, i) => `${i + 1}. ${p.name}: ${p.description}`).join('\n')

  const prompt = `Assume the role of a game design expert.
Evaluate how well the following idea aligns with the given Game Design Pillars.

Idea: ${context}

Design Pillars: ${pillarsText}`

  return await callStructured(
    prompt,
    '{ "rating": number (1-5), "feedback": string }',
  )
})
