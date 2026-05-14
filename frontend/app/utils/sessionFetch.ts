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

export class InvalidApiKeyError extends Error {
  constructor(message?: string) {
    super(message ?? 'Your API key is invalid. Please re-add it in Settings.')
    this.name = 'InvalidApiKeyError'
  }
}

/**
 * Wraps $fetch to detect encryption-key expired errors and throw SessionExpiredError.
 *
 * Triggers on:
 * - 401 with "Encryption key expired" (from NotAuthenticated in mixin/models)
 * - 401 with "invalid/disabled" (invalid API key → prompts re-add in Settings)
 * - 403 with CSRF-related messages (Django's CSRF middleware after session rotation)
 *
 * The caller should catch SessionExpiredError and trigger the password modal.
 * InvalidApiKeyError should show a toast telling the user to re-add the key.
 * This keeps the promise chain clean — no hanging promises.
 */
const KEY_EXPIRED_MSG = 'Encryption key expired'
const SESSION_EXPIRED_MSG = 'Session expired'
const INVALID_KEY_MSG = 'API key is invalid'

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
    if (
      status === 401 &&
      (detail.includes(KEY_EXPIRED_MSG) || detail.includes(SESSION_EXPIRED_MSG))
    ) {
      throw new SessionExpiredError(detail)
    }

    // Invalid/disabled API key → throw typed error that UI can catch
    if (status === 401 && detail.includes(INVALID_KEY_MSG)) {
      throw new InvalidApiKeyError(detail)
    }

    // Any 403 from the LLM/pillars API is a session/CSRF issue — our own
    // endpoints never return 403 for business-logic reasons (they return
    // 400, 401, or 500).  A real DRF PermissionDenied on a non-LLM endpoint
    // (e.g. IsOwner on a generic model) could match too, but in practice
    // the password modal recovery is harmless for the user.
    if (status === 403) {
      throw new SessionExpiredError(
        detail.includes('csrf')
          ? 'Session expired due to CSRF token mismatch.'
          : 'Session expired. Enter your password to re-enable API key access.',
      )
    }

    throw err
  }
}
