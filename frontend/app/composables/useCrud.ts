import { useOfflineFetch } from '~/studyMock'

export function useCrud<T>(apiUrl: string) {
  const items = ref<T[]>([])
  const loading = ref(false)
  const error = ref<unknown>(null)
  const { success, error: errorToast } = usePixeToast()

  async function fetchAll() {
    loading.value = true
    try {
      // mock-only: best-effort mapping of endpoints to offline keys
      if (apiUrl === 'llm/pillars/') {
        const offline = await useOfflineFetch<{ pillars: T[] }>('pillars')
        items.value = (offline as { pillars: T[] }).pillars || []
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
      return null
    } finally {
      loading.value = false
    }
  }

  async function createItem(_payload: Partial<T>) {
    try {
      success('Saved locally (mock mode)')
      return null
    } catch (err) {
      error.value = err
      errorToast(err)
      return null
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
