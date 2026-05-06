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

  async function reestablish(password: string): Promise<boolean> {
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
      return true
    } catch (err: unknown) {
      const e = err as Record<string, unknown>
      const response = e?.response as Record<string, unknown> | undefined
      const data = e?.data as Record<string, unknown> | undefined
      const status = (response?.status as number) || 0
      const detail =
        (data?.detail as string) || (data?.error as string) || (e?.message as string) || ''
      if (status === 403 && detail.includes('Wrong password')) {
        toast.add({ title: 'Wrong password', color: 'error' })
      } else if (status === 403 && detail.includes('CSRF')) {
        toast.add({ title: 'Session expired. Please log in again.', color: 'error' })
        // Hard session expiry — can't recover with password alone
        dismissModal()
        useRouter().push('/login')
      } else {
        toast.add({ title: detail || 'Failed to refresh key', color: 'error' })
      }
      return false
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
