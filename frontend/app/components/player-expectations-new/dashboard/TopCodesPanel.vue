<!-- frontend/app/components/player-expectations-new/dashboard/TopCodesPanel.vue
What this component does (high level):
displays the "drivers/aspect" section for one side of the dashboard.
Uses the /compare/top-codes response to show:
        1) most mentioned aspects (volume)
        2) most positive aspects (net sentiment)
        3) most negative aspects (net sentiment)
Uses the /compare/heatmap-codes responses to render three heatmaps (aesthetics/features/pain) -->
<script setup lang="ts">
import type { CompareHeatmapCodes, CompareTopCodes } from '~/utils/playerExpectationsNewDashboard'

// Subcomponents used to visualize the data
import TopVolumeBarChart from '~/components/player-expectations-new/dashboard/TopVolumeBarChart.vue'
import CodeHeatmapGrid from '~/components/player-expectations-new/dashboard/CodeHeatmapGrid.vue'
import NetAspectsBarChart from '~/components/player-expectations-new/dashboard/NetAspectsBarChart.vue'

// Props:
// data: the top-codes response (or null while loading)
// heat*: three heatmap datasets (or null while loading)
defineProps<{
  data: CompareTopCodes | null
  heatAesthetics: CompareHeatmapCodes | null
  heatFeatures: CompareHeatmapCodes | null
  heatPain: CompareHeatmapCodes | null
}>()
</script>

<template>
  <UCard>
    <div class="flex items-center justify-between">
      <div class="font-semibold">Aspect-Sentiment Pairs</div>
    </div>

    <!-- If we have no top-codes data yet, show a simple placeholder -->
    <div v-if="!data" class="text-sm text-slate-500 dark:text-slate-400 mt-2">—</div>

    <!-- Main content -->
    <div v-else class="mt-4 space-y-5">
      <div>

        <!-- 1) Most mentioned aspects -->
        <div>
          <div class="text-sm font-semibold mb-2">Most Mentioned Aspects</div>
          <TopVolumeBarChart :rows="data.table" :max-bars="15" />
        </div>
        <br />
        <br />

        <!-- 2) Net-sentiment rankings (positive and negative) -->
        <div class="space-y-4">
          <div class="text-sm font-semibold mb-2">Highest Rated Aspects: Ranked by Net Sentiment</div>
          <div class="sm:px-0 mb-3 text-[11px] leading-snug text-slate-600 dark:text-slate-300">
            Net sentiment = (positive mentions − negative mentions) / total mentions,<br />
            ranging from −1 (all negative) to +1 (all positive).
          </div>
          <NetAspectsBarChart title="Most positive" kind="pos" :rows="data.top_positive" />        <br />
          <div class="text-sm font-semibold mb-2">Lowest Rated Aspects: Ranked by Net Sentiment</div>
          <NetAspectsBarChart title="Most negative" kind="neg" :rows="data.top_negative" />
        </div>
      </div>

      <!-- 3) Heatmaps:-->
      <div class="space-y-4">
        <CodeHeatmapGrid title="Heatmap - Game Aesthetics" dimension="aesthetics" :data="heatAesthetics" />
        <CodeHeatmapGrid title="Heatmap - Game Features" dimension="features" :data="heatFeatures" />
        <CodeHeatmapGrid title="Heatmap - Pain Points" dimension="pain" :data="heatPain" />
      </div>
    </div>
  </UCard>
</template>
