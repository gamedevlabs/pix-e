<script setup lang="ts">
import type { ChartData, ChartOptions } from 'chart.js'
import { Bar } from 'vue-chartjs'

// ✅ Define typed props
const props = withDefaults(
    defineProps<{ chartData?: ChartData<'bar'> | null }>(),
    {
      chartData: () => ({ labels: [], datasets: [] }),
    }
)

// ✅ Strongly typed chart options
const chartOptions: ChartOptions<'bar'> = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
      labels: {
        color: 'var(--color-text)',
        usePointStyle: true,
        pointStyle: 'rect', // stylistic only
        boxWidth: 0,        // hide color box
      },
    },
    title: { display: false },
  },
  scales: {
    x: {
      ticks: { color: 'var(--color-text)' },
      grid: { color: 'rgba(255, 255, 255, 0.1)' },
    },
    y: {
      beginAtZero: true,
      ticks: { color: 'var(--color-text)' },
      grid: { color: 'rgba(255, 255, 255, 0.1)' },
    },
  },
}
</script>

<template>
  <div class="chart-container">
    <Bar
        v-if="props.chartData?.labels?.length"
        :data="props.chartData"
        :options="chartOptions"
    />
    <p v-else>No confusion data to display.</p>
  </div>
</template>

<style scoped>
.chart-container {
  height: 600px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}
</style>
