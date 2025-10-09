<script setup lang="ts">
import { computed } from 'vue'
import { Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
} from 'chart.js'

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale)

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

const aspectCounts = computed(() => {
  const counts = {}
  props.data.forEach((item) => {
    if (item.dominant_aspect) {
      const aspect = item.dominant_aspect
      counts[aspect] = (counts[aspect] || 0) + 1
    }
  })
  return counts
})

const chartData = computed(() => {
  const sortedAspects = Object.entries(aspectCounts.value)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 10) // Top 10 dominant aspects

  const labels = sortedAspects.map(([aspect]) => aspect)
  const data = sortedAspects.map(([, count]) => count)

  return {
    labels: labels,
    datasets: [
      {
        label: 'Dominant Aspect Count',
        backgroundColor: '#27599e',
        data: data,
      },
    ],
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false,
    },
    title: {
      display: true,
      text: 'Top 10 Dominant Aspects',
      color: 'var(--color-primary)',
    },
  },
  scales: {
    x: {
      ticks: {
        color: 'var(--color-text)',
      },
    },
    y: {
      ticks: {
        color: 'var(--color-text)',
      },
    },
  },
}
</script>

<template>
  <UCard>
    <template #header> Dominant Aspect Analysis </template>
    <div class="chart-container">
      <Bar
        v-if="!loading && chartData.labels.length > 0"
        :data="chartData"
        :options="chartOptions"
      />
      <p v-if="!loading && chartData.labels.length === 0">No dominant aspect data to display.</p>
      <p v-if="loading">Loading...</p>
    </div>
  </UCard>
</template>

<style scoped>
.chart-container {
  background-color: var(--color-card-background);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 15px;
  height: 600px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}
</style>
