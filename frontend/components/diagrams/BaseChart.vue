<script setup lang="ts">
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  ArcElement,
} from 'chart.js'
import { Bar, Line, Pie } from 'vue-chartjs'

ChartJS.register(
  Title,
  Tooltip,
  Legend,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  CategoryScale,
  LinearScale,
)

defineProps({
  type: {
    type: String,
    required: true,
  },
  chartData: {
    type: Object,
    required: true,
  },
  chartOptions: {
    type: Object,
    default: () => ({}),
  },
})

const chartTypes = {
  bar: Bar,
  line: Line,
  pie: Pie,
}
</script>

<template>
  <component
    :is="chartTypes[type]"
    v-if="chartData?.labels && chartData?.datasets"
    :data="chartData"
    :options="chartOptions"
  />
  <div v-else class="text-gray-500 text-sm p-4 text-center">Chart data not available.</div>
</template>
