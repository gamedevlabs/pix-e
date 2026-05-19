import { useApi } from '~/composables/useApi'

export function usePxExport() {
  const { apiFetch } = useApi()
  const loading = ref<boolean>(false)
  const error = ref<unknown>(null)
  const { success, error: errorToast } = usePixeToast()

  async function exportPxData(): Promise<object> {
    loading.value = true
    let data
    try {
      data = await apiFetch<object>('/api/pxexport/', {
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      })
    } catch (err) {
      error.value = err
      errorToast(err)
    } finally {
      loading.value = false
    }

    return data!
  }

  async function importPxData(payload: object) {
    try {
      await apiFetch<object>('/api/pximport/', {
        method: 'POST',
        body: payload,
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      })
      success('JSON imported successfully!')
    } catch (err) {
      error.value = err
      errorToast(err)
    }
  }

  return {
    loading,
    error,
    exportPxData,
    importPxData,
  }
}
