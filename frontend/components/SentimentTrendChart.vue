<script setup>
import BaseChart from '~/components/charts/BaseChart.vue'

const props = defineProps({
  chartData: {
    type: Object,
    required: true
  }
})

const options = {
  responsive: true,
  interaction: {mode: 'index', intersect: false},
  stacked: false,
  plugins: {
    title: {display: false}
  },
  scales: {
    x: {title: {display: true, text: 'Month'}},
    y: {title: {display: true, text: 'Mentions'}}
  }
}
</script>

<template>
  <div class="h-64">
    <BaseChart
        v-if="chartData?.labels && chartData?.datasets"
        type="line"
        :chartData="chartData"
        :chartOptions="options"
    />
    <div v-else class="text-sm text-gray-500 p-4">
      Loading chart data...
    </div>
  </div>
</template>
