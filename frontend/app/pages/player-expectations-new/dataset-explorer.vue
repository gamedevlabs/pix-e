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

definePageMeta({
  middleware: ['authentication', 'project-context'],
  pageConfig: {
    type: 'project-required',
    showSidebar: true,
    title: 'Dataset Explorer (v2)',
    icon: 'i-lucide-telescope',
    navGroup: 'main',
    navParent: 'player-expectations-landing',
    navOrder: 4,
    showInNav: true,
  },
})
//Create the core state manager
const core = usePlayerExpectationsNewDatasetExplorer()
//Create the view model, passing the core object into it.
const vm = useDatasetExplorerViewModel(core)

//  Error banner fix: ref object is "truthy" even if its .value is empty. ->create a computed string value
const errorTextValue = computed(() => vm.errorText.value)

// Sidebar prop-type fix: "Expected Array, got Object" -> wrappers guarantee we pass an array
const filteredFeatureGroupsValue = computed(() =>
  Array.isArray(vm.filteredFeatureGroups.value) ? vm.filteredFeatureGroups.value : [],
)
const filteredPainGroupsValue = computed(() =>
  Array.isArray(vm.filteredPainGroups.value) ? vm.filteredPainGroups.value : [],
)
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
      :q="core.q.value"
      :recommended="core.recommended.value"
      :sort="core.sort.value"
      :date-from="core.dateFrom.value"
      :date-to="core.dateTo.value"
      :min-votes-up="core.minVotesUp.value"
      :max-votes-up="core.maxVotesUp.value"
      :min-votes-funny="core.minVotesFunny.value"
      :max-votes-funny="core.maxVotesFunny.value"
      :min-playtime-at-review="core.minPlaytimeAtReview.value"
      :max-playtime-at-review="core.maxPlaytimeAtReview.value"
      :min-playtime-forever="core.minPlaytimeForever.value"
      :max-playtime-forever="core.maxPlaytimeForever.value"
      :page-size="core.pageSize.value"
      :loading="core.loading.value"
      :meta="core.meta.value"
      :prev-page="core.prevPage"
      :next-page="core.nextPage"
      @update:q="(v) => (core.q.value = v)"
      @update:recommended="(v) => (core.recommended.value = v)"
      @update:sort="(v) => (core.sort.value = v)"
      @update:date-from="(v) => (core.dateFrom.value = v)"
      @update:date-to="(v) => (core.dateTo.value = v)"
      @update:min-votes-up="(v) => (core.minVotesUp.value = v)"
      @update:max-votes-up="(v) => (core.maxVotesUp.value = v)"
      @update:min-votes-funny="(v) => (core.minVotesFunny.value = v)"
      @update:max-votes-funny="(v) => (core.maxVotesFunny.value = v)"
      @update:min-playtime-at-review="(v) => (core.minPlaytimeAtReview.value = v)"
      @update:max-playtime-at-review="(v) => (core.maxPlaytimeAtReview.value = v)"
      @update:min-playtime-forever="(v) => (core.minPlaytimeForever.value = v)"
      @update:max-playtime-forever="(v) => (core.maxPlaytimeForever.value = v)"
      @update:page-size="(v) => (core.pageSize.value = v)"
    />

    <!-- FIX: use the string value, not a ref object -->
    <UAlert v-if="errorTextValue" color="error" variant="soft" title="API error">
      <pre class="text-xs whitespace-pre-wrap">{{ errorTextValue }}</pre>
    </UAlert>

    <!-- Main layout: sidebar / list / detail -->
    <div class="grid grid-cols-12 gap-4">
      <!-- Left: filters sidebar...pass many refs so the sidebar can toggle them-->
      <DatasetExplorerFiltersSidebar
        :feature-search="vm.featureSearch.value"
        :pain-search="vm.painSearch.value"
        class="col-span-12 lg:col-span-3 h-[clamp(520px,120vh,760px)] card"
        :selected-genres="core.selectedGenres.value"
        :selected-games="core.selectedGames.value"
        :visible-games="core.visibleGames.value"
        :selected-aesthetic-codes="core.selectedAestheticCodes.value"
        :selected-feature-codes="core.selectedFeatureCodes.value"
        :selected-pain-codes="core.selectedPainCodes.value"
        :aesthetic-codes="vm.aestheticCodes"
        :filtered-feature-groups="filteredFeatureGroupsValue"
        :filtered-pain-groups="filteredPainGroupsValue"
        :click-genre="vm.clickGenre"
        :click-game="vm.clickGame"
        :click-code="vm.clickCode"
        :chip-variant="vm.chipVariant"
        @update:feature-search="(v) => (vm.featureSearch.value = v)"
        @update:pain-search="(v) => (vm.painSearch.value = v)"
      />

      <!-- Middle: review list...displays the current page of reviews -->
      <DatasetExplorerReviewList
        :selected-rec-id="vm.selectedRecId.value"
        :rows="core.rows.value"
        :meta="core.meta.value"
        :loading="core.loading.value"
        :page-size="core.pageSize.value"
        :truncate="vm.truncate"
        :format-unix="vm.formatUnix"
        class="col-span-12 lg:col-span-5 h-[clamp(520px,120vh,760px)] card"
        @update:selected-rec-id="(v) => (vm.selectedRecId.value = v)"
      />

      <!-- Right: detail view for the selected review-->
      <DatasetExplorerReviewDetail
        class="col-span-12 lg:col-span-4 h-[clamp(520px,120vh,760px)] card"
        :selected-review="vm.selectedReview.value"
        :pretty-sentiment="core.prettySentiment"
        :format-unix="vm.formatUnix"
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
  --dex-seg-on-bg: rgba(15, 23, 42, 0.1);
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
  --dex-seg-off-text: rgba(241, 245, 249, 0.8);

  --dex-row-hover: rgba(148, 163, 184, 0.1);
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
