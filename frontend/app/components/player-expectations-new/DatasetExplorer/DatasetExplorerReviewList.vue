<!-- frontend/app/components/playerExpectationsNewDatasetExplorer/DatasetExplorerReviewList.vue -->
<script setup lang="ts">
/**
 * WHAT THIS COMPONENT IS
 *
 * This component shows the middle column: a scrollable list of reviews.
 *
 * It receives:
 * - rows: the current page of reviews (as a ref)
 * - selectedRecId: which review is currently selected (as a ref)
 * - helper functions for display (truncate, formatUnix)
 *
 * It does NOT fetch data. It only displays what it is given
 * When you click a review row, it sets selectedRecId.value,
 * and the detail panel (DatasetExplorerReviewDetail) can then show that selected review.
 */
import type { Ref } from 'vue'
import type { ReviewRow } from '~/composables/usePlayerExpectationsNewDatasetExplorer'

//We only use page and total_pages here for display
type Meta = {
  page: number
  page_size: number
  total: number
  total_pages: number
}

//declares what this component expects from its parent.
defineProps<{
  rows: Ref<ReviewRow[]>
  meta: Ref<Meta | null>
  loading: Ref<boolean>
  pageSize: Ref<number>

  selectedRecId: Ref<string | null>

  truncate: (text: string, n?: number) => string
  formatUnix: (ts: number) => string
}>()
</script>

<template>
  <div>
    <!-- Header bar -->
    <div class="card-header flex items-center justify-between">
      <!-- show current page size -->
      <h3 class="font-semibold">Review List ({{ pageSize.value }} per page)</h3>
      <div class="text-xs text-slate-500 dark:text-slate-400" v-if="meta.value">
        Page {{ meta.value.page }} / {{ meta.value.total_pages }}
      </div>
    </div>

    <!-- Scrollable list container -->
    <div class="card-scroll p-0">
      <div class="divide-y divide-slate-200 dark:divide-slate-800">
        <button
          v-for="r in rows.value"
          :key="r.recommendation_id"
          type="button"
          class="review-row"
          :class="selectedRecId.value === r.recommendation_id ? 'review-row--selected' : ''"
          @click="selectedRecId.value = r.recommendation_id"
        >
          <div class="flex items-center justify-between gap-2">
            <div class="font-medium truncate">
              {{ r.game_name }}
            </div>

            <UBadge size="xs" :color="r.voted_up === 1 ? 'success' : 'error'" variant="soft">
              {{ r.voted_up === 1 ? 'Recommended' : 'Not recommended' }}
            </UBadge>
          </div>

          <div class="text-xs text-slate-500 dark:text-slate-400 mt-1">
            {{ formatUnix(r.timestamp_created) }} • 👍 {{ r.votes_up }} • 😂 {{ r.votes_funny }}
          </div>

          <!-- Row preview: shortened review text -->
          <div class="text-sm text-slate-700 dark:text-slate-200 mt-2 line-clamp-3">
            {{ truncate(r.review_text_en) }}
          </div>

          <div class="text-xs text-slate-500 dark:text-slate-400 mt-2 font-mono">
            {{ r.recommendation_id }}
          </div>
        </button>

        <!-- Loading / empty states -->
        <div v-if="loading.value" class="p-3 text-sm text-slate-500 dark:text-slate-400">Loading…</div>
        <div v-if="!loading.value && rows.value.length === 0" class="p-3 text-sm text-slate-500 dark:text-slate-400">
          No results (try relaxing filters).
        </div>
      </div>
    </div>
  </div>
</template>
