<script setup lang="ts">
import BaseChart from '~/components/diagrams/BaseChart.vue'

defineProps(['chartData'])

const options = {
  responsive: true,
  plugins: {
    legend: { position: 'bottom' },
    title: { display: false },
  },
}
</script>

<template>
  <BaseChart type="pie" :chart-data="chartData" :chart-options="options" />
</template>
