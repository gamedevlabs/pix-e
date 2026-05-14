import type { UserApiKey, CreateApiKeyPayload, UpdateApiKeyPayload } from '~/types/api-key'
import { sessionFetch } from '~/utils/sessionFetch'

export function useApiKeysApi() {
  const config = useRuntimeConfig()
  const baseUrl = config.public.apiBase
  const csrfToken = useCookie('csrftoken')

  function apiUrl(path: string) {
    return `${baseUrl}${path}`
  }

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
    return await $fetch<UserApiKey[]>(`${baseUrl}/api/accounts/api-keys/`, {
      credentials: 'include',
    })
  }

  async function createKey(payload: CreateApiKeyPayload): Promise<UserApiKey> {
    return await $fetch<UserApiKey>(`${baseUrl}/api/accounts/api-keys/`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'X-CSRFToken': csrfToken.value } as HeadersInit,
      body: payload,
    })
  }

  async function updateKey(id: string, payload: UpdateApiKeyPayload): Promise<UserApiKey> {
    return await $fetch<UserApiKey>(`${baseUrl}/api/accounts/api-keys/${id}/`, {
      method: 'PATCH',
      credentials: 'include',
      headers: { 'X-CSRFToken': csrfToken.value } as HeadersInit,
      body: payload,
    })
  }

  async function deleteKey(id: string): Promise<void> {
    await $fetch(`${baseUrl}/api/accounts/api-keys/${id}/`, {
      method: 'DELETE',
      credentials: 'include',
      headers: { 'X-CSRFToken': csrfToken.value } as HeadersInit,
    })
  }

  return { fetchKeys, createKey, updateKey, deleteKey, testKey }
}
