<!-- frontend/app/components/player-expectations-new/dashboard/CodeHeatmapGrid.vue
renders a “heatmap” of codes for ONE dimension (aesthetics / features / pain)
ech box shows a code number, and its color represents net sentiment:
  red (-1) -> white (0) -> green (+1)
For features/pain it draws a parent/child grid (parents are x-axis columns, children go downward).
on hover, it shows a tooltip with code name, net value, and total mentions. -->
<script setup lang="ts">
import { computed, ref } from 'vue'
import type { CompareHeatmapCodes, DimensionKey, HeatmapCodeRow } from '~/utils/playerExpectationsNewDashboard'
import { fmtFloat, fmtInt } from '~/utils/playerExpectationsNewDashboard'

const props = defineProps<{
  title: string
  dimension: DimensionKey
  data: CompareHeatmapCodes | null
}>()

type Cell = HeatmapCodeRow | null

function clamp(x: number, lo: number, hi: number) {
  return Math.max(lo, Math.min(hi, x))
}

//mix() linearly interpolates between two RGB channel values.
function mix(a: number, b: number, t: number) {
  return Math.round(a + (b - a) * t)
}

// Convert a net sentiment value (-1..1) into an RGB background color string
function netToColor(net: number) {
  const n = clamp(Number.isFinite(net) ? net : 0, -1, 1)

  const red = { r: 220, g: 38, b: 38 } // red-600-ish
  const green = { r: 22, g: 163, b: 74 } // green-600-ish
  const white = { r: 255, g: 255, b: 255 }

  if (n === 0) return `rgb(${white.r} ${white.g} ${white.b})`

  if (n > 0) {
    // 0..1 : white -> green
    const t = n
    const r = mix(white.r, green.r, t)
    const g = mix(white.g, green.g, t)
    const b = mix(white.b, green.b, t)
    return `rgb(${r} ${g} ${b})`
  } else {
    // -1..0 : red -> white
    const t = n + 1 // -1->0, 0->1
    const r = mix(red.r, white.r, t)
    const g = mix(red.g, white.g, t)
    const b = mix(red.b, white.b, t)
    return `rgb(${r} ${g} ${b})`
  }
}

// Choose text color based on how strong the net value is (contrast)
function textColorForNet(net: number, total: number) {
  if (!total) return 'rgba(226, 232, 240, 0.9)'
  const n = Math.abs(clamp(Number.isFinite(net) ? net : 0, -1, 1))
  if (n < 0.35) return 'rgba(15, 23, 42, 0.92)'
  return 'rgba(255,255,255,0.94)'
}

function cellStyle(c: HeatmapCodeRow | null) {
  if (!c) return { backgroundColor: 'transparent' }

  if (!c.total) {
    return {
      backgroundColor: 'rgba(148, 163, 184, 0.12)',
      color: 'rgba(226, 232, 240, 0.85)',
      border: '1px solid rgba(148, 163, 184, 0.22)',
    }
  }

  return {
    backgroundColor: netToColor(c.net),
    color: textColorForNet(c.net, c.total),
    border: '1px solid rgba(0,0,0,0.08)',
  }
}

function tooltipText(c: HeatmapCodeRow) {
  // multi-line tooltip
  return `${c.code_text} · ${c.code_int}\nnet ${fmtFloat(c.net, 2)} · n=${fmtInt(c.total)}`
}

const byCode = computed(() => {
  const m = new Map<number, HeatmapCodeRow>()
  for (const r of props.data?.rows ?? []) m.set(r.code_int, r)
  return m
})

//Aesthetics: single row sorted by code_int
const aestheticsRow = computed<Cell[]>(() => {
  if (props.dimension !== 'aesthetics') return []
  const codes = (props.data?.rows ?? []).map((r) => r.code_int).sort((a, b) => a - b)
  return codes.map((c) => byCode.value.get(c) ?? null)
})

/**
 * Hierarchical grid for features/pain:
 * Columns = parents (code%10==0), Rows = parent row + child rows...so 810 is also tope code but better since it shortens the height
 */
const hier = computed(() => {
  if (props.dimension === 'aesthetics') {
    return { parents: [] as number[], grid: [] as Cell[][] }
  }

  const rows = props.data?.rows ?? []
  const codes = rows.map((r) => r.code_int).sort((a, b) => a - b)

  const parents = codes.filter((c) => c >= 10 && c % 10 === 0)

  const childrenByParent = new Map<number, number[]>()
  for (const c of codes) {
    if (c < 10) continue
    const parent = Math.floor(c / 10) * 10
    if (!childrenByParent.has(parent)) childrenByParent.set(parent, [])
    if (c !== parent) childrenByParent.get(parent)!.push(c)
  }
  for (const [p, xs] of childrenByParent.entries()) {
    xs.sort((a, b) => a - b)
    childrenByParent.set(p, xs)
  }

  const maxDepth = Math.max(0, ...parents.map((p) => (childrenByParent.get(p)?.length ?? 0)))

  // Build a 2D grid:
  const grid: Cell[][] = []
  grid.push(parents.map((p) => byCode.value.get(p) ?? null))
  for (let i = 0; i < maxDepth; i++) {
    grid.push(
      parents.map((p) => {
        const child = childrenByParent.get(p)?.[i]
        return child ? byCode.value.get(child) ?? null : null
      })
    )
  }

  return { parents, grid }
})

function cellKey(c: Cell, ri: number, ci: number) {
  return c ? `${props.dimension}-code-${c.code_int}` : `${props.dimension}-empty-${ri}-${ci}`
}

//custom tool tip
const tip = ref({
  visible: false,
  x: 0,
  y: 0,
  text: '',
})

function showTip(e: MouseEvent, c: HeatmapCodeRow) {
  tip.value.visible = true
  tip.value.text = tooltipText(c)
  moveTip(e)
}

function moveTip(e: MouseEvent) {
  // keep it offset from cursor
  tip.value.x = e.clientX + 12
  tip.value.y = e.clientY + 12
}

function hideTip() {
  tip.value.visible = false
}
</script>

<template>
  <UCard class="relative">
    <div class="flex items-center justify-between gap-3">
      <div class="font-semibold">{{ title }}</div>
      <div class="text-xs text-slate-500 dark:text-slate-400">Heatmap by net (−1 → +1)</div>
    </div>

    <!-- Placeholder when data not loaded -->
    <div v-if="!data" class="text-sm text-slate-500 dark:text-slate-400 mt-2">—</div>

    <!-- Aesthetics -->
    <div v-else-if="dimension === 'aesthetics'" class="mt-3">
      <div class="flex flex-wrap gap-2">
        <template v-for="(c, i) in aestheticsRow" :key="cellKey(c, 0, i)">
          <div
            v-if="c"
            class="hm-cell"
            :style="cellStyle(c)"
            @mouseenter="(e) => showTip(e, c)"
            @mousemove="moveTip"
            @mouseleave="hideTip"
          >
            <span>{{ c.code_int }}</span>
          </div>

          <div v-else class="hm-cell hm-cell--empty" :style="cellStyle(null)" />
        </template>
      </div>
    </div>

    <!-- Features/Pain -->
    <div v-else class="mt-3 overflow-x-auto">
      <div class="inline-flex flex-col gap-2">
        <div v-for="(row, ri) in hier.grid" :key="`${dimension}-row-${ri}`" class="flex gap-2">
          <template v-for="(c, ci) in row" :key="cellKey(c, ri, ci)">
            <div
              v-if="c"
              class="hm-cell"
              :style="cellStyle(c)"
              @mouseenter="(e) => showTip(e, c)"
              @mousemove="moveTip"
              @mouseleave="hideTip"
            >
              <span>{{ c.code_int }}</span>
            </div>

            <div v-else class="hm-cell hm-cell--empty" :style="cellStyle(null)" />
          </template>
        </div>
      </div>
    </div>

    <div class="mt-3 text-[11px] text-slate-500 dark:text-slate-400">Hover over a box to see category name and net.</div>

    <!-- Custom tooltip -->
    <div
      v-if="tip.visible"
      class="hm-tip"
      :style="{ left: `${tip.x}px`, top: `${tip.y}px` }"
    >
      <pre class="hm-tip-pre">{{ tip.text }}</pre>
    </div>
  </UCard>
</template>

<style scoped>
.hm-cell {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.78rem;
  font-weight: 600;
  user-select: none;
  cursor: default;
}
.hm-cell--empty {
  background: transparent !important;
  border: 1px dashed rgba(148, 163, 184, 0.22);
}

/* Tooltip: fix */
.hm-tip {
  position: fixed;
  z-index: 9999;
  pointer-events: none;
  max-width: 360px;
  background: rgba(15, 23, 42, 0.92);
  color: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 10px;
  padding: 8px 10px;
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.35);
  white-space: pre-wrap;
}
.hm-tip-pre {
  margin: 0;
  font-size: 12px;
  line-height: 1.25;
  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji",
    "Segoe UI Emoji";
}
</style>
