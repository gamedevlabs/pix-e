import { callStructured } from '../../../utils/openai'

export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  const { name, description } = body

  if (!name || !description) {
    throw createError({ statusCode: 400, statusMessage: 'Missing name or description' })
  }

  const prompt = `Improve the following Game Design Pillar.
Check for structural issues regarding the following points:
1. The title does not match the description.
2. The intent of the pillar is not clear.
3. The pillar focuses on more than one aspect.
4. The description uses bullet points or lists.
Pillar Title: ${name}
Pillar Description: ${description}
Rewrite erroneous parts of the pillar and return a new pillar object.`

  const schemaHint = `{
  "pillarId": number,
  "name": string,
  "description": string
}`

  return await callStructured(prompt, schemaHint)
})
