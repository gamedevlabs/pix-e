<script setup lang="ts">
import BaseChart from '~/components/diagrams/BaseChart.vue'

defineProps(['chartData'])

const options = {
  responsive: true,
  plugins: {
    legend: { display: false },
    title: { display: false },
  },
}
</script>

<template>
  <BaseChart type="bar" :chart-data="chartData" :chart-options="options" />
</template>
