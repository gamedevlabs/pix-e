<script setup lang="ts">
import type { ChartData, ChartOptions } from 'chart.js'

// Strongly typed props
const props = defineProps<{ chartData: ChartData<'pie'> }>()

// Typed chart options
const options: ChartOptions<'pie'> = {
  responsive: true,
  plugins: {
    legend: { position: 'bottom' },
    title: { display: false },
  },
}
</script>

<template>
  <BaseChart
      type="pie"
      :chart-data="props.chartData"
      :chart-options="options"
  />
</template>
