import { useProjectDataProvider } from '~/studyMock'

// Map an apiUrl to a stable collection key used in the entities store.
function collectionKey(apiUrl: string): string {
  const clean = apiUrl.replace(/^api\//, '').replace(/\/$/, '')
  const parts = clean.split('/')
  if (parts.length >= 3) return parts.join(':')
  return parts[parts.length - 1] ?? clean
}

export function useCrudForPxWithAuthentication<T>(apiUrl: string) {
  const items = ref<T[]>([])
  const loading = ref(false)
  const error = ref<unknown>(null)
  const { success, error: errorToast } = usePixeToast()

  const collection = collectionKey(apiUrl)

  // Returns true when this is the top-level pxcharts collection
  function isPxChartsRoot() {
    return collection === 'pxcharts'
  }

  function isPxNodesRoot() {
    return collection === 'pxnodes'
  }

  async function fetchAll() {
    loading.value = true
    try {
      const provider = useProjectDataProvider()
      const list = await provider.getEntities(collection)

      if (isPxNodesRoot()) {
        // Hydrate each node with its components
        const allComponents = await provider.getEntities('pxcomponents')
        items.value = list.map((node: any) => ({
          ...node,
          components: allComponents.filter((c: any) => String(c.node) === String(node.id)),
          charts: [],
        })) as T[]
        return
      }

      items.value = list as T[]
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
      const provider = useProjectDataProvider()

      if (isPxChartsRoot()) {
        // Hydrate chart with its containers and edges
        const charts = await provider.getEntities(collection)
        const chart = charts.find((x: any) => String(x.id) === String(id)) as any
        if (!chart) return null

        const containersKey = `pxcharts:${id}:pxcontainers`
        const edgesKey = `pxcharts:${id}:pxedges`
        const containers = await provider.getEntities(containersKey)
        const edges = await provider.getEntities(edgesKey)

        return { ...chart, containers, edges } as T
      }

      if (isPxNodesRoot()) {
        // Hydrate node with its components
        const nodes = await provider.getEntities(collection)
        const node = nodes.find((x: any) => String(x.id) === String(id)) as any
        if (!node) return null
        const allComponents = await provider.getEntities('pxcomponents')
        return {
          ...node,
          components: allComponents.filter((c: any) => String(c.node) === String(id)),
          charts: [],
        } as T
      }

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

      if (isPxNodesRoot()) {
        // Add with empty components/charts arrays
        items.value = [...items.value, { ...created, components: [], charts: [] } as T]
      } else {
        items.value = [...items.value, created as T]
      }

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
          // Preserve hydrated fields (components, charts, containers, edges) from existing item
          const existing = items.value[idx] as any
          items.value = [
            ...items.value.slice(0, idx),
            {
              ...existing,
              ...updated,
              components: existing.components ?? [],
              charts: existing.charts ?? [],
            } as T,
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
