<script setup lang="ts">
import { ref, watch } from 'vue'
import MultiSelectFilter from './MultiSelectFilter.vue'

const props = defineProps<{
  selectedDataset: string
  uniqueGenres: []
  selectedGenres: []
  uniqueSentiments: []
  selectedSentiment: string
  uniqueGames: []
  selectedGames: []
}>()

const emit = defineEmits(['dataset-change', 'genre-change', 'sentiment-change', 'game-change'])

const datasetOptions = [
  'All Expectations',
  'Explicit Expectations',
  'Implicit Expectations',
  'Not Assigned',
]

type DatasetKey = keyof typeof datasetMapping

const datasetMapping = {
  'All Expectations': 'all',
  'Explicit Expectations': 'explicit',
  'Implicit Expectations': 'implicit',
  'Not Assigned': 'not_assigned',
}

// Create a reverse mapping to find the label from the prop value
const reverseDatasetMapping = Object.fromEntries(
  Object.entries(datasetMapping).map(([key, value]) => [value, key]),
)

// Initialize with the correct label
const initialLabel = reverseDatasetMapping[props.selectedDataset] || 'All Expectations'
const selectedDatasetArray = ref([initialLabel])

const selectedGenre = ref(props.selectedGenres)
const selectedSentimentArray = ref(props.selectedSentiment ? [props.selectedSentiment] : [])
const selectedGame = ref(props.selectedGames)

// Watchers to emit changes
watch(selectedDatasetArray, (newVal) => {
  const selectedValue = (newVal[0] || 'All Expectations') as DatasetKey
  const datasetValue = datasetMapping[selectedValue] || 'all'
  emit('dataset-change', datasetValue)
})

watch(selectedGenre, (newVal) => {
  emit('genre-change', newVal)
})

watch(selectedSentimentArray, (newVal) => {
  emit('sentiment-change', newVal[0] || '')
})

watch(selectedGame, (newVal) => {
  emit('game-change', newVal)
})
</script>

<template>
  <div class="filters-container bg-card-background p-6 rounded-lg shadow-lg border border-border">
    <h2 class="text-xl font-bold mb-4 text-primary">Filter Data</h2>

    <!-- Dataset Selector -->
    <div class="mb-4">
      <label class="block text-sm font-medium text-secondary mb-2">Dataset</label>
      <MultiSelectFilter
        v-model="selectedDatasetArray"
        :options="datasetOptions"
        placeholder="All Expectations"
        :single-select="true"
      />
    </div>

    <!-- Genre Multi-Select -->
    <div class="mb-4">
      <label class="block text-sm font-medium text-secondary mb-2">Genre</label>
      <MultiSelectFilter v-model="selectedGenre" :options="uniqueGenres" placeholder="All Genres" />
    </div>

    <!-- Sentiment Single-Select -->
    <div class="mb-4">
      <label class="block text-sm font-medium text-secondary mb-2">Sentiment</label>
      <MultiSelectFilter
        v-model="selectedSentimentArray"
        :options="uniqueSentiments"
        placeholder="All Sentiments"
      />
    </div>

    <!-- Game Multi-Select -->
    <div>
      <label class="block text-sm font-medium text-secondary mb-2">Game Name</label>
      <MultiSelectFilter v-model="selectedGame" :options="uniqueGames" placeholder="All Games" />
    </div>
  </div>
</template>
