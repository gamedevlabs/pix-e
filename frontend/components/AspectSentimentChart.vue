<script setup>
import BaseChart from '~/components/charts/BaseChart.vue'

defineProps(['chartData'])

const options = {
  responsive: true,
  plugins: {
    title: {
      display: false
    }
  },
  scales: {
    x: {stacked: true},
    y: {stacked: true}
  }
}
</script>

<template>
  <BaseChart type="bar" :chartData="chartData" :chartOptions="options"/>
</template>
