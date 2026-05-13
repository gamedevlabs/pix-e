import { useApi } from '~/composables/useApi'

export function useCrud<T>(apiUrl: string) {
  const { apiFetch } = useApi()
  const items = ref<T[]>([])
  const loading = ref(false)
  const error = ref<unknown>(null)
  const { success, error: errorToast } = usePixeToast()

  async function fetchAll() {
    loading.value = true
    try {
      const data = await apiFetch<T[]>(apiUrl, {
        credentials: 'include',
        headers: useRequestHeaders(['cookie']),
      })
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
      return await apiFetch<T>(`${apiUrl}${id}`)
    } catch (err) {
      error.value = err
      return null
    } finally {
      loading.value = false
    }
  }

  async function createItem(payload: Partial<T>) {
    try {
      const result = await apiFetch<T>(apiUrl, {
        method: 'POST',
        body: payload,
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      })
      success('Item created successfully!')
      await fetchAll()
      return result
    } catch (err) {
      error.value = err
      errorToast(err)
      return null
    }
  }

  async function updateItem(id: number | string, payload: Partial<T>) {
    try {
      await apiFetch<T>(`${apiUrl}${id}/`, {
        method: 'PATCH',
        body: payload,
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
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
      await apiFetch<null>(`${apiUrl}${id}/`, {
        method: 'DELETE',
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
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
