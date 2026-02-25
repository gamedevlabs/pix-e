<!-- frontend/app/components/player-expectations-new/dashboard/SentimentBar.vue
Shows a simple “stacked bar” of sentiment shares (positive/neutral/negative/missing).
Also shows the exact percentages as text below the bar.-->
<script setup lang="ts">
import { computed } from 'vue'
import type { CompareSentiments } from '~/utils/playerExpectationsNewDashboard'
import { pct } from '~/utils/playerExpectationsNewDashboard'

const props = defineProps<{ data: CompareSentiments | null }>()

// The backend provides shares as values between 0 and 1.
const shares = computed(() => props.data?.shares ?? { positive: 0, neutral: 0, negative: 0, missing: 0 })

// Convert a 0..1 share into a CSS width string like "42.00%".
function widthPct(x: number) {
  const v = Number.isFinite(x) ? x : 0
  const clamped = Math.max(0, Math.min(1, v))
  return `${(clamped * 100).toFixed(2)}%`
}
</script>

<template>
  <UCard>
    <!-- Header: title + total mention count -->
    <div class="flex items-center justify-between">
      <div class="font-semibold">Sentiment distribution</div>
      <div class="text-xs text-slate-500 dark:text-slate-400">
        {{ data ? data.total.toLocaleString() : '—' }} mentions
      </div>
    </div>

    <!-- color and width based on the sentument-->
    <div class="mt-3 h-3 w-full rounded overflow-hidden flex bg-slate-200 dark:bg-slate-800">
      <div class="h-full opacity-75" :style="{ width: widthPct(shares.positive), backgroundColor: 'var(--ui-success)' }" />
      <div class="h-full opacity-65" :style="{ width: widthPct(shares.neutral), backgroundColor: 'var(--ui-info)' }" />
      <div class="h-full opacity-65" :style="{ width: widthPct(shares.negative), backgroundColor: 'var(--ui-error)' }" />
      <div class="h-full opacity-50" :style="{ width: widthPct(shares.missing), backgroundColor: 'var(--ui-neutral)' }" />
    </div>

    <!-- labels with formatted percentage-->
    <div class="mt-2 grid grid-cols-2 gap-2 text-xs text-slate-600 dark:text-slate-300">
      <div>Positive: {{ pct(shares.positive, 1) }}</div>
      <div>Neutral: {{ pct(shares.neutral, 1) }}</div>
      <div>Negative: {{ pct(shares.negative, 1) }}</div>
      <div>Missing: {{ pct(shares.missing, 1) }}</div>
    </div>
  </UCard>
</template>
