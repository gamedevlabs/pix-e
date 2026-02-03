<script setup lang="ts">
// ============================================================================
// PAGE CONFIG - Edit these settings for this module
// ============================================================================
definePageMeta({
  middleware: ['authentication', 'project-context'],
  pageConfig: {
    type: 'project-required',
    showSidebar: true,
    title: 'Player Expectations',
    icon: 'i-lucide-book-open',
    navGroup: 'main',
    navOrder: 4,
    showInNav: true,
  },
})
// ============================================================================

const {
  aspectChartData,
  sentimentChartData,
  lineChartData,
  sentimentPieData,
  heatmapData,
  topConfusionsChartData,
  load,
} = usePlayerExpectationCharts('http://localhost:8000/api')

onMounted(load)
</script>

<template>
  <div class="p-4 space-y-10">
    <h1 class="text-3xl font-bold mb-6">🎮 Player Expectations Dashboard</h1>
    <UCard>
      <template #header>
        <h2 class="text-2xl font-semibold text-primary">🔍 Dashboard Overview</h2>
      </template>

      <p class="text-gray-700">
        This dashboard analyzes Steam reviews to uncover player expectations and sentiments using
        NLP techniques.
      </p>
      <ul class="list-disc list-inside space-y-1 text-gray-700">
        <li>
          <span class="font-semibold">Expectation Extraction:</span>
          Rule-based patterns (SpaCy) for explicit expectations and multi step LLM reasoning for
          implicit ones. Phrases are mapped to aspects like gameplay, graphics, and story.
        </li>
        <li>
          <span class="font-semibold">Aspect Identification & Clustering:</span>
          Semantic matching (MiniLM embeddings) assigns expectations to aspects. Agglomerative
          clustering groups similar expectations thematically.
        </li>
        <li>
          <span class="font-semibold">Aspect-Based Sentiment Analysis (ABSA):</span>
          Transformer models (DeBERTa v3, BERT-based ABSA) determine positive, neutral, or negative
          sentiment for each aspect.
        </li>
      </ul>
    </UCard>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- 1️⃣ Aspect Frequency -->
      <UCard>
        <template #header>
          <h2 class="text-xl font-semibold text-primary">Top 10 Aspects Mentioned</h2>
        </template>
        <AspectBarChart :chart-data="aspectChartData" />
      </UCard>

      <!-- 2️⃣ Sentiment Distribution per Aspect -->
      <UCard>
        <template #header>
          <h2 class="text-xl font-semibold text-primary">
            Top 10 Aspects with Sentiment Breakdown
          </h2>
        </template>
        <AspectSentimentChart :chart-data="sentimentChartData" />
      </UCard>

      <!-- 3️⃣ Sentiment Trend Over Time -->
      <UCard v-if="lineChartData?.datasets?.length">
        <template #header>
          <h2 class="text-xl font-semibold text-primary">Sentiment Trend Over Time</h2>
        </template>
        <SentimentTrendChart :chart-data="lineChartData" />
      </UCard>

      <!-- 4️⃣ Pie Chart: Sentiment Share -->
      <UCard>
        <template #header>
          <h2 class="text-xl font-semibold text-primary">Overall Sentiment Share</h2>
        </template>
        <SentimentPieChart :chart-data="sentimentPieData" />
      </UCard>

      <!-- 5️⃣ Heatmap -->
      <UCard>
        <template #header>
          <h2 class="text-xl font-semibold text-primary">Positive Mentions per Aspect per Year</h2>
        </template>
        <AspectHeatmap :heatmap-data="heatmapData" />
      </UCard>

      <!-- 6️⃣ Top Confusions -->
      <UCard>
        <template #header>
          <h2 class="text-xl font-semibold text-primary">Top Model-GPT Aspect Confusions</h2>
        </template>
        <TopConfusionBarChart :chart-data="topConfusionsChartData" />
      </UCard>
    </div>
  </div>
</template>

<style scoped>
.chart-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.5rem;
}
</style>
