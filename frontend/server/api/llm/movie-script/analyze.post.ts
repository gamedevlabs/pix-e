import { callStructured } from '../../../utils/openai'

export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  const { scriptContent } = body as { scriptContent: string }

  if (!scriptContent) {
    throw createError({ statusCode: 400, statusMessage: 'Missing scriptContent' })
  }

  const prompt = `You are a virtual production and Unreal Engine assistant.
You will be given a movie or episodic script. Carefully read the entire script and identify all assets that could be represented as Unreal Engine assets and reasonably sourced or matched via the Fab store (formerly Unreal Marketplace).

Your task is to extract possible asset needs, not exact products. Think in terms of searchable asset categories and keywords that a production team could use to find assets on Fab.

Only extract what is explicitly stated or clearly implied by the script. Do not invent story elements.

Fab Search Guidelines:
- Populate fab_search_keywords with clear, marketplace-style terms
- Example: "cyberpunk city", "desert cliffs", "sci-fi corridor", "military jeep", "modular interior"
- Prefer generic, reusable asset descriptions over story-specific names.

Rules:
- Output only valid JSON.
- Use empty arrays if no assets are identified.
- Reference scene numbers or scene headings when possible.
- Do not list specific Fab products—only searchable asset needs.

The provided movie script: ${scriptContent}`

  return await callStructured(
    prompt,
    '{ "result": [{ "scene": string, "asset_name": string, "asset_type": string, "fab_search_keyword": string, "notes": string }] }',
  )
})
