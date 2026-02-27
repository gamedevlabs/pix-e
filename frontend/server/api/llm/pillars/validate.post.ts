import { callStructured } from '../../../utils/openai'

export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  const { name, description } = body

  if (!name || !description) {
    throw createError({ statusCode: 400, statusMessage: 'Missing name or description' })
  }

  const prompt = `Validate the following Game Design Pillar.
Check for structural issues regarding the following points:
1. The name does not match the description.
2. The intent of the pillar is not clear.
3. The pillar focuses on more than one aspect.
4. The description uses bullet points or lists.
Name: ${name}
Description: ${description}
For each feedback limit your answer to one sentence.
Answer as if you were talking directly to the designer.`

  const schemaHint = `{
  "hasStructureIssue": boolean,
  "structuralIssues": [{ "title": string, "description": string, "severity": number (1-5) }],
  "content_feedback": string
}`

  return await callStructured(prompt, schemaHint)
})
