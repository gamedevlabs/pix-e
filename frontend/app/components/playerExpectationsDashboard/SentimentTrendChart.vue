<script setup lang="ts">
import type { ChartData, ChartOptions } from 'chart.js'

// ✅ Strongly typed props
const props = defineProps<{ chartData: ChartData<'line'> }>()

// ✅ Typed chart options for a line chart
const options: ChartOptions<'line'> = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  plugins: {
    title: { display: false },
  },
  scales: {
    x: { title: { display: true, text: 'Month' } },
    y: { title: { display: true, text: 'Mentions' } },
  },
}
</script>

<template>
  <div class="h-[600px]">
    <BaseChart
      v-if="props.chartData?.labels && props.chartData?.datasets"
      type="line"
      :chart-data="props.chartData"
      :chart-options="options"
    />
    <div v-else class="text-sm text-gray-500 p-4">Loading chart data...</div>
  </div>
</template>
