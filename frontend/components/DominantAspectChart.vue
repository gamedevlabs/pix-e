<template>
  <div class="chart-container">
    <h3>Top Dominant Aspects</h3>
    <Bar
      :data="chartData"
      :options="chartOptions"
      v-if="chartData.labels.length > 0"
    />
    <p v-else>No dominant aspect data to display.</p>
  </div>
</template>

<script setup>
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
    default: () => []
  }
})

const aspectCounts = computed(() => {
  const counts = {}
  props.data.forEach(item => {
    const aspect = item.dominant_aspect?.toLowerCase()
    if (aspect && aspect !== 'nan') { // Exclude NaN values
      counts[aspect] = (counts[aspect] || 0) + 1
    }
  })
  // Sort aspects by count in descending order and take top N
  return Object.entries(counts)
    .sort(([, countA], [, countB]) => countB - countA)
    .slice(0, 10) // Show top 10 aspects
    .reduce((acc, [aspect, count]) => {
      acc[aspect] = count
      return acc
    }, {})
})

const chartData = computed(() => {
  const labels = Object.keys(aspectCounts.value)
  const data = Object.values(aspectCounts.value)

  return {
    labels: labels,
    datasets: [
      {
        label: 'Number of Mentions',
        backgroundColor: '#00CED1', // DarkTurquoise
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
      display: false, // No need for legend if only one dataset
    },
    title: {
      display: true,
      text: 'Top 10 Dominant Aspects',
      color: 'var(--color-primary)' // Use CSS variable for title color
    }
  },
  scales: {
    x: {
      ticks: {
        color: 'var(--color-text)' // Use CSS variable for x-axis labels
      },
      grid: {
        color: 'rgba(255, 255, 255, 0.1)' // Light grid lines
      }
    },
    y: {
      beginAtZero: true,
      ticks: {
        color: 'var(--color-text)' // Use CSS variable for y-axis labels
      },
      grid: {
        color: 'rgba(255, 255, 255, 0.1)' // Light grid lines
      }
    }
  }
}
</script>

<style scoped>
.chart-container {
  background-color: var(--color-card-background);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 15px;
  height: 300px; /* Fixed height for the chart container */
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

h3 {
  margin-bottom: 10px;
}
</style>
