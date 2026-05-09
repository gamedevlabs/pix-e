export function usePixeToast() {
  const toast = useToast()

  function success(description?: string, title = 'Success') {
    toast.add({
      title,
      description,
      color: 'success',
    })
  }

  function error(error: unknown, fallback = 'Something went wrong', title = 'Error') {
    let description = fallback

    // Fetch errors have both `message` (raw HTTP) and `data` (response body).
    // Prioritize the response body — it has the user-facing message.
    if (
      typeof error === 'object' &&
      error !== null &&
      'data' in error &&
      typeof (error as Record<string, unknown>).data === 'object'
    ) {
      const data = (error as Record<string, unknown>).data as Record<string, unknown>
      if (typeof data.detail === 'string') {
        description = data.detail
      } else if (typeof data.error === 'string') {
        description = data.error
      } else if (typeof data.message === 'string') {
        description = data.message
      }
    } else if (error instanceof Error) {
      description = error.message
    } else if (typeof error === 'string') {
      description = error
    }

    toast.add({
      title,
      description,
      color: 'error',
    })
  }

  return { success, error }
}
