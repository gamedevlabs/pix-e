import { ref } from 'vue'

export const useSentiments = () => {
  const sentiments = ref([])
  const loading = ref(false)
  const error = ref(null)

  const fetchSentiments = async (type = 'all') => {
    loading.value = true
    error.value = null
    try {
      const config = useRuntimeConfig()
      const response = await fetch(`${config.public.apiBase}/api/sentiments/?type=${type}`)
      if (!response.ok) {
        throw new Error('Failed to fetch sentiments: ' + response.statusText);
      }
      const rawResponseText = await response.text(); // Read as text first
      console.log("Raw API Response:", rawResponseText.substring(0, 500) + '...'); // Log first 500 chars
      sentiments.value = JSON.parse(rawResponseText); // Manually parse
      console.log("Parsed Sentiments:", sentiments.value);
    } catch (e: any) {
      console.error("Error in fetchSentiments:", e); // Log the full error object
      error.value = e.message || 'An unknown error occurred during data fetch.'; // Ensure it's a string
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
