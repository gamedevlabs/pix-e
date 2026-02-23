import { useOfflineFetch } from '~/studyMock'

export function useCrudForPxWithAuthentication<T>(apiUrl: string) {
  const items = ref<T[]>([])
  const loading = ref(false)
  const error = ref<unknown>(null)
  const { success, error: errorToast } = usePixeToast()

  async function fetchAll() {
    loading.value = true
    try {
      if (apiUrl === 'api/pxcharts/') {
        const offline = await useOfflineFetch<{ charts: T[] }>('pxcharts')
        items.value = (offline as { charts: T[] }).charts || []
      } else {
        items.value = []
      }
    } catch (err) {
      error.value = err
      errorToast(err)
    } finally {
      loading.value = false
    }
  }

  async function fetchById(id: number | string) {
    loading.value = true
    try {
      return (
        (items.value as Array<{ id?: unknown }>).find?.((x) => String(x.id) === String(id)) ?? null
      )
    } catch (err) {
      error.value = err
      errorToast(err)
      return null
    } finally {
      loading.value = false
    }
  }

  async function createItem(_payload: Partial<T>) {
    try {
      success('Saved locally (mock mode)')
      await fetchAll()
      return undefined
    } catch (err) {
      error.value = err
      errorToast(err)
    }
  }

  async function updateItem(_id: number | string, _payload: Partial<T>) {
    try {
      success('Saved locally (mock mode)')
    } catch (err) {
      error.value = err
      errorToast(err)
    }
  }

  async function deleteItem(_id: number | string) {
    try {
      success('Deleted locally (mock mode)')
      await fetchAll()
    } catch (err) {
      error.value = err
      errorToast(err)
    }
  }

  return {
    items,
    loading,
    error,
    fetchAll,
    fetchById,
    createItem,
    updateItem,
    deleteItem,
  }
}
