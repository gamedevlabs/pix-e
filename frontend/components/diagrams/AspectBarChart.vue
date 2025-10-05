<script setup lang="ts">
import type { ChartData, ChartOptions } from 'chart.js'

// Define props with types
const props = defineProps<{
  chartData: ChartData
}>()

// Define your chart options (fully typed)
const options: ChartOptions = {
  responsive: true,
  plugins: {
    legend: { display: false },
    title: { display: false },
  },
}
</script>

<template>
  <BaseChart
      type="bar"
      :chart-data="props.chartData"
      :chart-options="options"
  />
</template>
