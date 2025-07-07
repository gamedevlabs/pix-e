<template>
  <div class="sentiment-table-container bg-card-background p-6 rounded-lg shadow-lg border border-border">
    <h2 v-if="!loading && !error" class="text-2xl font-bold mb-4 text-primary">Sentiment Data</h2>
    <p v-if="loading" class="text-yellow-400 animate-pulse">Loading sentiment data...</p>
    <p v-if="error" class="text-red-500 font-bold">⚠️ Error: {{ error }}</p>

    <div v-if="!loading && !error && sortedData.length > 0" class="table-wrapper overflow-x-auto">
      <table class="min-w-full bg-card-background rounded-lg text-text">
        <thead>
          <tr>
            <th @click="sortBy('name')" class="px-4 py-3 text-left text-sm font-medium text-secondary uppercase tracking-wider cursor-pointer hover:bg-hover-background transition-colors duration-200 rounded-tl-lg">
              Game Name <span v-if="sortColumn === 'name'">{{ sortDirection === 'asc' ? '▲' : '▼' }}</span>
            </th>
            <th @click="sortBy('genres')" class="px-4 py-3 text-left text-sm font-medium text-secondary uppercase tracking-wider cursor-pointer hover:bg-hover-background transition-colors duration-200">
              Genres <span v-if="sortColumn === 'genres'">{{ sortDirection === 'asc' ? '▲' : '▼' }}</span>
            </th>
            <th @click="sortBy('review_text')" class="px-4 py-3 text-left text-sm font-medium text-secondary uppercase tracking-wider cursor-pointer hover:bg-hover-background transition-colors duration-200">
              Review Text <span v-if="sortColumn === 'review_text'">{{ sortDirection === 'asc' ? '▲' : '▼' }}</span>
            </th>
            <th @click="sortBy('explicit_expectations')" class="px-4 py-3 text-left text-sm font-medium text-secondary uppercase tracking-wider cursor-pointer hover:bg-hover-background transition-colors duration-200">
              Explicit Expectations <span v-if="sortColumn === 'explicit_expectations'">{{ sortDirection === 'asc' ? '▲' : '▼' }}</span>
            </th>
            <th @click="sortBy('dominant_aspect')" class="px-4 py-3 text-left text-sm font-medium text-secondary uppercase tracking-wider cursor-pointer hover:bg-hover-background transition-colors duration-200">
              Dominant Aspect <span v-if="sortColumn === 'dominant_aspect'">{{ sortDirection === 'asc' ? '▲' : '▼' }}</span>
            </th>
            <th @click="sortBy('dominant_sentiment')" class="px-4 py-3 text-left text-sm font-medium text-secondary uppercase tracking-wider cursor-pointer hover:bg-hover-background transition-colors duration-200 rounded-tr-lg">
              Dominant Sentiment <span v-if="sortColumn === 'dominant_sentiment'">{{ sortDirection === 'asc' ? '▲' : '▼' }}</span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, index) in paginatedData" :key="index" class="border-t border-border hover:bg-hover-background transition-colors duration-200">
            <td class="px-4 py-3">{{ item.name }}</td>
            <td class="px-4 py-3">{{ item.genres }}</td>
            <td class="px-4 py-3 truncate max-w-xs">{{ item.review_text }}</td>
            <td class="px-4 py-3">{{ item.explicit_expectations }}</td>
            <td class="px-4 py-3">{{ item.dominant_aspect }}</td>
            <td
              class="px-4 py-3 font-bold"
              :class="{
                'text-green-400': item.dominant_sentiment === 'positive',
                'text-red-400': item.dominant_sentiment === 'negative',
                'text-yellow-400': item.dominant_sentiment === 'neutral'
              }"
            >
              {{ item.dominant_sentiment }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="pagination-controls flex justify-center items-center mt-6 space-x-4" v-if="!loading && !error && sortedData.length > 0">
      <button @click="prevPage" :disabled="currentPage === 1" class="bg-primary text-white px-4 py-2 rounded-md hover:bg-primary-dark disabled:bg-gray-700 disabled:text-gray-400 transition-colors duration-200">
        Previous
      </button>
      <span class="text-text font-medium">Page {{ currentPage }} of {{ totalPages }}</span>
      <button @click="nextPage" :disabled="currentPage === totalPages" class="bg-primary text-white px-4 py-2 rounded-md hover:bg-primary-dark disabled:bg-gray-700 disabled:text-gray-400 transition-colors duration-200">
        Next
      </button>
    </div>
    <p v-if="!loading && !error && data.length === 0" class="text-gray-400 text-center mt-4">No data available.</p>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: null
  }
})

const sortColumn = ref(null)
const sortDirection = ref('asc')

const currentPage = ref(1)
const itemsPerPage = ref(10)

const sortedData = computed(() => {
  if (!sortColumn.value) {
    return props.data
  }

  return [...props.data].sort((a, b) => {
    const aValue = a[sortColumn.value]
    const bValue = b[sortColumn.value]

    if (aValue === null || aValue === undefined) return sortDirection.value === 'asc' ? 1 : -1;
    if (bValue === null || bValue === undefined) return sortDirection.value === 'asc' ? -1 : 1;

    if (typeof aValue === 'string' && typeof bValue === 'string') {
      return sortDirection.value === 'asc'
        ? aValue.localeCompare(bValue)
        : bValue.localeCompare(aValue)
    } else {
      return sortDirection.value === 'asc'
        ? aValue - bValue
        : bValue - aValue
    }
  })
})

const totalPages = computed(() => {
  return Math.ceil(sortedData.value.length / itemsPerPage.value)
})

const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage.value
  const end = start + itemsPerPage.value
  return sortedData.value.slice(start, end)
})

const sortBy = (column) => {
  if (sortColumn.value === column) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortColumn.value = column
    sortDirection.value = 'asc'
  }
  currentPage.value = 1 // Reset to first page on sort change
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
  }
}

const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
  }
}

// Reset current page if data or filters change
watch(() => props.data, () => {
  currentPage.value = 1
})

</script>

<style scoped>
/* No scoped styles needed here as Tailwind classes are used directly */
</style>
