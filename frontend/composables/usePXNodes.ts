const API_URL = 'http://localhost:8000/pxnodes/'

export function usePxNodes() {
  const pxnodes = ref<PxNode[]>([])
  const loading = ref(false)
  const error = ref<unknown>(null)
  const toast = useToast()

  async function fetchPxNodes() {
    loading.value = true
    try {
      const data = await $fetch<PxNode[]>(API_URL)
      pxnodes.value = data || []
    } catch (err) {
      error.value = err
      toast.add({
        title: 'Error loading PxNodes',
        //description: 'Your action was completed successfully.',
        color: 'error',
      })
    } finally {
      loading.value = false
    }
  }

  async function createPxNode(payload: { name: string; description: string }) {
    try {
      await $fetch<PxNode>(API_URL, {
        method: 'POST',
        body: payload,
      })
      toast.add({
        title: 'Node created successfully!',
        color: 'success',
      })
      await fetchPxNodes()
    }
    catch (err) {
      error.value = err
      toast.add({
        title: 'Error creating node',
        color: 'error',
      })
    }
  }

  async function updatePxNode(id: number, payload: { name: string; description: string }) {
    try {
      await $fetch<PxNode>(`${API_URL}${id}/`, {
        method: 'PUT',
        body: payload,
      })
      toast.add({
        title: 'Node updated successfully!',
        color: 'success',
      })
      await fetchPxNodes()
    }
    catch (err) {
      error.value = err
      toast.add({
        title: 'Error updating node',
        color: 'error',
      })
    }
  }

  async function deletePxNode(id: number) {
    try {
      await $fetch<null>(`${API_URL}${id}/`, {
        method: 'DELETE',
      })
      toast.add({
        title: 'Node deleted successfully!',
        color: 'success',
      })
      await fetchPxNodes()
    }
    catch (err) {
      error.value = err
      toast.add({
        title: 'Error deleting node',
        color: 'error',
      })
    }
  }

  return {
    pxnodes,
    loading,
    error,
    fetchPxNodes,
    createPxNode,
    updatePxNode,
    deletePxNode,
  }
}
