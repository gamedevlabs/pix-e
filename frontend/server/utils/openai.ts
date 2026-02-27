import OpenAI from 'openai'

let _client: OpenAI | null = null

export function getOpenAIClient(): OpenAI {
  if (_client) return _client
  const config = useRuntimeConfig()
  const apiKey = (config.openaiApiKey || process.env.OPENAI_API_KEY || '').trim()
  if (!apiKey) throw new Error('OPENAI_API_KEY is not configured')
  _client = new OpenAI({ apiKey })
  return _client
}

export const MODEL = 'gpt-4o-mini'

/**
 * Call OpenAI and parse a structured JSON response.
 * The system prompt instructs the model to return valid JSON matching the described schema.
 */
export async function callStructured<T>(prompt: string, schemaHint: string): Promise<T> {
  const client = getOpenAIClient()

  const response = await client.chat.completions.create({
    model: MODEL,
    temperature: 0.7,
    response_format: { type: 'json_object' },
    messages: [
      {
        role: 'system',
        content: `You are a helpful assistant. Always respond with valid JSON only, no markdown fences.\nExpected response shape: ${schemaHint}`,
      },
      { role: 'user', content: prompt },
    ],
  })

  const content = response.choices[0]?.message?.content ?? '{}'
  return JSON.parse(content) as T
}
