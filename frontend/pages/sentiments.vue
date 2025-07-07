<template>
  <div class="sentiment-page-container p-6">
    <h1 class="text-4xl text-center mb-8 font-bold text-primary">Game Sentiment Analysis</h1>

    <SentimentFilters :sentiments="sentiments" @filter-change="handleFilterChange" />

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
      <SentimentDistributionChart :data="filteredSentiments" />
      <DominantAspectChart :data="filteredSentiments" />
    </div>

    <SentimentTable :data="filteredSentiments" :loading="loading" :error="error" />
  </div>
</template>


<script setup>
import { ref, onMounted, computed } from 'vue'
import { useSentiments } from '~/composables/useSentiments'
import SentimentFilters from '~/components/SentimentFilters.vue'
import SentimentTable from '~/components/SentimentTable.vue'
import SentimentDistributionChart from '~/components/SentimentDistributionChart.vue'
import DominantAspectChart from '~/components/DominantAspectChart.vue'

const { sentiments, loading, error, fetchSentiments } = useSentiments()

const filters = ref({
  genre: [],
  sentiment: '',
  game: []
})

const handleFilterChange = (newFilters) => {
  filters.value = newFilters
}

const filteredSentiments = computed(() => {
  let filtered = sentiments.value || []

  if (filters.value.genre && filters.value.genre.length > 0) {
    const selectedGenres = filters.value.genre;
    filtered = filtered.filter(item => {
      try {
        const parsedGenres = JSON.parse(item.genres.replace(/'/g, '"'))
        return selectedGenres.every(selectedG => parsedGenres.includes(selectedG))
      } catch (e) {
        console.error("Error parsing genres for filtering:", e, item.genres)
        return false
      }
    })
  }

  if (filters.value.sentiment) {
    filtered = filtered.filter(item => item.dominant_sentiment === filters.value.sentiment)
  }

  if (filters.value.game && filters.value.game.length > 0) {
    filtered = filtered.filter(item => filters.value.game.includes(item.name))
  }

  return filtered
})

onMounted(() => {
  fetchSentiments()
})
</script>