<template>
  <div class="filters-container bg-card-background p-6 rounded-lg shadow-lg border border-border">
    <h2 class="text-xl font-bold mb-4 text-primary">Filter Data</h2>

    <!-- Dataset Selector -->
    <div class="mb-4">
      <label class="block text-sm font-medium text-secondary mb-2">Dataset</label>
      <MultiSelectFilter
        :options="datasetOptions"
        v-model="selectedDatasetArray"
        placeholder="All Expectations"
      />
    </div>

    <!-- Genre Multi-Select -->
    <div class="mb-4">
      <label class="block text-sm font-medium text-secondary mb-2">Genre</label>
      <MultiSelectFilter
        :options="uniqueGenres"
        v-model="selectedGenre"
        placeholder="All Genres"
      />
    </div>

    <!-- Sentiment Single-Select -->
    <div class="mb-4">
      <label class="block text-sm font-medium text-secondary mb-2">Sentiment</label>
      <MultiSelectFilter
        :options="uniqueSentiments"
        v-model="selectedSentimentArray"
        placeholder="All Sentiments"
      />
    </div>

    <!-- Game Multi-Select -->
    <div>
      <label class="block text-sm font-medium text-secondary mb-2">Game Name</label>
      <MultiSelectFilter
        :options="uniqueGames"
        v-model="selectedGame"
        placeholder="All Games"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import MultiSelectFilter from './MultiSelectFilter.vue'

const props = defineProps({
  sentiments: Array,
  selectedDataset: String
})
const emit = defineEmits(['filter-change', 'dataset-change'])

// Dataset options
const datasetOptions = [
  'All Expectations',
  'Explicit Expectations',
  'Implicit Expectations',
  'Not Assigned'
]

// MultiSelectFilter returns array so wrap single dataset value
const selectedDatasetArray = ref([props.selectedDataset])
const selectedGenre = ref([])
const selectedSentimentArray = ref([])
const selectedGame = ref([])

// Emit dataset change when user selects new dataset
watch(selectedDatasetArray, (newVal) => {
  const datasetValue = newVal[0] || 'all'
  emit('dataset-change', datasetValue)
})

// Emit filter changes for genre, sentiment, game
const applyFilters = () => {
  emit('filter-change', {
    genre: selectedGenre.value,
    sentiment: selectedSentimentArray.value[0] || '', // single select
    game: selectedGame.value
  })
}

// Watch for filter changes
watch([selectedGenre, selectedSentimentArray, selectedGame], applyFilters, { deep: true })

// Unique filter options
const uniqueGenres = computed(() =>
  [...new Set(props.sentiments.flatMap(s =>
    JSON.parse(s.genres.replace(/'/g, '"'))
  ))].sort()
)
const uniqueSentiments = computed(() =>
  [...new Set(props.sentiments.map(s => s.dominant_sentiment).filter(Boolean))].sort()
)
const uniqueGames = computed(() =>
  [...new Set(props.sentiments.map(s => s.name).filter(Boolean))].sort()
)
</script>
