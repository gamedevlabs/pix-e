<!-- frontend/app/pages/player-expectations-new/dataset-explorer.vue -->
<script setup lang="ts">
//the actual page that the user visits ("Dataset Explorer").

import { computed, onMounted } from 'vue'

/*
 UI components (they render HTML).
 Each component gets props like refs, arrays, and handler functions.
 */
import DatasetExplorerTopFilterBar from '~/components/player-expectations-new/DatasetExplorer/DatasetExplorerTopFilterBar.vue'
import DatasetExplorerFiltersSidebar from '~/components/player-expectations-new/DatasetExplorer/DatasetExplorerFiltersSidebar.vue'
import DatasetExplorerReviewList from '~/components/player-expectations-new/DatasetExplorer/DatasetExplorerReviewList.vue'
import DatasetExplorerReviewDetail from '~/components/player-expectations-new/DatasetExplorer/DatasetExplorerReviewDetail.vue'

/*
import both core composable and the view model composable
 */
import { usePlayerExpectationsNewDatasetExplorer } from '~/composables/usePlayerExpectationsNewDatasetExplorer'
import { useDatasetExplorerViewModel } from '~/composables/useDatasetExplorerViewModel'

//Create the core state manager
const core = usePlayerExpectationsNewDatasetExplorer('/api/player-expectations-new')
//Create the view model, passing the core object into it.
const vm = useDatasetExplorerViewModel(core)


//  Error banner fix: ref object is "truthy" even if its .value is empty. ->create a computed string value
const errorTextValue = computed(() => (typeof vm.errorText.value === 'string' ? vm.errorText.value : ''))

// Sidebar prop-type fix: "Expected Array, got Object" -> wrappers guarantee we pass an array
const filteredFeatureGroupsValue = computed(() => (Array.isArray(vm.filteredFeatureGroups.value) ? vm.filteredFeatureGroups.value : []))
const filteredPainGroupsValue = computed(() => (Array.isArray(vm.filteredPainGroups.value) ? vm.filteredPainGroups.value : []))

/*
 * onMounted(...) runs when the page loads the first time
 * it calls core.load() to fetch the first page of reviews from the backend.
 */
onMounted(core.load)
</script>

<template>
  <div class="p-6 space-y-5">
    <div>
      <h1 class="text-3xl font-semibold">Dataset Explorer</h1>
      <p class="mt-1 text-slate-600 dark:text-slate-300">
        Browse reviews. Select one to inspect extracted quote → code → sentiment pairs.
      </p>
    </div>

    <!-- Top filter bar: pass refs + functions so the component can update filters and paginate. -->
    <DatasetExplorerTopFilterBar
      :q="core.q"
      :recommended="core.recommended"
      :sort="core.sort"
      :date-from="core.dateFrom"
      :date-to="core.dateTo"
      :min-votes-up="core.minVotesUp"
      :max-votes-up="core.maxVotesUp"
      :min-votes-funny="core.minVotesFunny"
      :max-votes-funny="core.maxVotesFunny"
      :min-playtime-at-review="core.minPlaytimeAtReview"
      :max-playtime-at-review="core.maxPlaytimeAtReview"
      :min-playtime-forever="core.minPlaytimeForever"
      :max-playtime-forever="core.maxPlaytimeForever"
      :page-size="core.pageSize"
      :loading="core.loading"
      :meta="core.meta"
      :prev-page="core.prevPage"
      :next-page="core.nextPage"
      :set-polarity="vm.setPolarity"
    />

    <!-- FIX: use the string value, not a ref object -->
    <UAlert v-if="errorTextValue" color="error" variant="soft" title="API error">
      <pre class="text-xs whitespace-pre-wrap">{{ errorTextValue }}</pre>
    </UAlert>

    <!-- Main layout: sidebar / list / detail -->
    <div class="grid grid-cols-12 gap-4">
      <!-- Left: filters sidebar...pass many refs so the sidebar can toggle them-->
      <DatasetExplorerFiltersSidebar
        class="col-span-12 lg:col-span-3 h-[clamp(520px,120vh,760px)] card"
        :selected-genres="core.selectedGenres"
        :selected-games="core.selectedGames"
        :visible-games="core.visibleGames"
        :selected-aesthetic-codes="core.selectedAestheticCodes"
        :selected-feature-codes="core.selectedFeatureCodes"
        :selected-pain-codes="core.selectedPainCodes"
        :aesthetic-codes="vm.aestheticCodes"
        :feature-search="vm.featureSearch"
        :pain-search="vm.painSearch"
        :filtered-feature-groups="filteredFeatureGroupsValue"
        :filtered-pain-groups="filteredPainGroupsValue"
        :click-genre="vm.clickGenre"
        :click-game="vm.clickGame"
        :click-code="vm.clickCode"
        :chip-variant="vm.chipVariant"
      />

      <!-- Middle: review list...displays the current page of reviews -->
      <DatasetExplorerReviewList
        class="col-span-12 lg:col-span-5 h-[clamp(520px,120vh,760px)] card"
        :rows="core.rows"
        :meta="core.meta"
        :loading="core.loading"
        :page-size="core.pageSize"
        :selected-rec-id="vm.selectedRecId"
        :truncate="vm.truncate"
        :format-unix="vm.formatUnix"
      />

      <!-- Right: detail view for the selected review-->
      <DatasetExplorerReviewDetail
        class="col-span-12 lg:col-span-4 h-[clamp(520px,120vh,760px)] card"
        :selected-review="vm.selectedReview"
        :pretty-sentiment="core.prettySentiment"
        :format-unix="vm.formatUnix"
        :highlight-review-html="vm.highlightReviewHtml"
      />
    </div>
  </div>
</template>

<style scoped>
/* These CSS variables set colors for "card" components in light/dark mode.*/

/* Light mode defaults */
:global(:root) {
  --dex-card-bg: #ffffff;
  --dex-card-text: rgb(15, 23, 42);
  --dex-card-border: rgba(15, 23, 42, 0.12);
  --dex-card-header-border: rgba(15, 23, 42, 0.08);

  --dex-seg-border: rgba(15, 23, 42, 0.16);
  --dex-seg-bg: rgba(15, 23, 42, 0.04);
  --dex-seg-on-bg: rgba(15, 23, 42, 0.10);
  --dex-seg-on-text: rgb(15, 23, 42);
  --dex-seg-off-text: rgba(15, 23, 42, 0.78);

  --dex-row-hover: rgba(15, 23, 42, 0.04);
  --dex-row-selected: rgba(15, 23, 42, 0.06);
  --dex-row-selected-border: rgba(15, 23, 42, 0.25);
}

/* Dark mode only when the app actually applies a dark selector */
:global(html.dark),
:global(body.dark),
:global(.dark),
:global([data-theme='dark']) {
  --dex-card-bg: rgba(2, 6, 23, 0.55);
  --dex-card-text: rgb(226, 232, 240);
  --dex-card-border: rgba(148, 163, 184, 0.18);
  --dex-card-header-border: rgba(148, 163, 184, 0.14);

  --dex-seg-border: rgba(148, 163, 184, 0.22);
  --dex-seg-bg: rgba(148, 163, 184, 0.08);
  --dex-seg-on-bg: rgba(148, 163, 184, 0.18);
  --dex-seg-on-text: rgb(241, 245, 249);
  --dex-seg-off-text: rgba(241, 245, 249, 0.80);

  --dex-row-hover: rgba(148, 163, 184, 0.10);
  --dex-row-selected: rgba(148, 163, 184, 0.14);
  --dex-row-selected-border: rgba(241, 245, 249, 0.22);
}

/*style classes inside child components with deep*/
:deep(.card) {
  border-radius: 12px;
  border: 1px solid var(--dex-card-border);
  background: var(--dex-card-bg);
  color: var(--dex-card-text);
  display: flex;
  flex-direction: column;
  min-height: 0;
  backdrop-filter: blur(10px);
}

:deep(.card-header) {
  padding: 12px 14px;
  border-bottom: 1px solid var(--dex-card-header-border);
  flex: 0 0 auto;
}

:deep(.card-scroll) {
  padding: 12px 14px;
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior: contain;
}

:deep(.segmented) {
  height: 30px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  border: 1px solid var(--dex-seg-border);
  border-radius: 10px;
  overflow: hidden;
  background: var(--dex-seg-bg);
}

:deep(.seg-btn) {
  height: 30px;
  padding: 0 10px;
  font-size: 0.82rem;
  line-height: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  user-select: none;
  white-space: nowrap;
  border-right: 1px solid var(--dex-seg-border);
}
:deep(.seg-btn:last-child) {
  border-right: none;
}

:deep(.seg-btn--on) {
  background: var(--dex-seg-on-bg);
  color: var(--dex-seg-on-text);
  font-weight: 600;
}

:deep(.seg-btn--off) {
  background: transparent;
  color: var(--dex-seg-off-text);
}
:deep(.seg-btn--off:hover) {
  background: var(--dex-row-hover);
}

:deep(.review-row) {
  width: 100%;
  text-align: left;
  padding: 12px 14px;
  border-left: 2px solid transparent;
  background: transparent;
}
:deep(.review-row:hover) {
  background: var(--dex-row-hover);
}
:deep(.review-row--selected) {
  background: var(--dex-row-selected);
  border-left-color: var(--dex-row-selected-border);
}
</style>
