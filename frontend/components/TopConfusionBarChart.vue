<template>
  <div class="chart-container">
    <Bar
      :data="chartData"
      :options="chartOptions"
      v-if="chartData && chartData.labels && chartData.labels.length > 0"
    />
    <p v-else>No confusion data to display.</p>
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
  chartData: {
    type: Object,
    default: () => ({ labels: [], datasets: [] })
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
      labels: {
        color: 'var(--color-text)',
        usePointStyle: true,
        pointStyle: 'rect', // Use a rectangle for consistency, but it will be hidden by usePointStyle
        boxWidth: 0, // Hide the color box
      }
    },
    title: {
      display: false,
    }
  },
  scales: {
    x: {
      ticks: {
        color: 'var(--color-text)'
      },
      grid: {
        color: 'rgba(255, 255, 255, 0.1)'
      }
    },
    y: {
      beginAtZero: true,
      ticks: {
        color: 'var(--color-text)'
      },
      grid: {
        color: 'rgba(255, 255, 255, 0.1)'
      }
    }
  }
}
</script>

<style scoped>
.chart-container {
  height: 600px; /* Fixed height for the chart container */
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}
</style>