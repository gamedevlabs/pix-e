import type { UserApiKey, CreateApiKeyPayload, UpdateApiKeyPayload } from '~/types/api-key'
import { sessionFetch } from '~/utils/sessionFetch'

export function useApiKeysApi() {
  const { apiFetch, apiUrl, csrfToken } = useApi()

  async function testKey(id: string): Promise<{ status: string; detail: string }> {
    return await sessionFetch<{ status: string; detail: string }>(
      apiUrl(`/api/accounts/api-keys/${id}/test/`),
      {
        method: 'POST',
        credentials: 'include',
        headers: { 'X-CSRFToken': csrfToken.value } as HeadersInit,
      },
    )
  }

  async function fetchKeys(): Promise<UserApiKey[]> {
    return await apiFetch<UserApiKey[]>('/api/accounts/api-keys/')
  }

  async function createKey(payload: CreateApiKeyPayload): Promise<UserApiKey> {
    return await apiFetch<UserApiKey>('/api/accounts/api-keys/', {
      method: 'POST',
      body: payload,
    })
  }

  async function updateKey(id: string, payload: UpdateApiKeyPayload): Promise<UserApiKey> {
    return await apiFetch<UserApiKey>(`/api/accounts/api-keys/${id}/`, {
      method: 'PATCH',
      body: payload,
    })
  }

  async function deleteKey(id: string): Promise<void> {
    await apiFetch(`/api/accounts/api-keys/${id}/`, {
      method: 'DELETE',
    })
  }

  return { fetchKeys, createKey, updateKey, deleteKey, testKey }
}
