import { useApi } from '~/composables/useApi'

export function useDataTransfer() {
  const { apiFetch } = useApi()
  const loading = ref<boolean>(false)
  const error = ref<unknown>(null)
  const { success, error: errorToast } = usePixeToast()
  const { addLog } = useSessionLog()

  async function exportProject(projectId: string): Promise<object | undefined> {
    addLog('info', 'project_export_started')

    loading.value = true

    try {
      const data = await apiFetch<object>(`/api/projects/${projectId}/export/`, {
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      })
      addLog('info', 'project_export_succeeded')
      return data
    } catch (err) {
      addLog('error', 'project_export_failed', {
        message: err instanceof Error ? err.message : String(err),
      })
      error.value = err
      errorToast(err)
    } finally {
      loading.value = false
    }
  }

  async function importProject(payload: object) {
    addLog('info', 'project_import_started')
    try {
      await apiFetch<object>('/api/projects/import/', {
        method: 'POST',
        body: payload,
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      })
      success('JSON imported successfully!')
      addLog('info', 'project_import_succeeded')
    } catch (err) {
      addLog('error', 'project_import_failed')
      error.value = err
      errorToast(err)
    }
  }

  async function overwriteProject(projectId: string, payload: object) {
    addLog('info', 'project_overwrite_started')
    try {
      await apiFetch<object>(`/api/projects/${projectId}/overwrite/`, {
        method: 'POST',
        body: payload,
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      })
      success('Project updated successfully!')
      addLog('info', 'project_overwrite_succeeded')
    } catch (err) {
      addLog('error', 'project_overwrite_failed')
      error.value = err
      errorToast(err)
      throw err
    }
  }

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
    exportProject,
    importProject,
    overwriteProject,
  }
}

// Filesystem-safe "<name>-<timestamp>.json" for exported projects.
export function exportFileName(projectName: string): string {
  const safe = (projectName || 'project')
    .replace(/[^a-z0-9-_]+/gi, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 60)
  const stamp = new Date().toISOString().replace(/[:.]/g, '-')
  return `${safe || 'project'}-${stamp}.json`
}
