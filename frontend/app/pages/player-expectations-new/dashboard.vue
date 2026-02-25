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
definePageMeta({
  middleware: ['authentication', 'project-context'],
  pageConfig: {
    type: 'project-required',
    showSidebar: true,
    title: 'Dashboard',
    icon: 'i-lucide-layout-dashboard',
    navGroup: 'main',
    navParent: 'player-expectations-landing',
    navOrder: 1,
    showInNav: true,
  },
})
// Sets the browser tab title for this page
useHead({ title: 'Player Expectations - Comparison Dashboard' })

// Create the compare state object (left + right +  loaded data)
const compare = usePlayerExpectationsNewDashboardCompare()

// When the page appears the first time, fetch initial data...otherwise empty
onMounted(compare.load)

//just bug fixing to check if dash is properly unmounted
//onMounted(() => console.log('DASH mounted'))
//onBeforeUnmount(() => console.log('DASH unmounted'))

// Show a simple "Loading…" hint only during the very first load:
const showLoadingHint = computed(
  () => compare.loading && !compare.leftKpis.value && !compare.rightKpis.value,
)
</script>

<template>
  <div class="p-6 space-y-5">
    <!-- Simple page layout: padding + vertical spacing between sections -->
    <div>
      <h1 class="text-3xl font-semibold">Dashboard</h1>
      <!-- Short explanation of what the page is for -->
      <p class="mt-1 text-slate-600 dark:text-slate-300">
        Two independent selections. Compare recommendation rate, sentiment distribution, drivers,
        heatmaps, and timeline of two subgroups.
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
        :app-ids="compare.left.appIds.value"
        :polarity="compare.left.polarity.value"
        :languages="compare.left.languages.value"
        :kpis="compare.leftKpis"
        :sentiments="compare.leftSent"
        :timeseries="compare.leftTs"
        :codes="compare.leftCodes"
        :heat-aesthetics="compare.leftHeatAesthetics"
        :heat-features="compare.leftHeatFeatures"
        :heat-pain="compare.leftHeatPain"
        @update:app-ids="(v) => (compare.left.appIds.value = v)"
        @update:polarity="(v) => (compare.left.polarity.value = v)"
        @update:languages="(v) => (compare.left.languages.value = v)"
      />

      <!-- RIGHT side panel:-->
      <CompareSidePanel
        title="Right selection"
        :genre-to-app-ids="GENRE_APPIDS"
        :game-names="GAME_NAMES"
        :app-ids="compare.right.appIds.value"
        :polarity="compare.right.polarity.value"
        :languages="compare.right.languages.value"
        :kpis="compare.rightKpis"
        :sentiments="compare.rightSent"
        :timeseries="compare.rightTs"
        :codes="compare.rightCodes"
        :heat-aesthetics="compare.rightHeatAesthetics"
        :heat-features="compare.rightHeatFeatures"
        :heat-pain="compare.rightHeatPain"
        @update:app-ids="(v) => (compare.right.appIds.value = v)"
        @update:polarity="(v) => (compare.right.polarity.value = v)"
        @update:languages="(v) => (compare.right.languages.value = v)"
      />
    </div>

    <!-- Minimal loading hint for the initial load only -->
    <div v-if="showLoadingHint" class="text-sm text-slate-500 dark:text-slate-400">Loading…</div>
  </div>
</template>
