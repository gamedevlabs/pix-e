<template>
  <div class="sentiment-page-container bg-background text-text min-h-screen p-8">
    <h1 class="text-4xl text-center mb-8 font-bold text-primary neon-text-glow">Game Sentiment Analysis Dashboard</h1>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
      <div class="lg:col-span-1">
        <SentimentFilters :sentiments="sentiments" @filter-change="handleFilterChange" />
      </div>
      <div class="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-6">
        <SentimentDistributionChart :data="filteredSentiments" />
        <DominantAspectChart :data="filteredSentiments" />
      </div>
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
  genre: [], // Array for multi-select
  sentiment: '', // String for single-select
  game: [] // Array for multi-select
})

const handleFilterChange = (newFilters) => {
  filters.value = newFilters
}

const filteredSentiments = computed(() => {
  console.log('filteredSentiments re-computing');
  console.log('Current filters:', filters.value);
  let filtered = sentiments.value || []

  // Genre filtering (multi-select)
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

  // Sentiment filtering (single-select)
  if (filters.value.sentiment) {
    filtered = filtered.filter(item => item.dominant_sentiment === filters.value.sentiment)
  }

  // Game Name filtering (multi-select)
  if (filters.value.game && filters.value.game.length > 0) {
    filtered = filtered.filter(item => filters.value.game.includes(item.name))
  }

  console.log('Filtered data count:', filtered.length);
  return filtered
})

onMounted(() => {
  fetchSentiments()
})
</script>