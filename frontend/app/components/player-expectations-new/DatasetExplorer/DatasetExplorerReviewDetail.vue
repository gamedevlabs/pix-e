<!-- frontend/app/components/playerExpectationsNewDatasetExplorer/DatasetExplorerReviewDetail.vue -->
<script setup lang="ts">
/**
 * WHAT THIS COMPONENT IS
 *
 * This is the RIGHT panel: it shows details for the currently selected review.
 *
 *  No v-html (avoids vue/no-v-html XSS lint).
 */
import { computed } from 'vue'
import type { ReviewRow } from '~/composables/usePlayerExpectationsNewDatasetExplorer'

type Segment = { text: string; highlight: boolean }
type Interval = { start: number; end: number } // [start, end)

//what we need from the parent
const props = defineProps<{
  selectedReview: ReviewRow | null
  prettySentiment: (s: string | null) => string
  formatUnix: (ts: number) => string
}>()

function findAllIntervals(text: string, needle: string): Interval[] {
  const out: Interval[] = []
  if (!needle) return out
  let i = 0
  while (i < text.length) {
    const j = text.indexOf(needle, i)
    if (j === -1) break
    out.push({ start: j, end: j + needle.length })
    i = j + needle.length
  }
  return out
}

function mergeIntervals(xs: Interval[]): Interval[] {
  if (xs.length === 0) return []

  const sorted = [...xs].sort((a, b) => a.start - b.start || a.end - b.end)
  const first = sorted[0]
  if (!first) return []

  const merged: Interval[] = []
  let cur: Interval = { start: first.start, end: first.end }

  for (let k = 1; k < sorted.length; k++) {
    const next = sorted[k]
    if (!next) continue

    if (next.start <= cur.end) {
      cur.end = Math.max(cur.end, next.end)
    } else {
      merged.push(cur)
      cur = { start: next.start, end: next.end }
    }
  }

  merged.push(cur)
  return merged
}

function buildSegments(text: string, intervals: Interval[]): Segment[] {
  if (intervals.length === 0) return [{ text, highlight: false }]
  const segs: Segment[] = []
  let pos = 0

  for (const it of intervals) {
    if (it.start > pos) segs.push({ text: text.slice(pos, it.start), highlight: false })
    segs.push({ text: text.slice(it.start, it.end), highlight: true })
    pos = it.end
  }

  if (pos < text.length) segs.push({ text: text.slice(pos), highlight: false })
  return segs
}

const highlightedSegments = computed<Segment[]>(() => {
  const r = props.selectedReview
  if (!r) return []
  const text = r.review_text_en ?? ''
  const quotes = (r.quotes ?? []).map((q) => q.quote_text).filter((s) => s.trim().length > 0)

  // gather all occurrences for all quotes
  const all: Interval[] = []
  for (const qt of quotes) all.push(...findAllIntervals(text, qt))

  // merge overlaps (multiple quotes can overlap / be adjacent)
  const merged = mergeIntervals(all)
  return buildSegments(text, merged)
})
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
      <div v-if="!selectedReview" class="text-sm text-slate-600 dark:text-slate-300">
        Select a review from the list to see details.
      </div>

      <!-- Detail state: a review is selected -->
      <div v-else class="space-y-4">
        <div>
          <div class="flex items-start justify-between gap-3">
            <div>
              <div class="text-lg font-semibold">{{ selectedReview.game_name }}</div>
              <div class="text-xs text-slate-500 dark:text-slate-400 mt-1 font-mono">
                {{ selectedReview.recommendation_id }}
              </div>
            </div>

            <UBadge :color="selectedReview.voted_up === 1 ? 'success' : 'error'" variant="soft">
              {{ selectedReview.voted_up === 1 ? 'Recommended' : 'Not recommended' }}
            </UBadge>
          </div>

          <div class="text-xs text-slate-500 dark:text-slate-400 mt-2">
            {{ formatUnix(selectedReview.timestamp_created) }}
            • 👍 {{ selectedReview.votes_up }} • 😂 {{ selectedReview.votes_funny }} • playtime:
            {{ selectedReview.playtime_at_review }} → {{ selectedReview.playtime_forever }}
          </div>
        </div>

        <!-- Review text with highlighted quote snippets -->
        <div>
          <div class="font-medium mb-2">Review text (highlighted quotes)</div>
          <div
            class="text-sm leading-relaxed text-slate-800 dark:text-slate-100 whitespace-pre-wrap"
          >
            <template v-for="(seg, i) in highlightedSegments" :key="i">
              <mark v-if="seg.highlight" class="rounded px-0.5">
                {{ seg.text }}
              </mark>
              <span v-else>{{ seg.text }}</span>
            </template>
          </div>
        </div>

        <!-- Extracted quotes and their code->sentiment pairs -->
        <div>
          <div class="font-medium mb-2">Extracted Quotes (true pairs only)</div>

          <!-- If the backend returned no quotes for this review -->
          <div
            v-if="!selectedReview.quotes?.length"
            class="text-sm text-slate-500 dark:text-slate-400"
          >
            No extracted quote → code → sentiment pairs for this review.
          </div>

          <!-- Otherwise show each quote block -->
          <div v-else class="space-y-3">
            <div
              v-for="qRow in selectedReview.quotes"
              :key="qRow.quote_id"
              class="border rounded p-3 border-slate-200 dark:border-slate-800"
            >
              <div class="flex items-center justify-between gap-2 mb-2">
                <UBadge size="xs" variant="soft">
                  {{ qRow.coarse_category }}
                </UBadge>
                <span class="text-xs text-slate-500 dark:text-slate-400"
                  >quote_id {{ qRow.quote_id }}</span
                >
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
                  <UBadge size="xs" variant="soft"> {{ c.code_int }} — {{ c.code_text }} </UBadge>

                  <UBadge size="xs" variant="outline">
                    sentiment: {{ prettySentiment(c.sentiment_v2) }}
                  </UBadge>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
