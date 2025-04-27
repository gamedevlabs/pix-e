const BASE_URL = 'http://localhost:8000/'

export function useCrud<T>(apiUrl: string) {
  const items = ref<T[]>([])
  const loading = ref(false)
  const error = ref<unknown>(null)
  const toast = useToast()
  const API_URL = BASE_URL + apiUrl

  async function fetchAll() {
    loading.value = true
    try {
      const data = await $fetch<T[]>(API_URL)
      items.value = data || []
    } catch (err) {
      error.value = err
      toast.add({
        title: 'Error loading items...',
        //description: 'Your action was completed successfully.',
        color: 'error',
      })
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
      toast.add({
        title: 'Item created successfully!',
        color: 'success',
      })
      await fetchAll()
    } catch (err) {
      error.value = err
      toast.add({
        title: 'Error creating item',
        color: 'error',
      })
    }
  }

  async function updateItem(
    id: number | string,
    payload: Partial<T>,
  ) {
    try {
      await $fetch<T>(`${API_URL}${id}/`, {
        method: 'PUT',
        body: payload,
      })
      toast.add({
        title: 'Item updated successfully!',
        color: 'success',
      })
      await fetchAll()
    } catch (err) {
      error.value = err
      toast.add({
        title: 'Error updating item',
        color: 'error',
      })
    }
  }

  async function deleteItem(id: number | string) {
    try {
      await $fetch<null>(`${API_URL}${id}/`, {
        method: 'DELETE',
      })
      toast.add({
        title: 'Item deleted successfully!',
        color: 'success',
      })
      await fetchAll()
    } catch (err) {
      error.value = err
      toast.add({
        title: 'Error deleting item',
        color: 'error',
      })
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
