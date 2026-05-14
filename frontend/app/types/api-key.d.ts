/**
 * Supported LLM provider types.
 * - `openai` — OpenAI API (GPT-4, GPT-4o, etc.)
 * - `gemini` — Google Gemini API
 * - `morpheus` — TUM CIT Morpheus cluster (free for students/staff)
 * - `custom` — Any OpenAI-compatible API (Azure, Groq, etc.)
 */
export type ProviderType = 'openai' | 'gemini' | 'morpheus' | 'custom'

/**
 * A user-stored API key configuration.
 * The raw `key` value is NEVER returned by the API; only `masked_key`
 * (last 4 characters) is visible after creation.
 */
export interface UserApiKey {
  /** Primary key UUID. */
  id: string
  /** The LLM provider this key belongs to. */
  provider: ProviderType
  /** Human-readable label chosen by the user. */
  label: string
  /** Custom base URL for the provider API. */
  base_url: string
  /** Whether this key is currently enabled for requests. */
  is_active: boolean
  /** Reason the key was disabled: 'auth_failure' means provider rejected it. */
  disabled_reason: string
  /** Masked key value — only the last 4 characters are visible. */
  masked_key: string
  /** Timestamp of the last successful API test, or null if never tested. */
  last_used_at: string | null
  /** Creation timestamp. */
  created_at: string
  /** Last update timestamp. */
  updated_at: string
}

/**
 * Payload for creating a new API key.
 * The `key` field is write-only and is never returned in responses.
 */
export interface CreateApiKeyPayload {
  /** The LLM provider type. */
  provider: ProviderType
  /** Human-readable label for the key. */
  label: string
  /** Raw API key value — write-only, discarded after creation. */
  key: string
  /** Optional custom base URL for the provider API. */
  base_url?: string
}

/**
 * Payload for updating an existing API key.
 * Only metadata fields can be changed by default; the key value itself
 * can only be provided when the key is disabled due to auth_failure.
 */
export interface UpdateApiKeyPayload {
  /** Updated human-readable label. */
  label?: string
  /** Toggle whether the key is active for requests. */
  is_active?: boolean
  /** Updated custom base URL. */
  base_url?: string
  /** New API key value — only accepted when key was disabled due to auth_failure. */
  key?: string
}
