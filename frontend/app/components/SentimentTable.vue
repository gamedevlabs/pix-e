<script setup lang="ts">
import { ref, computed, watch } from 'vue'

const props = defineProps({
  data: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const headers = [
  { label: 'Game Name', key: 'name' },
  { label: 'Genres', key: 'genres' },
  { label: 'Review Text', key: 'review_text' },
  { label: 'Expectations', key: 'expectations' },
  { label: 'Dominant Aspect', key: 'dominant_aspect' },
  { label: 'Dominant Sentiment', key: 'dominant_sentiment' },
]

const sortColumn = ref(null)
const sortDirection = ref('asc')
const currentPage = ref(1)
const itemsPerPage = ref(10)

// Format JSON/array values
const formatCell = (value) => {
  if (typeof value === 'object' && value !== null) {
    return JSON.stringify(value)
  }
  return value
}

// Sorted Data
const sortedData = computed(() => {
  if (!sortColumn.value) return props.data
  return [...props.data].sort((a, b) => {
    const aVal = a[sortColumn.value]
    const bVal = b[sortColumn.value]
    if (aVal == null) return sortDirection.value === 'asc' ? 1 : -1
    if (bVal == null) return sortDirection.value === 'asc' ? -1 : 1
    return sortDirection.value === 'asc'
      ? String(aVal).localeCompare(String(bVal))
      : String(bVal).localeCompare(String(aVal))
  })
})

// Paginated Data
const totalPages = computed(() => Math.ceil(sortedData.value.length / itemsPerPage.value))
const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage.value
  return sortedData.value.slice(start, start + itemsPerPage.value)
})

// Sorting
const sortBy = (column) => {
  if (sortColumn.value === column) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortColumn.value = column
    sortDirection.value = 'asc'
  }
  currentPage.value = 1
}

// Pagination
const nextPage = () => {
  if (currentPage.value < totalPages.value) currentPage.value++
}
const prevPage = () => {
  if (currentPage.value > 1) currentPage.value--
}

// Reset to page 1 on data change
watch(
  () => props.data,
  () => {
    currentPage.value = 1
  },
)
</script>

<template>
  <div
    class="sentiment-table-container bg-card-background p-6 rounded-lg shadow-lg border border-border"
  >
    <h2 class="text-xl font-bold text-primary mb-4">Filtered Sentiment Data</h2>

    <!-- Loading State -->
    <p v-if="loading" class="text-yellow-400 animate-pulse">Loading sentiment data...</p>

    <!-- No Data Message -->
    <p v-if="!loading && paginatedData.length === 0" class="text-gray-400 text-center">
      No data available for the selected filters.
    </p>

    <!-- Data Table -->
    <div v-if="!loading && paginatedData.length > 0" class="table-wrapper overflow-x-auto">
      <table class="min-w-full bg-card-background rounded-lg text-text">
        <thead>
          <tr>
            <th
              v-for="header in headers"
              :key="header.key"
              class="px-4 py-3 text-left text-sm font-medium text-secondary uppercase tracking-wider cursor-pointer hover:bg-hover-background transition-colors duration-200"
              :class="{
                'rounded-tl-lg': header.key === headers[0].key,
                'rounded-tr-lg': header.key === headers.at(-1).key,
              }"
              @click="sortBy(header.key)"
            >
              {{ header.label }}
              <span v-if="sortColumn === header.key">
                {{ sortDirection === 'asc' ? '▲' : '▼' }}
              </span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(item, index) in paginatedData"
            :key="index"
            class="border-t border-border hover:bg-hover-background transition-colors duration-200"
          >
            <td class="px-4 py-3">{{ item.name }}</td>
            <td class="px-4 py-3">{{ item.genres }}</td>
            <td class="px-4 py-3">{{ item.review_text }}</td>
            <td class="px-4 py-3">{{ formatCell(item.expectations) }}</td>
            <td class="px-4 py-3">{{ item.dominant_aspect }}</td>
            <td
              class="px-4 py-3 font-bold"
              :class="{
                'text-sentiment-positive': item.dominant_sentiment === 'positive',
                'text-sentiment-negative': item.dominant_sentiment === 'negative',
                'text-sentiment-neutral': item.dominant_sentiment === 'neutral',
              }"
            >
              {{ item.dominant_sentiment }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination Controls -->
    <div
      v-if="!loading && totalPages > 1"
      class="pagination-controls flex justify-center items-center mt-6 space-x-4"
    >
      <button
        :disabled="currentPage === 1"
        class="bg-primary text-white px-4 py-2 rounded-md hover:bg-primary-dark disabled:bg-gray-700 disabled:text-gray-400 transition-colors duration-200"
        @click="prevPage"
      >
        Previous
      </button>
      <span class="text-text font-medium">Page {{ currentPage }} of {{ totalPages }}</span>
      <button
        :disabled="currentPage === totalPages"
        class="bg-primary text-white px-4 py-2 rounded-md hover:bg-primary-dark disabled:bg-gray-700 disabled:text-gray-400 transition-colors duration-200"
        @click="nextPage"
      >
        Next
      </button>
    </div>
  </div>
</template>

<style scoped>
.text-sentiment-positive {
  color: #27599e;
}

.text-sentiment-neutral {
  color: #a1d5cc;
}

.text-sentiment-negative {
  color: #d9c85f;
}
</style>
