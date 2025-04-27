const API_URL = 'http://localhost:8000/pxcomponentdefinitions/'

export function usePxComponentDefinitions() {
  const px_component_definitions = ref<PxComponentDefinition[]>([])
  const loading = ref(false)
  const error = ref<unknown>(null)
  const toast = useToast()

  async function fetchPxComponentDefinitions() {
    loading.value = true
    try {
      const data = await $fetch<PxComponentDefinition[]>(API_URL)
      px_component_definitions.value = data || []
    } catch (err) {
      error.value = err
      toast.add({
        title: 'Error loading PxComponentDefinitions',
        //description: 'Your action was completed successfully.',
        color: 'error',
      })
    } finally {
      loading.value = false
    }
  }

  async function createPxComponentDefinition(payload: { name: string; type: PxValueType }) {
    try {
      await $fetch<PxComponentDefinition>(API_URL, {
        method: 'POST',
        body: payload,
      })
      toast.add({
        title: 'Definition created successfully!',
        color: 'success',
      })
      await fetchPxComponentDefinitions()
    } catch (err) {
      error.value = err
      toast.add({
        title: 'Error creating definition',
        color: 'error',
      })
    }
  }

  async function updatePxComponentDefinition(
    id: number,
    payload: { name: string; type: PxValueType },
  ) {
    try {
      await $fetch<PxComponentDefinition>(`${API_URL}${id}/`, {
        method: 'PUT',
        body: payload,
      })
      toast.add({
        title: 'PxComponentDefinition updated successfully!',
        color: 'success',
      })
      await fetchPxComponentDefinitions()
    } catch (err) {
      error.value = err
      toast.add({
        title: 'Error updating PxComponentDefinition',
        color: 'error',
      })
    }
  }

  async function deletePxComponentDefinition(id: number) {
    try {
      await $fetch<null>(`${API_URL}${id}/`, {
        method: 'DELETE',
      })
      toast.add({
        title: 'PxComponentDefinition deleted successfully!',
        color: 'success',
      })
      await fetchPxComponentDefinitions()
    } catch (err) {
      error.value = err
      toast.add({
        title: 'Error deleting definition',
        color: 'error',
      })
    }
  }

  return {
    px_component_definitions,
    loading,
    error,
    fetchPxComponentDefinitions,
    createPxComponentDefinition,
    updatePxComponentDefinition,
    deletePxComponentDefinition,
  }
}
