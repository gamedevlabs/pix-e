<!-- frontend/app/components/playerExpectationsNewDatasetExplorer/DatasetExplorerReviewList.vue -->
<script setup lang="ts">
/**
 * WHAT THIS COMPONENT IS
 *
 * This component shows the middle column: a scrollable list of reviews.
 *
 * receives plain values (rows/meta/loading/pageSize/selectedRecId)
 * emits update:selected-rec-id so parent can v-model bind without prop mutation
 *
 * It does NOT fetch data. It only displays what it is given
 * When you click a review row, it sets selectedRecId.value,
 * and the detail panel (DatasetExplorerReviewDetail) can then show that selected review.
 */
import type { ReviewRow } from '~/composables/usePlayerExpectationsNewDatasetExplorer'

//We only use page and total_pages here for display
type Meta = {
  page: number
  page_size: number
  total: number
  total_pages: number
}

//declares what this component expects from its parent.
const props = defineProps<{
  rows: ReviewRow[]
  meta: Meta | null
  loading: boolean
  pageSize: number
  selectedRecId: string | null
  truncate: (text: string, n?: number) => string
  formatUnix: (ts: number) => string
}>()

type Emits = {
  'update:selectedRecId': [string | null]
}

const emit = defineEmits<Emits>()

function selectRec(id: string) {
  emit('update:selectedRecId', id)
}
</script>

<template>
  <div>
    <!-- Header bar -->
    <div class="card-header flex items-center justify-between">
      <!-- show current page size -->
      <h3 class="font-semibold">Review List ({{ pageSize }} per page)</h3>
      <div v-if="meta" class="text-xs text-slate-500 dark:text-slate-400">
        Page {{ meta.page }} / {{ meta.total_pages }}
      </div>
    </div>

    <!-- Scrollable list container -->
    <div class="card-scroll p-0">
      <div class="divide-y divide-slate-200 dark:divide-slate-800">
        <button
          v-for="r in rows"
          :key="r.recommendation_id"
          type="button"
          class="review-row"
          :class="selectedRecId === r.recommendation_id ? 'review-row--selected' : ''"
          @click="selectRec(r.recommendation_id)">
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

          <div class="text-sm text-slate-700 dark:text-slate-200 mt-2 line-clamp-3">
            {{ truncate(r.review_text_en) }}
          </div>

          <div class="text-xs text-slate-500 dark:text-slate-400 mt-2 font-mono">
            {{ r.recommendation_id }}
          </div>
        </button>

        <!-- Loading / empty states -->
        <div v-if="loading" class="p-3 text-sm text-slate-500 dark:text-slate-400">Loading…</div>
        <div v-if="!loading && rows.length === 0" class="p-3 text-sm text-slate-500 dark:text-slate-400">
          No results (try relaxing filters).
        </div>
      </div>
    </div>
  </div>
</template>
