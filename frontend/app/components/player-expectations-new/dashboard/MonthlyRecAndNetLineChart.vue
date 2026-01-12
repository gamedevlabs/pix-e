<!-- frontend/app/components/player-expectations-new/dashboard/MonthlyRecAndNetLineChart.vue
draws a simple line chart over time (by month).
it shows TWO lines at once:
    1) Recommendation rate (0..1) on the left axis
    2) Net sentiment (-1..1) on the right axis
chart scrolls horizontally -->
<script setup lang="ts">
import { computed } from 'vue'
import type { CompareTimeseries } from '~/utils/playerExpectationsNewDashboard'
import { pct, fmtFloat } from '~/utils/playerExpectationsNewDashboard'

const props = withDefaults(
  defineProps<{
    title?: string
    data?: CompareTimeseries | null
  }>(),
  {
    title: 'Timeline - Recommendation Rate vs. Net Sentiment (Monthly Average)',
    data: null,
  }
)

// Small helper: keep numbers inside a range (prevents layout issues)
function clamp(x: number, lo: number, hi: number) {
  return Math.max(lo, Math.min(hi, x))
}


type Point = {
  month: string
  rec: number // 0..1
  net: number // -1..1
}

//net sentiment calculation logic
//Net sentiment is computed from mentions: net = (positive - negative) / total_mentions
const points = computed<Point[]>(() => {
  const xs = props.data?.data ?? []
  return xs
    .map((p) => {
      const pos = Number(p.mentions?.positive ?? 0)
      const neu = Number(p.mentions?.neutral ?? 0)
      const neg = Number(p.mentions?.negative ?? 0)
      const miss = Number(p.mentions?.missing ?? 0)
      const total = pos + neu + neg + miss
      const net = total ? (pos - neg) / total : 0
      const rec = clamp(Number(p.recommended_rate ?? 0), 0, 1)
      return { month: String(p.month ?? ''), rec, net: clamp(net, -1, 1) }
    })
    .filter((p) => !!p.month)
})


/**
 * layout constants.
 * H is the total height.
 * P_* are paddings so we have space for axis labels.
 */
const H = 290
const P_T = 16
const P_B = 66 // extra room for labels
const P_L = 56
const P_R = 56
const INNER_H = H - P_T - P_B

// Horizontal spacing per month, and a minimum chart width.
// If there are many months, W grows and the container scrolls.
const STEP_X = 28
const MIN_W = 720

// Chart width depends on number of points (at least MIN_W)
const W = computed(() => {
  const n = points.value.length
  return Math.max(MIN_W, P_L + P_R + Math.max(1, n - 1) * STEP_X)
})

// Convert a point index (0..n-1) into an x position in the SVG
function xAt(i: number) {
  return P_L + i * STEP_X
}

// Map recommendation rate (0..1) to a y coordinate
function yRec(rec: number) {
  const t = clamp(rec, 0, 1)
  return P_T + (1 - t) * INNER_H
}

// Map net sentiment (-1..1) to a y coordinate
function yNet(net: number) {
  const t = (clamp(net, -1, 1) + 1) / 2
  return P_T + (1 - t) * INNER_H
}

//Convert a numeric series
function pathFor(series: number[], yFn: (v: number) => number) {
  const first = series[0]
  if (first === undefined) return ''

  let d = `M ${xAt(0)} ${yFn(first)}`
  for (let i = 1; i < series.length; i++) {
    const v = series[i]
    if (v === undefined) continue
    d += ` L ${xAt(i)} ${yFn(v)}`
  }
  return d
}

const recSeries = computed(() => points.value.map((p) => p.rec))
const netSeries = computed(() => points.value.map((p) => p.net))

const pathRec = computed(() => pathFor(recSeries.value, yRec))
const pathNet = computed(() => pathFor(netSeries.value, yNet))

// Tick marks for the left axis (recommendation rate)
const recTicks = computed(() => [
  { v: 1, y: yRec(1) },
  { v: 0.5, y: yRec(0.5) },
  { v: 0, y: yRec(0) },
])

// Tick marks for the right axis (net sentiment)
const netTicks = computed(() => [
  { v: 1, y: yNet(1) },
  { v: 0, y: yNet(0) },
  { v: -1, y: yNet(-1) },
])


function parseMonthKey(m: string): { yyyy: number; mm: number } | null {
  // expected "YYYY-MM"
  const s = (m || '').trim()
  const match = /^(\d{4})-(\d{2})$/.exec(s)
  if (!match) return null
  const yyyy = Number(match[1])
  const mm = Number(match[2])
  if (!Number.isFinite(yyyy) || !Number.isFinite(mm) || mm < 1 || mm > 12) return null
  return { yyyy, mm }
}
// Turn "YYYY-MM" into a short label like "01/25"
function monthLabel(m: string): string {
  const parsed = parseMonthKey(m)
  if (!parsed) return m
  const mm = String(parsed.mm).padStart(2, '0')
  const yy = String(parsed.yyyy).slice(-2)
  return `${mm}/${yy}` // e.g. 01/25
}

// Decide which x-axis ticks get labels...decided to do every second +  last and first
const xTicks = computed(() => {
  const xs = points.value
  const n = xs.length
  return xs.map((p, i) => {
    const major = i === 0 || i === n - 1 || i % 2 === 0
    return {
      i,
      month: p.month,
      label: monthLabel(p.month),
      major,
    }
  })
})

// y position of the x-axis baseline
const AXIS_Y = computed(() => H - P_B)
</script>

<template>
  <UCard>
    <div class="flex items-center justify-between gap-4">
      <div class="font-semibold">{{ title }}</div>

      <div class="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
        <div class="inline-flex items-center gap-1.5">
          <span class="dot" :style="{ backgroundColor: 'var(--ui-primary)' }" />
          Rec.
        </div>
        <div class="inline-flex items-center gap-1.5">
          <span class="dot" :style="{ backgroundColor: 'var(--ui-secondary)' }" />
          Sentiment
        </div>
      </div>
    </div>

    <div v-if="!points.length" class="text-sm text-slate-500 dark:text-slate-400 mt-2">—</div>

    <div v-else class="mt-3 overflow-x-auto">
      <svg :width="W" :height="H" class="block">
        <!-- horizontal gridlines -->
        <g>
          <line
            v-for="t in recTicks"
            :key="`grid-${t.v}`"
            :x1="P_L"
            :x2="W - P_R"
            :y1="t.y"
            :y2="t.y"
            stroke="rgba(148,163,184,0.22)"
            stroke-width="1"
          />
        </g>

        <!-- left axis: rec% -->
        <g>
          <text
            v-for="t in recTicks"
            :key="`l-${t.v}`"
            :x="P_L - 8"
            :y="t.y"
            text-anchor="end"
            dominant-baseline="middle"
            fill="rgba(148,163,184,0.95)"
            font-size="11"
          >
            {{ pct(t.v, 0) }}
          </text>
        </g>

        <!-- right axis: net -->
        <g>
          <text
            v-for="t in netTicks"
            :key="`r-${t.v}`"
            :x="W - P_R + 8"
            :y="t.y"
            text-anchor="start"
            dominant-baseline="middle"
            fill="rgba(148,163,184,0.95)"
            font-size="11"
          >
            {{ fmtFloat(t.v, 1) }}
          </text>
        </g>

        <!-- y-axis lines ..left adn right -->
        <line :x1="P_L" :x2="P_L" :y1="P_T" :y2="AXIS_Y" stroke="rgba(148,163,184,0.25)" />
        <line :x1="W - P_R" :x2="W - P_R" :y1="P_T" :y2="AXIS_Y" stroke="rgba(148,163,184,0.25)" />

        <!-- x-axis baseline -->
        <line :x1="P_L" :x2="W - P_R" :y1="AXIS_Y" :y2="AXIS_Y" stroke="rgba(148,163,184,0.25)" />

        <!-- x-axis ticks (minor + major) + labels on major ticks -->
        <g v-for="t in xTicks" :key="`xt-${t.month}-${t.i}`">
          <!-- tick line -->
          <line
            :x1="xAt(t.i)"
            :x2="xAt(t.i)"
            :y1="AXIS_Y"
            :y2="AXIS_Y + (t.major ? 10 : 6)"
            stroke="rgba(148,163,184,0.35)"
            stroke-width="1"
          >
            <!-- Tooltip on hover -->
            <title>{{ t.label }}</title>
          </line>

          <!-- label -->
          <text
            v-if="t.major"
            :x="xAt(t.i)"
            :y="AXIS_Y + 18"
            text-anchor="middle"
            dominant-baseline="hanging"
            fill="rgba(148,163,184,0.95)"
            font-size="11"
          >
            {{ t.label }}
          </text>
        </g>

        <!-- series -->
        <path :d="pathRec" fill="none" stroke="var(--ui-primary)" stroke-width="2.4" opacity="0.92" />
        <path :d="pathNet" fill="none" stroke="var(--ui-secondary)" stroke-width="2.4" opacity="0.92" />

        <!-- points with tooltips -->
        <g v-for="(p, i) in points" :key="`pt-${p.month}-${i}`">
          <circle :cx="xAt(i)" :cy="yRec(p.rec)" r="2.6" fill="var(--ui-primary)">
            <title>{{ monthLabel(p.month) }} — Rec. rate: {{ pct(p.rec, 1) }}</title>
          </circle>
          <circle :cx="xAt(i)" :cy="yNet(p.net)" r="2.6" fill="var(--ui-secondary)">
            <title>{{ monthLabel(p.month) }} — Net: {{ fmtFloat(p.net, 2) }}</title>
          </circle>
        </g>
      </svg>
    </div>

    <!-- Small caption explaining the two axes -->
    <div class="mt-2 text-[11px] text-slate-500 dark:text-slate-400">
      Left axis = recommendation rate. Right axis = net sentiment (pos−neg)/all mentions.
    </div>
  </UCard>
</template>

<style scoped>
.dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  display: inline-block;
  border: 1px solid rgba(15, 23, 42, 0.15);
}
</style>
