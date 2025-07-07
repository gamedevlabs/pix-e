<template>
  <div>
    <h2>Filters</h2>
    <div class="filters bg-gray-800 p-4 rounded-lg shadow-md">
      <div class="filter-group mb-4">
        <label for="genre-select" class="text-green-400">🎨 Genre</label>
        <MultiSelectFilter
          :options="uniqueGenres"
          v-model="selectedGenre"
          placeholder="Select Genres"
          @update:model-value="applyFilters"
          class="neon-input"
        />
      </div>
      <div class="filter-group mb-4">
        <label for="sentiment-select" class="text-green-400">💬 Sentiment</label>
        <select
          id="sentiment-select"
          v-model="selectedSentiment"
          @change="applyFilters"
          class="w-full p-2 rounded-lg bg-gray-700 text-green-300 border border-green-500 hover:border-green-300 transition"
        >
          <option value="">All Sentiments</option>
          <option v-for="sentiment in uniqueSentiments" :key="sentiment" :value="sentiment">
            {{ sentiment }}
          </option>
        </select>
      </div>
    <div class="filter-group mb-4">
        <label for="game-select">Game Name:</label>
        <MultiSelectFilter
          :options="uniqueGames"
          v-model="selectedGame"
          placeholder="Select Games"
          @update:model-value="applyFilters"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  sentiments: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['filter-change'])

const selectedGenre = ref([])
const selectedSentiment = ref('')
const selectedGame = ref([])

const uniqueGenres = computed(() => {
  const genres = new Set()
  props.sentiments.forEach(item => {
    if (item.genres) {
      // Genres are stored as a string representation of a list, so we need to parse it
      try {
        const parsedGenres = JSON.parse(item.genres.replace(/'/g, '"'))
        parsedGenres.forEach(g => genres.add(g.trim()))
      } catch (e) {
        console.error("Error parsing genres:", e, item.genres)
      }
    }
  })
  return Array.from(genres).sort()
})

const uniqueSentiments = computed(() => {
  const sentiments = new Set()
  props.sentiments.forEach(item => {
    if (item.dominant_sentiment) {
      sentiments.add(item.dominant_sentiment.trim())
    }
  })
  return Array.from(sentiments).sort()
})

const uniqueGames = computed(() => {
  const games = new Set()
  props.sentiments.forEach(item => {
    if (item.name) {
      games.add(item.name.trim())
    }
  })
  return Array.from(games).sort()
})

const applyFilters = () => {
  emit('filter-change', {
    genre: selectedGenre.value,
    sentiment: selectedSentiment.value,
    game: selectedGame.value
  })
}

// Watch for changes in sentiments prop and reset filters if data changes significantly
watch(() => props.sentiments, () => {
  selectedGenre.value = []
  selectedSentiment.value = ''
  selectedGame.value = []
}, { deep: true })
</script>

<style scoped>
.filters {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.filter-group label {
  margin-right: 10px;
}

.filter-group select {
  padding: 8px;
  border-radius: 4px;
  border: 1px solid #ccc;
}
</style>