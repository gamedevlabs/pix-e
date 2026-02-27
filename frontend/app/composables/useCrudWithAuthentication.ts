import { useProjectDataProvider } from '~/studyMock'

function collectionKey(apiUrl: string): string {
  const clean = apiUrl.replace(/^api\//, '').replace(/\/$/, '')
  const parts = clean.split('/')
  if (parts.length >= 3) return parts.join(':')
  return parts[parts.length - 1] ?? clean
}

export function useCrudWithAuthentication<T>(apiUrl: string) {
  const items = ref<T[]>([])
  const loading = ref(false)
  const error = ref<unknown>(null)
  const { success, error: errorToast } = usePixeToast()

  const collection = collectionKey(apiUrl)

  async function fetchAll() {
    loading.value = true
    try {
      const provider = useProjectDataProvider()
      items.value = (await provider.getEntities(collection)) as T[]
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

  async function createItem(payload: Partial<T>) {
    try {
      const provider = useProjectDataProvider()
      const created = await provider.createEntity(collection, payload as Record<string, unknown>)
      items.value = [...items.value, created as T]
      success('Saved locally (mock mode)')
      return (created as any).id as string
    } catch (err) {
      error.value = err
      errorToast(err)
      return undefined
    }
  }

  async function updateItem(id: number | string, payload: Partial<T>) {
    try {
      const provider = useProjectDataProvider()
      const updated = await provider.updateEntity(collection, String(id), payload as Record<string, unknown>)
      if (updated) {
        const idx = (items.value as Array<{ id?: unknown }>).findIndex(
          (x) => String(x.id) === String(id),
        )
        if (idx !== -1) {
          items.value = [
            ...items.value.slice(0, idx),
            updated as T,
            ...items.value.slice(idx + 1),
          ]
        }
      }
      success('Saved locally (mock mode)')
    } catch (err) {
      error.value = err
      errorToast(err)
    }
  }

  async function deleteItem(id: number | string) {
    try {
      const provider = useProjectDataProvider()
      await provider.deleteEntity(collection, String(id))
      items.value = (items.value as Array<{ id?: unknown }>).filter(
        (x) => String(x.id) !== String(id),
      ) as T[]
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
