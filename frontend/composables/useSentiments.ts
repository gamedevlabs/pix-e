import { ref } from 'vue'

export const useSentiments = () => {
  const sentiments = ref([])
  const loading = ref(false)
  const error = ref(null)

  const fetchSentiments = async () => {
    loading.value = true
    try {
      const response = await fetch('http://localhost:8000/api/sentiments/')
      if (!response.ok) {
        throw new Error('Failed to fetch sentiments')
      }
      sentiments.value = await response.json()
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  return {
    sentiments,
    loading,
    error,
    fetchSentiments
  }
}
