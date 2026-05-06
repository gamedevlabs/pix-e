import type { UserApiKey, CreateApiKeyPayload, UpdateApiKeyPayload } from '~/types/api-key'

/**
 * Composable providing CRUD operations for user API keys.
 * Keys are managed per-provider and support testing connectivity.
 */
export function useApiKeysApi() {
  const config = useRuntimeConfig()
  const baseUrl = config.public.apiBase
  const csrfToken = useCookie('csrftoken')

  function apiUrl(path: string) {
    return `${baseUrl}${path}`
  }

  function doFetch<T>(url: string, opts?: Record<string, unknown>): Promise<T> {
    return sessionFetch<T>(url, opts)
  }

  /**
   * Fetch all API keys for the authenticated user.
   * Returns masked keys only — the raw key value is never exposed.
   */
  async function fetchKeys(): Promise<UserApiKey[]> {
    return doFetch(apiUrl('/api/accounts/api-keys/'), {
      credentials: 'include',
    })
  }

  /**
   * Create a new API key for a provider.
   * The `key` field in the payload is write-only and won't be returned.
   * @param payload - Provider, label, key value and optional metadata.
   * @returns The created key with its masked_key visible.
   */
  async function createKey(payload: CreateApiKeyPayload): Promise<UserApiKey> {
    return doFetch(apiUrl('/api/accounts/api-keys/'), {
      method: 'POST',
      credentials: 'include',
      headers: { 'X-CSRFToken': csrfToken.value } as HeadersInit,
      body: payload,
    })
  }

  /**
   * Update an existing API key's metadata (label, active status, etc.).
   * The key value itself cannot be changed — create a new key instead.
   * @param id - UUID of the key to update.
   * @param payload - Fields to update (all optional).
   * @returns The updated key.
   */
  async function updateKey(id: string, payload: UpdateApiKeyPayload): Promise<UserApiKey> {
    return doFetch(apiUrl(`/api/accounts/api-keys/${id}/`), {
      method: 'PATCH',
      credentials: 'include',
      headers: { 'X-CSRFToken': csrfToken.value } as HeadersInit,
      body: payload,
    })
  }

  /**
   * Permanently delete an API key.
   * @param id - UUID of the key to delete.
   */
  async function deleteKey(id: string): Promise<void> {
    return doFetch(apiUrl(`/api/accounts/api-keys/${id}/`), {
      method: 'DELETE',
      credentials: 'include',
      headers: { 'X-CSRFToken': csrfToken.value } as HeadersInit,
    })
  }

  /**
   * Test connectivity for an API key by making a lightweight request.
   * This endpoint is rate-limited to prevent abuse.
   * @param id - UUID of the key to test.
   * @returns Status result with a human-readable detail message.
   */
  async function testKey(id: string): Promise<{ status: string; detail: string }> {
    return doFetch(apiUrl(`/api/accounts/api-keys/${id}/test/`), {
      method: 'POST',
      credentials: 'include',
      headers: { 'X-CSRFToken': csrfToken.value } as HeadersInit,
    })
  }

  return { fetchKeys, createKey, updateKey, deleteKey, testKey }
}
