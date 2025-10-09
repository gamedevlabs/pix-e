<script setup lang="ts">
import type { ChartData, ChartOptions } from 'chart.js'

// If this chart is always a bar chart, use the generic for better types:
type T = 'bar'

// Option A: keep `props.chartData`
const props = defineProps<{ chartData: ChartData<T> | null }>()

const options: ChartOptions<T> = {
  responsive: true,
  plugins: {
    title: { display: false },
  },
  scales: {
    x: { stacked: true },
    y: { stacked: true },
  },
}
</script>

<template>
  <BaseChart type="bar" :chart-data="props.chartData" :chart-options="options" />
</template>
