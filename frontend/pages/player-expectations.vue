<template>
  <div class="p-6 space-y-10">
    <h1 class="text-3xl font-bold mb-6">🎮 Player Expectations Dashboard</h1>
<div class="bg-white rounded-lg shadow p-5 border border-gray-200 space-y-3">
  <h2 class="text-2xl font-semibold text-primary">🔍 Dashboard Overview</h2>
  <p class="text-gray-700">
    This dashboard analyzes Steam reviews to uncover player expectations and sentiments using NLP techniques.
  </p>
  <ul class="list-disc list-inside space-y-1 text-gray-700">
    <li>
      <span class="font-semibold">Expectation Extraction:</span>
      Rule-based patterns (SpaCy) for explicit expectations and multi step LLM reasoning for implicit ones. Phrases are mapped to aspects like gameplay, graphics, and story.
    </li>
    <li>
      <span class="font-semibold">Aspect Identification & Clustering:</span>
      Semantic matching (MiniLM embeddings) assigns expectations to aspects. Agglomerative clustering groups similar expectations thematically.
    </li>
    <li>
      <span class="font-semibold">Aspect-Based Sentiment Analysis (ABSA):</span>
      Transformer models (DeBERTa v3, BERT-based ABSA) determine positive, neutral, or negative sentiment for each aspect.
    </li>
  </ul>
</div>

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
      <!-- 6️⃣ Top Confusions -->
<ChartCard title="Top Model-GPT Aspect Confusions">
  <TopConfusionBarChart :chartData="topConfusionsChartData" />
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
import TopConfusionBarChart from '~/components/TopConfusionBarChart.vue'


// Reactive State
const aspectChartData = ref(null)
const sentimentChartData = ref(null)
const lineChartData = ref(null)
const sentimentPieData = ref(null)
const heatmapData = ref(null)
const topConfusionsChartData = ref(null)

onMounted(async () => {
  try {
    const res = await axios.get('http://localhost:8000/api/player-expectations/')
    const data = res.data
    const poster_palette = ['#27599e', '#a1d5cc', '#d9c85f', '#3b6cb2', '#69a89f']

    // 1️⃣ Aspect Frequency Chart
    aspectChartData.value = {
      labels: Object.keys(data.aspectFrequency),
      datasets: [{
        label: 'Mentions',
        data: Object.values(data.aspectFrequency),
        backgroundColor: poster_palette
      }]
    }

    // 2️⃣ Aspect Sentiment Breakdown
    const rawSentimentData = data.aspectSentiment
    const sentiments = ['positive', 'neutral', 'negative']
    const sentimentColors = {
      positive: poster_palette[0],
      neutral: poster_palette[1],
      negative: poster_palette[2]
    }

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
        backgroundColor: sentimentColors[sentiment]
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
        borderColor: sentimentColors[sentiment],
        fill: false
      }))
    }

    // 4️⃣ Pie Chart
    sentimentPieData.value = {
      labels: Object.keys(data.sentimentPie),
      datasets: [{
        data: Object.values(data.sentimentPie),
        backgroundColor: [sentimentColors.positive, sentimentColors.neutral, sentimentColors.negative]
      }]
    }

    // 5️⃣ Heatmap
    heatmapData.value = data.heatmap

    // 6️⃣ Top Confusions Chart
    const confusionPalette = [
    '#27599e', '#a1d5cc', '#d9c85f', // Blue, Teal (light), Yellow (dark)
    '#3b6cb2', '#69a89f', '#f8ef9a', // Blue (light), Teal (dark), Yellow (light)
    '#153b7a', '#8ac9c0', '#f2e686', // Blue (dark), Teal (mid), Yellow (mid)
    '#27599e'                        // Repeat base blue for 11th bar
    ]

    // Trim palette to match number of bars
    const trimmedPalette = confusionPalette.slice(0, data.topConfusions.length)

    topConfusionsChartData.value = {
    labels: data.topConfusions.map(c => c.pair),
    datasets: [{
        label: 'Model → GPT',
        data: data.topConfusions.map(c => c.count),
        backgroundColor: trimmedPalette
    }]
    }
    console.log("data.topConfusions:", data.topConfusions);
    console.log("topConfusionsChartData.value:", topConfusionsChartData.value);
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
