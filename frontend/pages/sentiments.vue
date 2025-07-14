<template>
  <div class="sentiment-dashboard">
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <SentimentFilters
        :sentiments="allSentiments"
        :selected-dataset="selectedDataset"
        @dataset-change="onDatasetChange"
        @filter-change="updateFilters"
      />
      <SentimentChart :data="filteredData" />
    </div>
    <SentimentTable :data="filteredData" />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import axios from 'axios'
import SentimentFilters from '@/components/SentimentFilters.vue'
import SentimentChart from '@/components/SentimentDistributionChart.vue'
import SentimentTable from '@/components/SentimentTable.vue'

const allSentiments = ref([])
const filters = ref({
  genre: [],
  sentiment: '',
  game: []
})
const selectedDataset = ref('all')
const loading = ref(false)
const error = ref(null)

const fetchSentiments = async () => {
  loading.value = true
  error.value = null
  try {
    const response = await axios.get(`http://localhost:8000/api/sentiments/?type=${selectedDataset.value}`)
    allSentiments.value = response.data
  } catch (err) {
    console.error(err)
    error.value = 'Failed to load sentiment data.'
  } finally {
    loading.value = false
  }
}

onMounted(fetchSentiments)

const onDatasetChange = (dataset) => {
  selectedDataset.value = dataset
  fetchSentiments()
}

const updateFilters = (newFilters) => {
  filters.value = newFilters
}

const filteredData = computed(() => {
  return allSentiments.value.filter(item => {
    const matchesGenre = filters.value.genre.length === 0 || (
      item.genres && JSON.parse(item.genres.replace(/'/g, '"')).some(g => filters.value.genre.includes(g))
    )
    const matchesSentiment = !filters.value.sentiment || item.dominant_sentiment === filters.value.sentiment
    const matchesGame = filters.value.game.length === 0 || filters.value.game.includes(item.name)
    return matchesGenre && matchesSentiment && matchesGame
  })
})
</script>

<style scoped>
.sentiment-dashboard {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
</style>
