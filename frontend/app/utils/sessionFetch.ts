/* eslint-disable @typescript-eslint/no-explicit-any */

/**
 * Custom error thrown when the user's encryption session key has expired.
 * The frontend should catch this and show the password re-entry modal.
 */
export class SessionExpiredError extends Error {
  constructor(message?: string) {
    super(message ?? 'Encryption key expired. Enter your password to re-enable API key access.')
    this.name = 'SessionExpiredError'
  }
}

/**
 * Wraps $fetch to detect encryption-key expired errors and throw SessionExpiredError.
 *
 * Triggers on:
 * - 401 with "Encryption key expired" (from NotAuthenticated in mixin/models)
 * - 403 with CSRF-related messages (Django's CSRF middleware after session rotation)
 *
 * The caller should catch SessionExpiredError and trigger the password modal.
 * This keeps the promise chain clean — no hanging promises.
 */
const KEY_EXPIRED_MSG = 'Encryption key expired'

/**
 * Guard: don't call sessionFetch during SSR — there's no browser session.
 * The caller must ensure this only runs client-side (e.g. from onMounted or user interaction).
 */
function ensureClient(): void {
  if (import.meta.server) {
    throw new Error(
      'sessionFetch called during SSR. Wrap in onMounted() or guard with import.meta.client.',
    )
  }
}

export async function sessionFetch<T>(url: string, opts?: Record<string, unknown>): Promise<T> {
  ensureClient()
  try {
    return await $fetch<T>(url, opts)
  } catch (err: any) {
    const status = err?.response?.status ?? err?.status ?? 0
    const data = err?.data as Record<string, unknown> | undefined

    const detail: string =
      (typeof data?.detail === 'string' && data.detail) ||
      (typeof data?.error === 'string' && data.error) ||
      (typeof data?.message === 'string' && data.message) ||
      (typeof err?.message === 'string' && err.message) ||
      ''

    // Key expired → throw typed error that UI can catch
    if (status === 401 && detail.includes(KEY_EXPIRED_MSG)) {
      throw new SessionExpiredError(detail)
    }

    // Any 403 in this app is almost certainly a CSRF failure caused by
    // inconsistent session state (e.g. expired encryption key).
    if (status === 403) {
      throw new SessionExpiredError('Session expired due to CSRF token mismatch.')
    }

    throw err
  }
}
