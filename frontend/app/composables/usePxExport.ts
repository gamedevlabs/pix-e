import { useProjectDataProvider } from '~/studyMock'

export function usePxExport() {
  const loading = ref<boolean>(false)
  const error = ref<unknown>(null)
  const { success, error: errorToast } = usePixeToast()

  async function exportPxData(): Promise<object> {
    const provider = useProjectDataProvider()
    loading.value = true
    try {
      const json = await provider.exportState()
      return JSON.parse(json)
    } catch (err) {
      error.value = err
      errorToast(err)
      return {}
    } finally {
      loading.value = false
    }
  }

  async function importPxData(payload: object) {
    const provider = useProjectDataProvider()
    try {
      await provider.importState(JSON.stringify(payload))
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
