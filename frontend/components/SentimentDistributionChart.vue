<template>
  <ChartCard title="Sentiment Distribution">
    <div class="chart-container">
      <Doughnut v-if="chartData.labels.length > 0" :data="chartData" :options="chartOptions" />
      <p v-else>No sentiment data to display.</p>
    </div>
  </ChartCard>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Doughnut } from 'vue-chartjs'
import { Chart as ChartJS, Title, Tooltip, Legend, ArcElement, CategoryScale } from 'chart.js'
import ChartCard from '@/components/ChartCard.vue'

ChartJS.register(Title, Tooltip, Legend, ArcElement, CategoryScale)

const props = defineProps({
  data: {
    type: Array,
    default: () => [],
  },
})

const positiveColor = ref('#27599e')
const neutralColor = ref('#a1d5cc')
const negativeColor = ref('#d9c85f')

const sentimentCounts = computed(() => {
  const counts = {
    positive: 0,
    negative: 0,
    neutral: 0,
  }
  props.data.forEach((item) => {
    const sentiment = item.dominant_sentiment?.toLowerCase()
    if (sentiment === 'positive') {
      counts.positive++
    } else if (sentiment === 'negative') {
      counts.negative++
    } else {
      // Consider null, undefined, or other values as neutral
      counts.neutral++
    }
  })
  return counts
})

const chartData = computed(() => {
  const labels = []
  const data = []
  const backgroundColors = []

  if (sentimentCounts.value.positive > 0) {
    labels.push('Positive')
    data.push(sentimentCounts.value.positive)
    backgroundColors.push(positiveColor.value)
  }
  if (sentimentCounts.value.negative > 0) {
    labels.push('Negative')
    data.push(sentimentCounts.value.negative)
    backgroundColors.push(negativeColor.value)
  }
  if (sentimentCounts.value.neutral > 0) {
    labels.push('Neutral')
    data.push(sentimentCounts.value.neutral)
    backgroundColors.push(neutralColor.value)
  }

  return {
    labels: labels,
    datasets: [
      {
        backgroundColor: backgroundColors,
        data: data,
      },
    ],
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'right',
      labels: {
        color: 'var(--color-text)', // Use CSS variable for legend text color
      },
    },
    title: {
      display: false,
      text: 'Sentiment Distribution',
      color: 'var(--color-primary)', // Use CSS variable for title color
    },
  },
}
</script>

<style scoped>
.chart-container {
  height: 600px; /* Fixed height for the chart container */
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

h3 {
  margin-bottom: 10px;
}
</style>
