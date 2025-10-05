<script setup>
import BaseChart from '~/components/diagrams/BaseChart.vue'

defineProps(['chartData'])

const options = {
  responsive: true,
  indexAxis: 'y', // Horizontal bars
  plugins: {
    legend: { display: false },
    title: {
      display: true,
      text: 'Top Model-GPT Aspect Confusions',
      font: { size: 18 },
    },
  },
  scales: {
    x: {
      beginAtZero: true,
      title: {
        display: true,
        text: 'Number of Confusions',
      },
    },
    y: {
      title: {
        display: true,
        text: 'Model → GPT',
      },
      ticks: {
        autoSkip: false,
        font: { size: 12 },
      },
    },
  },
}
</script>

<template>
  <BaseChart type="bar" :chart-data="chartData" :chart-options="options" />
</template>
