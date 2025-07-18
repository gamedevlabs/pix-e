<template>
  <div class="p-6 space-y-10">
    <h1 class="text-3xl font-bold mb-6">🎮 Player Expectations Dashboard</h1>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- 1️⃣ Aspect Frequency -->
      <ChartCard title="Top 10 Aspects Mentioned">
        <AspectBarChart :chartData="aspectChartData" />
      </ChartCard>

      <!-- 2️⃣ Sentiment Distribution per Aspect -->
      <ChartCard title="Top 10 Aspects with Sentiment Breakdown">
        <AspectSentimentChart :chartData="sentimentChartData" />

      </ChartCard>

      <!-- 3️⃣ Sentiment Trend Over Time -->
      <ChartCard title="Sentiment Trend Over Time" v-if="lineChartData?.datasets?.length">
        <SentimentTrendChart :chartData="lineChartData" />
      </ChartCard>

      <!-- 4️⃣ Pie Chart: Sentiment Share -->
      <ChartCard title="Overall Sentiment Share">
        <SentimentPieChart :chartData="sentimentPieData" />
      </ChartCard>

      <!-- 5️⃣ Heatmap -->
      <ChartCard title="Positive Mentions per Aspect per Year">
        <AspectHeatmap :heatmapData="heatmapData" />
      </ChartCard>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

// Chart Components
import ChartCard from '~/components/ChartCard.vue'
import AspectBarChart from '~/components/AspectBarChart.vue'
import AspectSentimentChart from '~/components/AspectSentimentChart.vue'
import SentimentTrendChart from '~/components/SentimentTrendChart.vue'
import SentimentPieChart from '~/components/SentimentPieChart.vue'
import AspectHeatmap from '~/components/AspectHeatmap.vue'


// Reactive State
const aspectChartData = ref(null)
const sentimentChartData = ref(null)
const lineChartData = ref(null)
const sentimentPieData = ref(null)
const heatmapData = ref(null)

onMounted(async () => {
  try {
    const res = await axios.get('http://localhost:8000/api/player-expectations/')
    const data = res.data

    // 1️⃣ Aspect Frequency Chart
    aspectChartData.value = {
      labels: Object.keys(data.aspectFrequency),
      datasets: [{
        label: 'Mentions',
        data: Object.values(data.aspectFrequency),
        backgroundColor: '#60a5fa'
      }]
    }

    // 2️⃣ Aspect Sentiment Breakdown
    const rawSentimentData = data.aspectSentiment
    const sentiments = ['positive', 'neutral', 'negative']

    // 提取aspect顺序
    const labels = Array.from(
      new Set(rawSentimentData.map(item => item.dominant_aspect))
    )

    // 初始化一个 Map<sentiment, Map<aspect, count>>
    const sentimentMap = new Map()
    for (const sentiment of sentiments) {
      sentimentMap.set(sentiment, new Map())
    }

    // 填充数据
    for (const item of rawSentimentData) {
      const { dominant_aspect, dominant_sentiment, count } = item
      sentimentMap.get(dominant_sentiment).set(dominant_aspect, count)
    }

    // 构建 chartData
    sentimentChartData.value = {
      labels,
      datasets: sentiments.map(sentiment => ({
        label: sentiment,
        data: labels.map(aspect => sentimentMap.get(sentiment).get(aspect) || 0),
        backgroundColor:
          sentiment === 'positive'
            ? '#22c55e'
            : sentiment === 'neutral'
            ? '#facc15'
            : '#ef4444'
      }))
    }


    // 3️⃣ Trend Over Time
    const trendData = data.trendOverTime
    const timeLabels = trendData.map(i => i.month)
    lineChartData.value = {
      labels: timeLabels,
      datasets: sentiments.map(sentiment => ({
        label: sentiment,
        data: trendData.map(i => i[sentiment] || 0),
        borderColor: sentiment === 'positive' ? '#22c55e' : sentiment === 'neutral' ? '#facc15' : '#ef4444',
        fill: false
      }))
    }

    // 4️⃣ Pie Chart
    sentimentPieData.value = {
      labels: Object.keys(data.sentimentPie),
      datasets: [{
        data: Object.values(data.sentimentPie),
        backgroundColor: ['#22c55e', '#facc15', '#ef4444']
      }]
    }

    // 5️⃣ Heatmap
    heatmapData.value = data.heatmap
  } catch (err) {
    console.error('Error loading data:', err)
  }
})
</script>

<style scoped>
.chart-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.5rem;
}
</style>
