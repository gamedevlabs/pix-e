// Production-ready error handling for moodboards

import type { MoodboardError, APIError } from '~/types/moodboard'

export class MoodboardException extends Error {
  constructor(
    message: string,
    public code: string,
    public recoverable: boolean = false,
    public context?: Record<string, any>
  ) {
    super(message)
    this.name = 'MoodboardException'
  }

  toMoodboardError(): MoodboardError {
    return {
      code: this.code,
      message: this.message,
      recoverable: this.recoverable,
      context: this.context,
      timestamp: Date.now()
    }
  }
}

// Specific error types
export class NetworkError extends MoodboardException {
  constructor(message: string, context?: Record<string, any>) {
    super(message, 'NETWORK_ERROR', true, context)
  }
}

export class ValidationError extends MoodboardException {
  constructor(message: string, field?: string) {
    super(message, 'VALIDATION_ERROR', false, { field })
  }
}

export class PermissionError extends MoodboardException {
  constructor(message: string, required_permission?: string) {
    super(message, 'PERMISSION_ERROR', false, { required_permission })
  }
}

export class NotFoundError extends MoodboardException {
  constructor(resource: string, id: string) {
    super(`${resource} not found`, 'NOT_FOUND', false, { resource, id })
  }
}

export class QuotaExceededError extends MoodboardException {
  constructor(quota_type: string, limit: number) {
    super(`${quota_type} quota exceeded`, 'QUOTA_EXCEEDED', false, { quota_type, limit })
  }
}

// Error handler utilities
export const handleAPIError = (error: any): MoodboardException => {
  // Network errors
  if (!navigator.onLine) {
    return new NetworkError('No internet connection. Please check your network and try again.')
  }

  if (error.code === 'NETWORK_ERR' || error.message === 'Network Error') {
    return new NetworkError('Network error occurred. Please try again.', { originalError: error })
  }

  // HTTP errors
  if (error.response) {
    const status = error.response.status
    const data = error.response.data

    switch (status) {
      case 400:
        return new ValidationError(data?.message || 'Invalid request data')
      case 401:
        return new PermissionError('Authentication required')
      case 403:
        return new PermissionError(data?.message || 'Permission denied')
      case 404:
        return new NotFoundError('Resource', 'unknown')
      case 413:
        return new QuotaExceededError('file_size', data?.max_size || 0)
      case 429:
        return new QuotaExceededError('rate_limit', data?.limit || 0)
      case 500:
        return new MoodboardException('Server error occurred. Please try again later.', 'SERVER_ERROR', true)
      default:
        return new MoodboardException(
          data?.message || 'An unexpected error occurred',
          'UNKNOWN_ERROR',
          status < 500
        )
    }
  }

  // Client-side errors
  if (error.name === 'AbortError') {
    return new MoodboardException('Operation was cancelled', 'CANCELLED', true)
  }

  if (error.name === 'TimeoutError') {
    return new NetworkError('Request timed out. Please try again.')
  }

  // Default fallback
  return new MoodboardException(
    error.message || 'An unexpected error occurred',
    'UNKNOWN_ERROR',
    false,
    { originalError: error.toString() }
  )
}

// Retry mechanism with exponential backoff
export const withRetry = async <T>(
  operation: () => Promise<T>,
  options: {
    maxRetries?: number
    baseDelay?: number
    maxDelay?: number
    retryCondition?: (error: MoodboardException) => boolean
  } = {}
): Promise<T> => {
  const {
    maxRetries = 3,
    baseDelay = 1000,
    maxDelay = 10000,
    retryCondition = (error: MoodboardException) => error.recoverable
  } = options

  let lastError: MoodboardException

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await operation()
    } catch (error) {
      lastError = error instanceof MoodboardException ? error : handleAPIError(error)

      // Don't retry on last attempt or non-recoverable errors
      if (attempt === maxRetries || !retryCondition(lastError)) {
        throw lastError
      }

      // Calculate delay with exponential backoff and jitter
      const delay = Math.min(
        baseDelay * Math.pow(2, attempt) + Math.random() * 1000,
        maxDelay
      )

      console.warn(`Operation failed (attempt ${attempt + 1}/${maxRetries + 1}), retrying in ${delay}ms...`, lastError)
      await new Promise(resolve => setTimeout(resolve, delay))
    }
  }

  throw lastError!
}

// Error recovery strategies
export const recoveryStrategies = {
  // Refresh authentication token
  refreshAuth: async (): Promise<void> => {
    // Implementation depends on your auth system
    try {
      const { $auth } = useNuxtApp()
      if ($auth && typeof ($auth as any).refresh === 'function') {
        await ($auth as any).refresh()
      }
    } catch (error) {
      console.warn('Failed to refresh auth:', error)
    }
  },

  // Reload data from server
  reloadData: async (id: string): Promise<void> => {
    const { fetchMoodboard } = useMoodboards()
    await fetchMoodboard(id)
  },

  // Sync offline changes
  syncOfflineChanges: async (): Promise<void> => {
    const offlineQueue = getOfflineQueue()
    for (const operation of offlineQueue) {
      try {
        await operation.execute()
        removeFromOfflineQueue(operation.id)
      } catch (error) {
        console.warn('Failed to sync offline operation:', operation, error)
      }
    }
  },

  // Clear cache and reload
  clearCacheAndReload: (): void => {
    clearMoodboardCache()
    window.location.reload()
  }
}

// Error notification system
export const showErrorNotification = (error: MoodboardError): void => {
  const toast = useToast()

  const color: 'warning' | 'error' = error.recoverable ? 'warning' : 'error'

  const notification = {
    title: getErrorTitle(error.code),
    description: error.message,
    color,
    timeout: error.recoverable ? 5000 : 0
  }

  toast.add(notification)
}

const getErrorTitle = (code: string): string => {
  const titles: Record<string, string> = {
    NETWORK_ERROR: 'Connection Error',
    VALIDATION_ERROR: 'Invalid Input',
    PERMISSION_ERROR: 'Access Denied',
    NOT_FOUND: 'Not Found',
    QUOTA_EXCEEDED: 'Limit Exceeded',
    SERVER_ERROR: 'Server Error',
    UNKNOWN_ERROR: 'Unexpected Error'
  }
  return titles[code] || 'Error'
}

const getErrorActions = (error: MoodboardError) => {
  const actions = []

  if (error.recoverable) {
    actions.push({
      label: 'Retry',
      color: 'primary',
      variant: 'solid',
      click: () => {
        // Retry logic will be implemented per component
      }
    })
  }

  if (error.code === 'NETWORK_ERROR') {
    actions.push({
      label: 'Work Offline',
      color: 'neutral',
      variant: 'outline',
      click: () => {
        enableOfflineMode()
      }
    })
  }

  return actions
}

// Offline queue management
let offlineQueue: Array<{ id: string; execute: () => Promise<void> }> = []

const getOfflineQueue = () => offlineQueue
const removeFromOfflineQueue = (id: string) => {
  offlineQueue = offlineQueue.filter(op => op.id !== id)
}

const enableOfflineMode = () => {
  // Implementation for offline mode
}

const clearMoodboardCache = () => {
  // Clear relevant caches
}
