import { useApi } from '~/composables/useApi'

export function usePxExport() {
  const { apiFetch } = useApi()
  const loading = ref<boolean>(false)
  const error = ref<unknown>(null)
  const { success, error: errorToast } = usePixeToast()
  const { addLog } = useSessionLog()

  async function exportPxData(): Promise<object> {
    addLog('info', 'px_export_started')

    loading.value = true
    let data
    try {
      data = await apiFetch<object>('/api/pxexport/', {
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      })
      addLog('info', 'px_export_succeeded')
    } catch (err) {
      addLog('error', 'px_export_failed', {
        message: err instanceof Error ? err.message : String(err),
      })
      error.value = err
      errorToast(err)
    } finally {
      loading.value = false
    }

    return data!
  }

  async function importPxData(payload: object) {
    addLog('info', 'px_import_started')
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
      addLog('info', 'px_import_succeeded')
    } catch (err) {
      addLog('error', 'px_import_failed')
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
