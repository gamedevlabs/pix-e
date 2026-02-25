<!-- frontend/app/components/player-expectations-new/dashboard/KpiRow.vue -->
<script setup lang="ts">
import type { CompareKpis } from '~/utils/playerExpectationsNewDashboard'
import { fmtFloat, fmtInt, pct } from '~/utils/playerExpectationsNewDashboard'

defineProps<{ kpis: CompareKpis | null }>()
</script>

<template>
  <!-- 4 small KPI cards: 2 columns on mobile, 4 columns on medium+ screens -->
  <div class="grid grid-cols-2 md:grid-cols-4 gap-2">
    <UCard>
      <div class="text-xs text-slate-500 dark:text-slate-400">Reviews</div>
      <div class="text-lg font-semibold">{{ kpis ? fmtInt(kpis.reviews) : '—' }}</div>
    </UCard>

    <UCard>
      <div class="text-xs text-slate-500 dark:text-slate-400">Rec. rate</div>
      <div class="text-lg font-semibold">{{ kpis ? pct(kpis.recommended_rate, 1) : '—' }}</div>
    </UCard>

    <UCard>
      <div class="text-xs text-slate-500 dark:text-slate-400">Total mentions</div>
      <div class="text-lg font-semibold">{{ kpis ? fmtInt(kpis.mentions_total) : '—' }}</div>
    </UCard>

    <UCard>
      <div class="text-xs text-slate-500 dark:text-slate-400">Mentions / review</div>
      <div class="text-lg font-semibold">{{ kpis ? fmtFloat(kpis.mentions_per_review, 2) : '—' }}</div>
    </UCard>
  </div>
</template>
