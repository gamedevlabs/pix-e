<script setup>
import BaseChart from '~/components/charts/BaseChart.vue'

defineProps(['chartData'])

const options = {
  responsive: true,
  plugins: {
    legend: { position: 'bottom' },
    title: { display: false }
  }
}
</script>

<template>
  <BaseChart type="pie" :chartData="chartData" :chartOptions="options" />
</template>
