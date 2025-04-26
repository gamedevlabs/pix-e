import { ref } from 'vue'
import type { PxNode } from "~/types/px";

const API_URL = 'http://localhost:8000/pxnodes/'

export function usePxNodes() {
  const pxnodes = ref<PxNode[]>([])
  const loading = ref(false)
  const error = ref<unknown>(null)

  async function fetchPxNodes() {
    loading.value = true
    try {
      const { data } = await useFetch(API_URL)
      pxnodes.value = data.value || []
    } catch (err) {
      error.value = err
    } finally {
      loading.value = false
    }
  }

  async function createPxNode(payload: { name: string; description: string }) {
    await $fetch<PxNode>(API_URL, {
      method: 'POST',
      body: payload,
    })
    await fetchPxNodes()
  }

  async function updatePxNode(id: number, payload: { name: string; description: string }) {
    await $fetch<PxNode>(`${API_URL}${id}/`, {
      method: 'PUT',
      body: payload,
    })
    await fetchPxNodes()
  }

  async function deletePxNode(id: number) {
    await $fetch<null>(`${API_URL}${id}/`, {
      method: 'DELETE',
    })
    await fetchPxNodes()
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
