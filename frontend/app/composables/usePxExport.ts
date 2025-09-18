const BASE_URL = 'http://localhost:8000/'

export function usePxExport() {
  const loading = ref<boolean>(false)
  const error = ref<unknown>(null)
  const API_URL = BASE_URL + 'api/'
  const { success, error: errorToast } = usePixeToast()

  async function exportPxData(): Promise<object> {
    loading.value = true
    let data
    try {
      data = await $fetch<object>(API_URL + 'pxexport/', {
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
      await $fetch<object>(API_URL + 'pximport/', {
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
