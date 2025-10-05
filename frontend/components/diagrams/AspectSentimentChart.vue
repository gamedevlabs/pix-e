<script setup lang="ts">
import BaseChart from '~/components/diagrams/BaseChart.vue'

defineProps(['chartData'])

const options = {
  responsive: true,
  plugins: {
    title: {
      display: false,
    },
  },
  scales: {
    x: { stacked: true },
    y: { stacked: true },
  },
}
</script>

<template>
  <BaseChart type="bar" :chart-data="chartData" :chart-options="options" />
</template>
