<!-- frontend/app/components/player-expectations-new/dashboard/TopVolumeBarChart.vue
represents "MOST EXTREMEM" aspects, so aspects that are only mentioned positive, regardless of volume
-->
<script setup lang="ts">
import { computed, ref } from 'vue'
import type { TopCodeRow } from '~/utils/playerExpectationsNewDashboard'
import { fmtInt, fmtFloat } from '~/utils/playerExpectationsNewDashboard'

const props = defineProps<{
  rows: TopCodeRow[]
  maxBars?: number
}>()

const BAR_W = 40
const GAP = 10
const LABEL_H = 112

// Plot geometry
const PLOT_H = 224 // px (h-56)
const PAD_TOP = 10
const PAD_BOT = 10
const INNER_H = PLOT_H - PAD_TOP - PAD_BOT

// widen axis gutter so 5–6 digits fit
const AXIS_W = 20

function clamp(x: number, lo: number, hi: number) {
  return Math.max(lo, Math.min(hi, x))
}

// Select the first N rows to display (default: 15)
const top = computed(() => {
  const xs = props.rows ?? []
  const n = props.maxBars ?? 15
  return xs.slice(0, n)
})

//heighest bar
const maxTotal = computed(() => {
  const m = Math.max(0, ...top.value.map((r) => Number(r.total ?? 0)))
  return m || 1
})

//count -> percentage
function barHeightPct(total: number) {
  return `${(clamp(total / maxTotal.value, 0, 1) * 100).toFixed(2)}%`
}

function segPct(part: number, total: number) {
  if (!total) return '0%'
  return `${(clamp(part / total, 0, 1) * 100).toFixed(2)}%`
}

// tooltip text for one bar
function tooltipText(r: TopCodeRow) {
  return [
    `${r.code_text} · ${r.code_int}`,
    `Mentions: ${fmtInt(r.total)}`,
    `Positive: ${fmtInt(r.positive)}`,
    `Neutral: ${fmtInt(r.neutral)}`,
    `Negative: ${fmtInt(r.negative)}`,
    `Missing: ${fmtInt(r.missing)}`,
    `Net: ${fmtFloat(r.net, 2)}`,
  ].join('\n')
}

type Tick = { frac: number; value: number; yPx: number; anchor: 'middle' | 'top' }
// Create 5 y-axis tick labels based on maxTotal
const ticks = computed<Tick[]>(() => {
  const m = maxTotal.value
  const fracs = [1, 0.75, 0.5, 0.25, 0]
  return fracs.map((f) => {
    const y = PAD_TOP + (1 - f) * INNER_H
    return {
      frac: f,
      value: Math.round(m * f),
      yPx: y,
      anchor: f === 0 ? 'top' : 'middle',
    }
  })
})

// Minimum width of the plot
const plotMinWidth = computed(() => {
  const n = top.value.length || (props.maxBars ?? 15)
  return Math.max(520, n * BAR_W + (n - 1) * GAP + 24)
})

// Custom tooltip (fixed)
const tip = ref({
  visible: false,
  x: 0,
  y: 0,
  text: '',
})

function showTip(e: MouseEvent, r: TopCodeRow) {
  tip.value.visible = true
  tip.value.text = tooltipText(r)
  moveTip(e)
}

function moveTip(e: MouseEvent) {
  tip.value.x = e.clientX + 12
  tip.value.y = e.clientY + 12
}

function hideTip() {
  tip.value.visible = false
}
</script>

<template>
  <div class="space-y-2">
    <!-- Sentiment legend -->
    <div class="flex flex-wrap gap-3 text-[11px] text-slate-500 dark:text-slate-400">
      <div class="inline-flex items-center gap-1.5">
        <span class="legend-dot" :style="{ backgroundColor: 'var(--ui-success)' }" />
        Positive
      </div>
      <div class="inline-flex items-center gap-1.5">
        <span class="legend-dot" :style="{ backgroundColor: 'var(--ui-info)' }" />
        Neutral
      </div>
      <div class="inline-flex items-center gap-1.5">
        <span class="legend-dot" :style="{ backgroundColor: 'var(--ui-error)' }" />
        Negative
      </div>
      <div class="inline-flex items-center gap-1.5">
        <span class="legend-dot" :style="{ backgroundColor: 'var(--ui-neutral)' }" />
        Missing
      </div>
    </div>

    <!-- Two columns:
     - Left: y-axis labels
     - Right: scrollable plot + x labels -->
    <div class="grid gap-3" :style="{ gridTemplateColumns: `${AXIS_W}px minmax(0, 1fr)` }">
      <!-- Y axis labels -->
      <div class="relative" :style="{ height: `${PLOT_H}px` }">
        <div
          v-for="t in ticks"
          :key="t.frac"
          class="axis-tick"
          :style="{
            top: `${t.yPx}px`,
            transform: t.anchor === 'middle' ? 'translateY(-50%)' : 'translateY(0)',
          }"
        >
          {{ fmtInt(t.value) }}
        </div>
      </div>

      <!-- Plot + labels -->
      <div class="min-w-0 overflow-x-auto">
        <div :style="{ minWidth: `${plotMinWidth}px` }">
          <!-- Plot area -->
          <div
            class="relative rounded-lg"
            :style="{
              height: `${PLOT_H}px`,
              paddingTop: `${PAD_TOP}px`,
              paddingBottom: `${PAD_BOT}px`,
              paddingLeft: '10px',
              paddingRight: '10px',
            }"
          >
            <!-- Gridlines -->
            <div class="absolute left-[10px] right-[10px] top-0 bottom-0 pointer-events-none">
              <div
                v-for="t in ticks"
                :key="`line-${t.frac}`"
                class="absolute left-0 right-0"
                :style="{ top: `${t.yPx}px` }"
              >
                <div class="h-px bg-slate-200/40 dark:bg-slate-800/50" />
              </div>
            </div>

            <!-- Bars -->
            <div class="relative h-full flex items-end" :style="{ gap: `${GAP}px` }">
              <div
                v-for="r in top"
                :key="`${r.coarse_category}-${r.code_int}`"
                :style="{ width: `${BAR_W}px` }"
                class="h-full flex items-end tv-bar-hit"
                @mouseenter="(e) => showTip(e, r)"
                @mousemove="moveTip"
                @mouseleave="hideTip"
              >
                <div
                  class="w-full rounded-md overflow-hidden border border-slate-200/30 dark:border-slate-800/40"
                  :style="{ height: barHeightPct(r.total) }"
                >
                  <div class="h-full w-full flex flex-col">
                    <div
                      class="w-full"
                      :style="{
                        height: segPct(r.positive, r.total),
                        backgroundColor: 'var(--ui-success)',
                        opacity: 0.85,
                      }"
                    />
                    <div
                      class="w-full"
                      :style="{
                        height: segPct(r.neutral, r.total),
                        backgroundColor: 'var(--ui-info)',
                        opacity: 0.70,
                      }"
                    />
                    <div
                      class="w-full"
                      :style="{
                        height: segPct(r.negative, r.total),
                        backgroundColor: 'var(--ui-error)',
                        opacity: 0.75,
                      }"
                    />
                    <div
                      class="w-full"
                      :style="{
                        height: segPct(r.missing, r.total),
                        backgroundColor: 'var(--ui-neutral)',
                        opacity: 0.55,
                      }"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- X labels, rotated vertically to fit -->
          <div class="mt-2 flex items-start px-[10px]" :style="{ gap: `${GAP}px` }">
            <div
              v-for="r in top"
              :key="`lbl-${r.coarse_category}-${r.code_int}`"
              class="flex items-start justify-center"
              :style="{ width: `${BAR_W}px`, height: `${LABEL_H}px` }"
            >
              <div class="x-vertical" :title="r.code_text">
                {{ r.code_text }}
              </div>
            </div>
          </div>

          <div class="mt-2 text-[11px] text-slate-500 dark:text-slate-400">
            X: top {{ top.length }} by net · Y: #mentions · Hover over a bar for more info.
          </div>
        </div>
      </div>
    </div>

    <!-- Custom tooltip -->
    <div v-if="tip.visible" class="tv-tip" :style="{ left: `${tip.x}px`, top: `${tip.y}px` }">
      <pre class="tv-tip-pre">{{ tip.text }}</pre>
    </div>
  </div>
</template>

<style scoped>
.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  display: inline-block;
  border: 1px solid rgba(15, 23, 42, 0.15);
}

.axis-tick {
  position: absolute;
  left: 0;
  right: 0;
  padding-right: 8px;
  text-align: right;
  font-size: 11px;
  color: rgba(148, 163, 184, 0.95);
}

.x-vertical {
  writing-mode: vertical-rl;
  transform: rotate(180deg);
  text-align: right;
  font-size: 11px;
  line-height: 1.05;
  color: rgba(148, 163, 184, 0.95);
  max-height: 112px;
  overflow: hidden;
}

/* Make the bar hit area consistent */
.tv-bar-hit {
  cursor: default;
}

/* Tooltip: fixed so it works inside scroll containers ... never blocks pointer */
.tv-tip {
  position: fixed;
  z-index: 9999;
  pointer-events: none;
  max-width: 380px;
  background: rgba(15, 23, 42, 0.92);
  color: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 10px;
  padding: 8px 10px;
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.35);
  white-space: pre-wrap;
}
.tv-tip-pre {
  margin: 0;
  font-size: 12px;
  line-height: 1.25;
  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji",
    "Segoe UI Emoji";
}
</style>
