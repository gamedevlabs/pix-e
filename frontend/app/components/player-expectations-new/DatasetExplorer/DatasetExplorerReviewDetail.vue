<!-- frontend/app/components/playerExpectationsNewDatasetExplorer/DatasetExplorerReviewDetail.vue -->
<script setup lang="ts">
/**
 * WHAT THIS COMPONENT IS
 *
 * This is the RIGHT panel: it shows details for the currently selected review.
 */
import type { Ref } from 'vue'
import type { ReviewRow } from '~/composables/usePlayerExpectationsNewDatasetExplorer'

//what we need from the parent
defineProps<{
  selectedReview: Ref<ReviewRow | null>
  prettySentiment: (s: string | null) => string
  formatUnix: (ts: number) => string
  highlightReviewHtml: (reviewText: string, quotes: string[]) => string
}>()
</script>

<template>
  <div>
    <!-- Header -->
    <div class="card-header">
      <h3 class="font-semibold">Review Detail</h3>
    </div>

    <!-- Scrollable content -->
    <div class="card-scroll">
      <!-- Empty state: no selection -->
      <div v-if="!selectedReview.value" class="text-sm text-slate-600 dark:text-slate-300">
        Select a review from the list to see details.
      </div>

      <!-- Detail state: a review is selected -->
      <div v-else class="space-y-4">
        <div>
          <div class="flex items-start justify-between gap-3">
            <div>
              <div class="text-lg font-semibold">{{ selectedReview.value.game_name }}</div>
              <div class="text-xs text-slate-500 dark:text-slate-400 mt-1 font-mono">
                {{ selectedReview.value.recommendation_id }}
              </div>
            </div>

            <UBadge :color="selectedReview.value.voted_up === 1 ? 'success' : 'error'" variant="soft">
              {{ selectedReview.value.voted_up === 1 ? 'Recommended' : 'Not recommended' }}
            </UBadge>
          </div>

          <div class="text-xs text-slate-500 dark:text-slate-400 mt-2">
            {{ formatUnix(selectedReview.value.timestamp_created) }}
            • 👍 {{ selectedReview.value.votes_up }}
            • 😂 {{ selectedReview.value.votes_funny }}
            • playtime: {{ selectedReview.value.playtime_at_review }} → {{ selectedReview.value.playtime_forever }}
          </div>
        </div>

        <!-- Review text with highlighted quote snippets -->
        <div>
          <div class="font-medium mb-2">Review text (highlighted quotes)</div>
          <div
            class="text-sm leading-relaxed text-slate-800 dark:text-slate-100 whitespace-pre-wrap"
            v-html="
              highlightReviewHtml(
                selectedReview.value.review_text_en,
                (selectedReview.value.quotes || []).map((qq) => qq.quote_text)
              )
            "
          />
        </div>

        <!-- Extracted quotes and their code->sentiment pairs -->
        <div>
          <div class="font-medium mb-2">Extracted Quotes (true pairs only)</div>

          <!-- If the backend returned no quotes for this review -->
          <div v-if="!selectedReview.value.quotes?.length" class="text-sm text-slate-500 dark:text-slate-400">
            No extracted quote → code → sentiment pairs for this review.
          </div>

          <!-- Otherwise show each quote block -->
          <div v-else class="space-y-3">
            <div
              v-for="qRow in selectedReview.value.quotes"
              :key="qRow.quote_id"
              class="border rounded p-3 border-slate-200 dark:border-slate-800"
            >
              <div class="flex items-center justify-between gap-2 mb-2">
                <UBadge size="xs" variant="soft">
                  {{ qRow.coarse_category }}
                </UBadge>
                <span class="text-xs text-slate-500 dark:text-slate-400">quote_id {{ qRow.quote_id }}</span>
              </div>

              <div class="text-sm text-slate-800 dark:text-slate-100">
                {{ qRow.quote_text }}
              </div>

              <div class="mt-3 flex flex-col gap-2">
                <div
                  v-for="c in qRow.codes"
                  :key="`${c.coarse_category}-${c.code_int}`"
                  class="flex flex-wrap gap-2 items-center"
                >
                  <UBadge size="xs" variant="soft">
                    {{ c.code_int }} — {{ c.code_text }}
                  </UBadge>

                  <UBadge size="xs" variant="outline"> sentiment: {{ prettySentiment(c.sentiment_v2) }} </UBadge>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>
