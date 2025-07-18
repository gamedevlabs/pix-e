<script setup>
import BaseChart from '~/components/charts/BaseChart.vue'

defineProps(['chartData'])

const options = {
  responsive: true,
  plugins: {
    legend: {display: false},
    title: {display: false}
  }
}
</script>

<template>
  <BaseChart type="bar" :chartData="chartData" :chartOptions="options"/>
</template>
