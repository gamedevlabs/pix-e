import { useProject } from '@/composables/useProject'
export function useCrudWithAuthentication<T>(apiUrl: string) {
  const config = useRuntimeConfig()
  const items = ref<T[]>([])
  const loading = ref(false)
  const error = ref<unknown>(null)
  const { success, error: errorToast } = usePixeToast()
  const API_URL = config.public.apiBase + '/' + apiUrl
  const projectStore = useProject()

  async function fetchAll() : Promise<T[]> {
    loading.value = true
    try {
      const data = await $fetch<T[]>(API_URL, {
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      })
      items.value = data || []
      return data
    } catch (err) {
      error.value = err
      errorToast(err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchById(id: number | string) {
    loading.value = true
    try {
      return await $fetch<T>(`${API_URL}${id}`, {
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      })
    } catch (err) {
      error.value = err
      errorToast(err)
      return null
    } finally {
      loading.value = false
    }
  }

  async function createItem(payload: Partial<T>) : Promise<T> {
    try {
      const data = await $fetch<T>(API_URL, {
        method: 'POST',
        body: payload,
        credentials: 'include',
        headers: {
          'X-CSRFToken': useCookie('csrftoken').value,
        } as HeadersInit,
      })
      success('Item created successfully!')
      await fetchAll()
      return data
    } catch (err) {
      error.value = err
      errorToast(err)
      throw err
    }
  }

  async function updateItem(id: number | string, payload: Partial<T>) {
    try {
      await $fetch<T>(`${API_URL}${id}/`, {
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
      await $fetch<null>(`${API_URL}${id}/`, {
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

  watch(
    () => projectStore.activeProjectId,
    async (nextId, previousId) => {
      if (previousId !== null && nextId !== previousId) {
        console.log("weird fetchAll going on")
        await fetchAll()
      }
    },
  )

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
