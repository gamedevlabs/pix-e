<template>
  <div class="filters-container bg-card-background p-6 rounded-lg shadow-lg border border-border">
    <h2 class="text-2xl font-bold mb-6 text-primary">Filter Data</h2>
    <div class="filters space-y-6">
      <div class="filter-group">
        <label for="genre-select" class="block text-lg font-medium mb-2 text-secondary">🎨 Genre</label>
        <MultiSelectFilter
          :options="uniqueGenres"
          v-model="selectedGenre"
          placeholder="Select Genres"
        />
      </div>

      <div class="filter-group">
        <label for="sentiment-select" class="block text-lg font-medium mb-2 text-secondary">💬 Sentiment</label>
        <select
          id="sentiment-select"
          v-model="selectedSentiment"
          @change="applyFilters"
          class="w-full p-3 rounded-md bg-input-background text-text border border-border focus:ring-2 focus:ring-primary focus:border-transparent transition-all duration-200 ease-in-out"
        >
          <option value="">All Sentiments</option>
          <option v-for="sentiment in uniqueSentiments" :key="sentiment" :value="sentiment">{{ sentiment }}</option>
        </select>
      </div>

      <div class="filter-group">
        <label for="game-select" class="block text-lg font-medium mb-2 text-secondary">🎮 Game Name</label>
        <MultiSelectFilter
          :options="uniqueGames"
          v-model="selectedGame"
          placeholder="Select Games"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import MultiSelectFilter from './MultiSelectFilter.vue' // Import the MultiSelectFilter

const props = defineProps({
  sentiments: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['filter-change'])

const selectedGenre = ref([]) // Changed to array
const selectedSentiment = ref('') // Remains string
const selectedGame = ref([]) // Changed to array

const uniqueGenres = computed(() => {
  const genres = new Set()
  props.sentiments.forEach(item => {
    if (item.genres) {
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
  const dataToFilter = props.sentiments.filter(item => {
    const matchesGenre = selectedGenre.value.length === 0 || (
      item.genres && JSON.parse(item.genres.replace(/'/g, '"')).some(g => selectedGenre.value.includes(g))
    )
    const matchesGame = selectedGame.value.length === 0 || selectedGame.value.includes(item.name)
    return matchesGenre && matchesGame
  })

  dataToFilter.forEach(item => {
    if (item.dominant_sentiment) {
      sentiments.add(item.dominant_sentiment.trim())
    }
  })
  return Array.from(sentiments).sort()
})

const uniqueGames = computed(() => {
  const games = new Set()
  const dataToFilter = props.sentiments.filter(item => {
    const matchesGenre = selectedGenre.value.length === 0 || (
      item.genres && JSON.parse(item.genres.replace(/'/g, '"')).some(g => selectedGenre.value.includes(g))
    )
    const matchesSentiment = selectedSentiment.value === '' || item.dominant_sentiment === selectedSentiment.value
    return matchesGenre && matchesSentiment
  })

  dataToFilter.forEach(item => {
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
watch([selectedGenre, selectedSentiment, selectedGame], () => {
  applyFilters()
}, { deep: true })

// 1️⃣ When Genre changes: Clear invalid Games and Sentiments
watch(selectedGenre, (newGenre, oldGenre) => {
  // Clear invalid Games
  if (selectedGame.value.length > 0) {
    const validGames = uniqueGames.value; // uniqueGames already reacts to selectedGenre
    const newSelectedGames = selectedGame.value.filter(game => validGames.includes(game));
    if (newSelectedGames.length !== selectedGame.value.length) {
      selectedGame.value = newSelectedGames;
    }
  }

  // Clear invalid Sentiment
  if (selectedSentiment.value !== '') {
    const validSentiments = uniqueSentiments.value; // uniqueSentiments already reacts to selectedGenre
    if (!validSentiments.includes(selectedSentiment.value)) {
      selectedSentiment.value = '';
    }
  }
}, { deep: true });

// 2️⃣ When Games change: Clear invalid Sentiments
watch(selectedGame, (newGame, oldGame) => {
  if (selectedSentiment.value !== '') {
    const validSentiments = uniqueSentiments.value; // uniqueSentiments already reacts to selectedGame
    if (!validSentiments.includes(selectedSentiment.value)) {
      selectedSentiment.value = '';
    }
  }
}, { deep: true });

// 3️⃣ When Sentiment changes: Clear invalid Games
watch(selectedSentiment, (newSentiment, oldSentiment) => {
  if (selectedGame.value.length > 0) {
    const validGames = uniqueGames.value; // uniqueGames already reacts to selectedSentiment
    const newSelectedGames = selectedGame.value.filter(game => validGames.includes(game));
    if (newSelectedGames.length !== selectedGame.value.length) {
      selectedGame.value = newSelectedGames;
    }
  }
});

// When Game changes → reset invalid Sentiment
watch(selectedGame, () => {
  const validSentiments = uniqueSentiments.value
  if (selectedSentiment.value && !validSentiments.includes(selectedSentiment.value)) {
    selectedSentiment.value = '' // Reset invalid sentiment
  }
}, { deep: true })

// When Sentiment changes → reset invalid Games
watch(selectedSentiment, () => {
  if (selectedGame.value.length > 0) {
    const validGames = uniqueGames.value
    const newSelectedGames = selectedGame.value.filter(game => validGames.includes(game))
    if (newSelectedGames.length !== selectedGame.value.length) {
      selectedGame.value = newSelectedGames // OR clear completely: []
    }
  }
})
</script>

<style scoped>
.filters {
  display: flex;
  flex-direction: column; /* Changed to column for better stacking */
  gap: 20px;
}

.filter-group label {
  margin-bottom: 8px; /* Added margin for spacing */
}

/* No specific styles for select as Tailwind classes are used directly */
</style>