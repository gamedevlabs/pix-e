<script setup lang="ts">
// Main data state
const allSentiments = ref([])
const loading = ref(false)
const error = ref(null)

// Filter states
const selectedDataset = ref('all')
const selectedGenres = ref([])
const selectedSentiment = ref('')
const selectedGames = ref([])

// Fetch data from API
const fetchSentiments = async () => {
  loading.value = true
  error.value = null
  try {
    const sentiments = await $fetch(
      `http://localhost:8000/api/sentiments/?type=${selectedDataset.value}`,
    )
    allSentiments.value = sentiments.data
  } catch (err) {
    console.error(err)
    error.value = 'Failed to load sentiment data.'
  } finally {
    loading.value = false
  }
}

// Initial data load
onMounted(fetchSentiments)

// Dynamic options for filters
const uniqueGenres = computed(() => {
  let data = allSentiments.value

  if (selectedSentiment.value) {
    data = data.filter((item) => item.dominant_sentiment === selectedSentiment.value)
  }
  if (selectedGames.value.length > 0) {
    data = data.filter((item) => selectedGames.value.includes(item.name))
  }

  return [...new Set(data.flatMap((item) => JSON.parse(item.genres.replace(/'/g, '"'))))].sort()
})

const uniqueSentiments = computed(() => {
  let data = allSentiments.value

  if (selectedGenres.value.length > 0) {
    data = data.filter((item) =>
      selectedGenres.value.some((g) => JSON.parse(item.genres.replace(/'/g, '"')).includes(g)),
    )
  }
  if (selectedGames.value.length > 0) {
    data = data.filter((item) => selectedGames.value.includes(item.name))
  }

  return [...new Set(data.map((item) => item.dominant_sentiment).filter(Boolean))].sort()
})

const uniqueGames = computed(() => {
  let data = allSentiments.value

  if (selectedGenres.value.length > 0) {
    data = data.filter((item) =>
      selectedGenres.value.some((g) => JSON.parse(item.genres.replace(/'/g, '"')).includes(g)),
    )
  }
  if (selectedSentiment.value) {
    data = data.filter((item) => item.dominant_sentiment === selectedSentiment.value)
  }

  return [...new Set(data.map((item) => item.name).filter(Boolean))].sort()
})

// Main filtered data for diagrams and tables
const filteredData = computed(() => {
  let data = allSentiments.value

  if (selectedGenres.value.length > 0) {
    data = data.filter((item) =>
      selectedGenres.value.some((g) => JSON.parse(item.genres.replace(/'/g, '"')).includes(g)),
    )
  }
  if (selectedSentiment.value) {
    data = data.filter((item) => item.dominant_sentiment === selectedSentiment.value)
  }
  if (selectedGames.value.length > 0) {
    data = data.filter((item) => selectedGames.value.includes(item.name))
  }

  return data
})

// Event handlers for filter changes
const onDatasetChange = (dataset) => {
  selectedDataset.value = dataset
  selectedGenres.value = []
  selectedSentiment.value = ''
  selectedGames.value = []
  fetchSentiments()
}

const onGenreChange = (genres) => {
  selectedGenres.value = genres
}

const onSentimentChange = (sentiment) => {
  selectedSentiment.value = sentiment
}

const onGameChange = (games) => {
  selectedGames.value = games
}
</script>

<template>
  <div class="sentiment-dashboard">
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <SentimentFilters
        :selected-dataset="selectedDataset"
        :unique-genres="uniqueGenres"
        :selected-genres="selectedGenres"
        :unique-sentiments="uniqueSentiments"
        :selected-sentiment="selectedSentiment"
        :unique-games="uniqueGames"
        :selected-games="selectedGames"
        @dataset-change="onDatasetChange"
        @genre-change="onGenreChange"
        @sentiment-change="onSentimentChange"
        @game-change="onGameChange"
      />
      <SentimentDistributionChart :key="selectedDataset" :data="filteredData" />
      <DominantAnalysis :data="filteredData" :loading="loading" />
    </div>
    <SentimentTable :key="selectedDataset" :data="filteredData" />
  </div>
</template>

<style scoped>
.sentiment-dashboard {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
</style>
