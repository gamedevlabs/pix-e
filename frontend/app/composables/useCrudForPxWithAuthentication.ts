import { useProjectDataProvider } from '~/studyMock'

type EntityLike = Record<string, unknown> & { id?: unknown }

function asEntityLike(x: unknown): EntityLike {
  return (x ?? {}) as EntityLike
}

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
      const list = (await provider.getEntities(collection)) as unknown[]

      if (isPxNodesRoot()) {
        // Hydrate each node with its components
        const allComponents = (await provider.getEntities('pxcomponents')) as unknown[]
        items.value = list.map((nodeU) => {
          const node = asEntityLike(nodeU)
          return {
            ...node,
            components: allComponents
              .map(asEntityLike)
              .filter((c) => String(c.node) === String(node.id)),
            charts: [],
          }
        }) as T[]
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
        const charts = (await provider.getEntities(collection)) as unknown[]
        const chart = charts.map(asEntityLike).find((x) => String(x.id) === String(id))
        if (!chart) return null

        const containersKey = `pxcharts:${id}:pxcontainers`
        const edgesKey = `pxcharts:${id}:pxedges`
        const containers = await provider.getEntities(containersKey)
        const edges = await provider.getEntities(edgesKey)

        return { ...chart, containers, edges } as T
      }

      if (isPxNodesRoot()) {
        // Hydrate node with its components
        const nodes = (await provider.getEntities(collection)) as unknown[]
        const node = nodes.map(asEntityLike).find((x) => String(x.id) === String(id))
        if (!node) return null
        const allComponents = (await provider.getEntities('pxcomponents')) as unknown[]
        return {
          ...node,
          components: allComponents.map(asEntityLike).filter((c) => String(c.node) === String(id)),
          charts: [],
        } as T
      }

      // In mock/study mode we can't rely on this composable's `items` being populated
      // (e.g. a component card may fetch a definition by id before the definitions
      // list has been loaded). Always fall back to the provider store.
      const list = (await provider.getEntities(collection)) as unknown[]
      const found = list.map(asEntityLike).find((x) => String(x.id) === String(id))
      if (found) return found as T

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
      const created = asEntityLike(
        await provider.createEntity(collection, payload as Record<string, unknown>),
      )

      if (isPxNodesRoot()) {
        // Add with empty components/charts arrays
        items.value = [...items.value, { ...created, components: [], charts: [] } as T]
      } else {
        items.value = [...items.value, created as T]
      }

      success('Saved locally (mock mode)')
      return (created.id ?? '') as string
    } catch (err) {
      error.value = err
      errorToast(err)
      return undefined
    }
  }

  async function updateItem(id: number | string, payload: Partial<T>) {
    try {
      const provider = useProjectDataProvider()
      const updatedU = await provider.updateEntity(
        collection,
        String(id),
        payload as Record<string, unknown>,
      )
      const updated = updatedU ? asEntityLike(updatedU) : null
      if (updated) {
        const idx = (items.value as Array<{ id?: unknown }>).findIndex(
          (x) => String(x.id) === String(id),
        )
        if (idx !== -1) {
          // Preserve hydrated fields (components, charts, containers, edges) from existing item
          const existing = asEntityLike(items.value[idx])
          items.value = [
            ...items.value.slice(0, idx),
            {
              ...existing,
              ...updated,
              components: (existing as Record<string, unknown>).components ?? [],
              charts: (existing as Record<string, unknown>).charts ?? [],
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
