<script setup lang="ts">
import { Bar, Line, Pie } from 'vue-chartjs'
import type { ChartData, ChartOptions } from 'chart.js'

type ChartType = 'bar' | 'line' | 'pie'

// Strongly-typed props with a default for options
const props = withDefaults(
  defineProps<{
    type: ChartType
    chartData: ChartData | null
    chartOptions?: ChartOptions
  }>(),
  {
    chartOptions: () => ({}),
  },
)

const chartTypes: Record<ChartType, Component> = {
  bar: Bar,
  line: Line,
  pie: Pie,
}

// Select the component based on the prop (keeps TS happy)
const Selected = computed(() => chartTypes[props.type])
</script>

<template>
  <component
    :is="Selected"
    v-if="chartData?.labels && chartData?.datasets"
    :data="chartData"
    :options="chartOptions"
  />
  <div v-else class="text-gray-500 text-sm p-4 text-center">Chart data not available.</div>
</template>
