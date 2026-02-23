export function useCrudWithAuthentication<T>(_apiUrl: string) {
  const items = ref<T[]>([])
  const loading = ref(false)
  const error = ref<unknown>(null)
  const { success, error: errorToast } = usePixeToast()

  async function fetchAll() {
    loading.value = true
    try {
      items.value = []
    } catch (err) {
      error.value = err
      errorToast(err)
    } finally {
      loading.value = false
    }
  }

  async function fetchById(_id: number | string) {
    loading.value = true
    try {
      return null
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
