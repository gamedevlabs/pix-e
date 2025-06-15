const BASE_URL = 'http://localhost:8000/'

export function useCrud<T>(apiUrl: string) {
  const items = ref<T[]>([])
  const loading = ref(false)
  const error = ref<unknown>(null)
  const { success, error: errorToast } = usePixeToast()
  const API_URL = BASE_URL + apiUrl

  async function fetchAll() {
    loading.value = true
    try {
      const data = await $fetch<T[]>(API_URL)
      items.value = data || []
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
      return await $fetch<T>(`${API_URL}${id}`)
    } catch (err) {
      error.value = err
      return null
    } finally {
      loading.value = false
    }
  }

  async function createItem(payload: Partial<T>) {
    try {
      await $fetch<T>(API_URL, {
        method: 'POST',
        body: payload,
      })
      success('Item created successfully!')
      await fetchAll()
    } catch (err) {
      error.value = err
      errorToast(err)
    }
  }

  async function updateItem(id: number | string, payload: Partial<T>) {
    try {
      await $fetch<T>(`${API_URL}${id}/`, {
        method: 'PUT',
        body: payload,
      })
      success('Item updated successfully!')
      await fetchAll()
    } catch (err) {
      error.value = err
      errorToast(err)
    }
  }

  async function deleteItem(id: number | string) {
    try {
      await $fetch<null>(`${API_URL}${id}/`, {
        method: 'DELETE',
      })
      success('Item deleted successfully!')
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
