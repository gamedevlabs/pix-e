export function usePixeToast() {
  const toast = useToast()

  function success(description?: string, title = 'Success') {
    const show = () => {
      toast.add({
        title,
        description,
        color: 'success',
      })
    }

    const nuxtApp = useNuxtApp()

    if (nuxtApp.isHydrating) {
      onNuxtReady(show)
    } else {
      show()
    }
  }

  function error(error: unknown, fallback = 'Something went wrong', title = 'Error') {
    let description = fallback

    if (error instanceof Error) {
      description = error.message
    } else if (typeof error === 'string') {
      description = error
    } else if (
      typeof error === 'object' &&
      error !== null &&
      'data' in error &&
      typeof (error as Record<string, unknown>).data === 'object'
    ) {
      const data = (error as Record<string, unknown>).data as Record<string, unknown>
      if (typeof data.message === 'string') {
        description = data.message
      }
    }

    const show = () => {
      toast.add({
        title,
        description,
        color: 'error',
      })
    }

    const nuxtApp = useNuxtApp()

    if (nuxtApp.isHydrating) {
      onNuxtReady(show)
    } else {
      show()
    }
  }

  return { success, error }
}
