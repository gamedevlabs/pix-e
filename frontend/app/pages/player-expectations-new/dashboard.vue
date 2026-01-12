<!-- frontend/app/pages/player-expectations-new/dashboard.vue
 What this page does (high level):
renders the “Comparison Dashboard” page.
creates one composable instance that manages left/right filter state + data.
on first mount, it triggers the initial load.
passes all needed props down into two CompareSidePanel components (Left and Right)...see components for more info
-->
<script setup lang="ts">
import { onMounted, computed } from 'vue'

// UI building blocks for this page
import CompareSidePanel from '~/components/player-expectations-new/dashboard/CompareSidePanel.vue'
import ApiErrorAlert from '~/components/player-expectations-new/dashboard/ApiErrorAlert.vue'

// Shared data (used to show selectable games / genres in the UI)
import { GENRE_APPIDS, GAME_NAMES } from '~/composables/usePlayerExpectationsNewDatasetExplorer'

// Main composable: holds state + loads data for both sides
import { usePlayerExpectationsNewDashboardCompare } from '~/composables/usePlayerExpectationsNewDashboardCompare'

// Sets the browser tab title for this page
useHead({ title: 'Player Expectations - Comparison Dashboard' })

// Create the compare state object (left + right +  loaded data)
const compare = usePlayerExpectationsNewDashboardCompare()

// When the page appears the first time, fetch initial data...otherwise empty
onMounted(compare.load)

// Show a simple "Loading…" hint only during the very first load:
const showLoadingHint = computed(() => compare.loading && !compare.leftKpis.value && !compare.rightKpis.value)
</script>

<template>
  <!-- Simple page layout: padding + vertical spacing between sections -->
  <div class="p-6 space-y-5">
    <div>
      <h1 class="text-3xl font-semibold">Dashboard</h1>
      <!-- Short explanation of what the page is for -->
      <p class="mt-1 text-slate-600 dark:text-slate-300">
        Two independent selections. Compare recommendation rate, sentiment distribution, drivers, heatmaps, and timeline of two subgroups.
      </p>
    </div>

    <!-- If the composable captured an error from any request, show it here..using the error component -->
    <ApiErrorAlert :error="compare.error" />

    <!-- Two-column layout on large screens, one column on small screens -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <!-- LEFT side panel:-->
      <CompareSidePanel
        title="Left selection"
        :genre-to-app-ids="GENRE_APPIDS"
        :game-names="GAME_NAMES"
        :side="compare.left"
        :kpis="compare.leftKpis"
        :sentiments="compare.leftSent"
        :timeseries="compare.leftTs"
        :codes="compare.leftCodes"
        :heat-aesthetics="compare.leftHeatAesthetics"
        :heat-features="compare.leftHeatFeatures"
        :heat-pain="compare.leftHeatPain"
      />

      <!-- RIGHT side panel:-->
      <CompareSidePanel
        title="Right selection"
        :genre-to-app-ids="GENRE_APPIDS"
        :game-names="GAME_NAMES"
        :side="compare.right"
        :kpis="compare.rightKpis"
        :sentiments="compare.rightSent"
        :timeseries="compare.rightTs"
        :codes="compare.rightCodes"
        :heat-aesthetics="compare.rightHeatAesthetics"
        :heat-features="compare.rightHeatFeatures"
        :heat-pain="compare.rightHeatPain"
      />
    </div>

    <!-- Minimal loading hint for the initial load only -->
    <div v-if="showLoadingHint" class="text-sm text-slate-500 dark:text-slate-400">Loading…</div>
  </div>
</template>
