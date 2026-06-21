export function usePixeToast() {
  const toast = useToast()
  const nuxtApp = useNuxtApp()

  function safeShow(fn: () => void) {
    if (import.meta.server) return

    if (nuxtApp.isHydrating) {
      onNuxtReady(() => {
        requestAnimationFrame(fn)
      })
    } else {
      fn()
    }
  }

  function success(description?: string, title = 'Success') {
    safeShow(() => {
      toast.add({
        title,
        description,
        color: 'success',
      })
    })
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

    safeShow(() => {
      toast.add({
        title,
        description,
        color: 'error',
      })
    })
  }

  function info(description?: string, title = 'Info') {
    safeShow(() => {
      toast.add({
        title,
        description,
        color: 'info',
      })
    })
  }

  return { success, error, info }
}
