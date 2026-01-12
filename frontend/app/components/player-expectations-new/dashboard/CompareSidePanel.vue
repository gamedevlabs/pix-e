<!-- frontend/app/components/player-expectations-new/dashboard/CompareSidePanel.vue
     What this component does (high level):
     - Renders ONE “side” of the comparison dashboard (Left or Right).
     - Shows the filter UI at the top.
     - Shows the charts below (KPIs, sentiment bar, drivers/heatmaps, and timeline).
     - The actual data is loaded elsewhere (in the composable) and passed in as refs. -->
<script setup lang="ts">
import type { Ref } from 'vue'

// Child components that build up this side panel
import CompareFilters from '~/components/player-expectations-new/dashboard/CompareFilters.vue'
import KpiRow from '~/components/player-expectations-new/dashboard/KpiRow.vue'
import SentimentBar from '~/components/player-expectations-new/dashboard/SentimentBar.vue'
import TopCodesPanel from '~/components/player-expectations-new/dashboard/TopCodesPanel.vue'
import MonthlyRecAndNetLineChart from '~/components/player-expectations-new/dashboard/MonthlyRecAndNetLineChart.vue'

// Types for the API responses and filter values
import type {
  CompareHeatmapCodes,
  CompareKpis,
  CompareSentiments,
  CompareTimeseries,
  CompareTopCodes,
  DashboardLanguage,
  DashboardPolarity,
} from '~/utils/playerExpectationsNewDashboard'

// SideState describes the editable filter state for ONE side
type SideState = {
  appIds: Ref<number[]>
  polarity: Ref<DashboardPolarity>
  languages: Ref<DashboardLanguage[]>
}

defineProps<{
  title: string

  // filter sources
  genreToAppIds: Record<string, number[]>
  gameNames: Record<number, string>

  // v-model-ish side state (refs)
  side: SideState

  // data blocks (refs)
  kpis: Ref<CompareKpis | null>
  sentiments: Ref<CompareSentiments | null>
  timeseries: Ref<CompareTimeseries | null>

  codes: Ref<CompareTopCodes | null>

  heatAesthetics: Ref<CompareHeatmapCodes | null>
  heatFeatures: Ref<CompareHeatmapCodes | null>
  heatPain: Ref<CompareHeatmapCodes | null>
}>()
</script>

<template>
  <!-- Card container for one side -->
  <UCard>
    <div class="space-y-4">
      <!-- Filters -->
      <CompareFilters
        :title="title"
        :genre-to-app-ids="genreToAppIds"
        :game-names="gameNames"
        :app-ids="side.appIds.value"
        :polarity="side.polarity.value"
        :languages="side.languages.value"
        @update:appIds="(v) => (side.appIds.value = v)"
        @update:polarity="(v) => (side.polarity.value = v)"
        @update:languages="(v) => (side.languages.value = v)"
      />

      <!-- KPI + sentiment -->
      <div class="space-y-3">
        <KpiRow :kpis="kpis.value" />
        <SentimentBar :data="sentiments.value" />
      </div>

      <!-- Drivers + heatmaps -->
      <TopCodesPanel
        :data="codes.value"
        :heat-aesthetics="heatAesthetics.value"
        :heat-features="heatFeatures.value"
        :heat-pain="heatPain.value"
      />

      <!-- Timeline -->
      <MonthlyRecAndNetLineChart title="Timeline - Recommendation Rate vs. Net Sentiment (Monthly Average)" :data="timeseries.value" />
    </div>
  </UCard>
</template>
