/**
 * Tracks whether the user's encryption key has expired and provides
 * a method to re-establish it with the user's password.
 *
 * Usage:
 *   import { sessionFetch, SessionExpiredError } from '~/utils/sessionFetch'
 *   import { getSessionKey } from '~/composables/useSessionKey'
 *
 *   try {
 *     await sessionFetch('/api/some-endpoint/')
 *   } catch (err) {
 *     if (err instanceof SessionExpiredError) {
 *       getSessionKey().handleSessionExpired(() => sessionFetch('/api/some-endpoint/'))
 *     }
 *   }
 */
export function useSessionKey() {
  const config = useRuntimeConfig()
  const sessionExpired = ref(false)
  const showPasswordModal = ref(false)
  const toast = useToast()

  let retryFn: (() => Promise<unknown>) | null = null

  async function reestablish(
    password: string,
  ): Promise<{ ok: boolean; error?: string; openSettings?: boolean }> {
    // First, do a GET to refresh the CSRF cookie (might be stale from key expiry)
    try {
      await $fetch(`${config.public.apiBase}/api/accounts/me/`, {
        credentials: 'include',
      })
    } catch {
      // OK if this fails — we just needed the CSRF cookie refresh
    }
    const csrfToken = useCookie('csrftoken')
    try {
      await $fetch(`${config.public.apiBase}/api/accounts/reestablish-key/`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'X-CSRFToken': csrfToken.value } as HeadersInit,
        body: { password },
      })
      // Key re-established — retry the original request
      if (retryFn) {
        await retryFn()
      }
      sessionExpired.value = false
      showPasswordModal.value = false
      retryFn = null
      toast.add({ title: 'Session refreshed', color: 'success' })
      return { ok: true }
    } catch (err: unknown) {
      const e = err as Record<string, unknown>
      const response = e?.response as Record<string, unknown> | undefined
      const data = e?.data as Record<string, unknown> | undefined
      const status = (response?.status as number) || 0
      const detail =
        (data?.detail as string) || (data?.error as string) || (e?.message as string) || ''
      if (status === 403 && detail.includes('Wrong password')) {
        return { ok: false, error: 'Wrong password' }
      } else if (status === 403 && detail.includes('CSRF')) {
        dismissModal()
        useRouter().push('/login')
        return { ok: false, error: 'Session expired. Please log in again.' }
      } else {
        // Retry failed — not a password issue. Close modal, show toast.
        dismissModal()
        const isInvalidKey =
          detail.includes('API key is invalid') ||
          detail.includes('disabled') ||
          detail.includes('no valid')
        const msg = detail || 'Failed to refresh key'
        if (isInvalidKey) {
          toast.add({ title: 'API Key Invalid', description: msg, color: 'error' })
        } else {
          toast.add({ title: 'Error', description: msg, color: 'error' })
        }
        return { ok: false, error: msg, openSettings: isInvalidKey }
      }
    }
  }

  /**
   * Stores the retry function and shows the password re-entry modal.
   * Call this after catching SessionExpiredError from sessionFetch.
   * The modal's reestablish() will invoke the stored retry on success.
   */
  function handleSessionExpired<T>(retry: () => Promise<T>): void {
    retryFn = retry as () => Promise<unknown>
    sessionExpired.value = true
    showPasswordModal.value = true
  }

  function dismissModal() {
    sessionExpired.value = false
    showPasswordModal.value = false
    retryFn = null
  }

  return {
    sessionExpired,
    showPasswordModal,
    reestablish,
    handleSessionExpired,
    dismissModal,
  }
}

let _instance: ReturnType<typeof useSessionKey> | null = null

export function getSessionKey() {
  if (!_instance) {
    _instance = useSessionKey()
  }
  return _instance
}
