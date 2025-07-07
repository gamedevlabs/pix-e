<template>
  <div class="sentiment-table-container">
    <h2 v-if="!loading && !error">Sentiment Data</h2>
    <p v-if="loading">Loading sentiment data...</p>
    <p v-if="error" class="error-message">Error: {{ error }}</p>

    <div v-if="!loading && !error && data.length > 0" class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>Game Name</th>
            <th>Genres</th>
            <th>Review Text</th>
            <th>Explicit Expectations</th>
            <th>Dominant Aspect</th>
            <th>Dominant Sentiment</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, index) in data" :key="index">
            <td>{{ item.name }}</td>
            <td>{{ item.genres }}</td>
            <td>{{ item.review_text }}</td>
            <td>{{ item.explicit_expectations }}</td>
            <td>{{ item.dominant_aspect }}</td>
            <td>{{ item.dominant_sentiment }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p v-if="!loading && !error && data.length === 0">No data available.</p>
  </div>
</template>

<script setup>
import { defineProps } from 'vue'

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
</script>

<style scoped>
.sentiment-table-container {
  margin-top: 20px;
}

.table-wrapper {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 15px;
}

th, td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

th {
  background-color: #f2f2f2;
}

.error-message {
  color: red;
  font-weight: bold;
}
</style>