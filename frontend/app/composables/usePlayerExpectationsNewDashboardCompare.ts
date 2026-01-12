// frontend/app/composables/usePlayerExpectationsNewDashboardCompare.ts
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import type {
  CompareHeatmapCodes,
  CompareKpis,
  CompareScope,
  CompareSentiments,
  CompareTopCodes,
  CompareTimeseries,
  DashboardLanguage,
  DashboardPolarity,
  DimensionKey,
} from '~/utils/playerExpectationsNewDashboard'

// Turn [10, 20, 30] into "10,20,30" for query params.
function toCsv(nums: number[]): string | undefined {
  return nums.length ? nums.join(',') : undefined
}

// Convert languages array into a CSV string, but ignore "all".
function toLangCsv(langs: DashboardLanguage[]): string | undefined {
  const xs = langs.filter((x) => x !== 'all')
  return xs.length ? xs.join(',') : undefined
}

async function fetchJson<T>(url: string, params: Record<string, string | number | undefined>) {
  return await $fetch<T>(url, { params })
}

// Runtime config can optionally provide a different API origin (e.g. another domain).
// this was done for the ngrok usecase where basepath differed
export function usePlayerExpectationsNewDashboardCompare(apiBase?: string) {
  const cfg = (typeof useRuntimeConfig === 'function' ? useRuntimeConfig() : undefined) as any

  // Base URL for all endpoints used by this composable.
  function joinBase(origin: string | undefined, path: string) {
    const o = (origin ?? '').trim()
    if (!o) return path // same-origin => "/api/..."
    return `${o.replace(/\/$/, '')}${path}`
  }

  const base =
    apiBase ??
    joinBase(cfg?.public?.apiBase as string | undefined, '/api/player-expectations-new')


  const makeSide = () => {
    const appIds = ref<number[]>([])
    const polarity = ref<DashboardPolarity>('any')
    const languages = ref<DashboardLanguage[]>(['all'])
    return { appIds, polarity, languages }
  }

  const left = makeSide()
  const right = makeSide()

  const loading = ref(false)
  const error = ref<unknown>(null)

  const leftKpis = ref<CompareKpis | null>(null)
  const rightKpis = ref<CompareKpis | null>(null)

  const leftSent = ref<CompareSentiments | null>(null)
  const rightSent = ref<CompareSentiments | null>(null)

  // NEW: timeseries
  const leftTs = ref<CompareTimeseries | null>(null)
  const rightTs = ref<CompareTimeseries | null>(null)

  const leftCodes = ref<CompareTopCodes | null>(null)
  const rightCodes = ref<CompareTopCodes | null>(null)

  // heatmaps (all codes)
  const leftHeatAesthetics = ref<CompareHeatmapCodes | null>(null)
  const leftHeatFeatures = ref<CompareHeatmapCodes | null>(null)
  const leftHeatPain = ref<CompareHeatmapCodes | null>(null)

  const rightHeatAesthetics = ref<CompareHeatmapCodes | null>(null)
  const rightHeatFeatures = ref<CompareHeatmapCodes | null>(null)
  const rightHeatPain = ref<CompareHeatmapCodes | null>(null)

  const leftScope = computed<CompareScope>(() => ({
    appIds: left.appIds.value,
    polarity: left.polarity.value,
    languages: left.languages.value,
  }))

  const rightScope = computed<CompareScope>(() => ({
    appIds: right.appIds.value,
    polarity: right.polarity.value,
    languages: right.languages.value,
  }))

  // Convert a CompareScope into backend query parameters.
  function scopeParams(scope: CompareScope) {
    return {
      app_ids: toCsv(scope.appIds),
      polarity: scope.polarity,
      languages: toLangCsv(scope.languages),
    }
  }


  // Load one heatmap (aesthetics/features/pain) for a given scope
  async function loadHeatmap(scope: CompareScope, dimension: DimensionKey) {
    const p = scopeParams(scope)
    return await fetchJson<CompareHeatmapCodes>(`${base}/dashboard/compare/heatmap-codes/`, {
      ...p,
      dimension,
    })
  }


  // Load all data blocks needed for one side (Left OR Right).
  // We fetch in parallel because they are independent requests.
  async function loadSide(scope: CompareScope) {
    const p = scopeParams(scope)

    const [kpis, sent, ts, codes, heatA, heatF, heatP] = await Promise.all([
      fetchJson<CompareKpis>(`${base}/dashboard/compare/kpis/`, p),
      fetchJson<CompareSentiments>(`${base}/dashboard/compare/sentiments/`, p),

      // NEW: timeline
      fetchJson<CompareTimeseries>(`${base}/dashboard/compare/timeseries/`, p),

      // Drivers table should be “most mentioned aspects regardless of level”
      fetchJson<CompareTopCodes>(`${base}/dashboard/compare/top-codes/`, { ...p, level: 'all', limit: 20 }),


      loadHeatmap(scope, 'aesthetics'),
      loadHeatmap(scope, 'features'),
      loadHeatmap(scope, 'pain'),
    ])

    return { kpis, sent, ts, codes, heatA, heatF, heatP }
  }

  // Load BOTH sides, then write the results into the refs used by components.
  async function load() {

    //console.count('LOAD') // just a bug fix var

    loading.value = true
    error.value = null
    try {
      const [L, R] = await Promise.all([loadSide(leftScope.value), loadSide(rightScope.value)])

      leftKpis.value = L.kpis
      leftSent.value = L.sent
      leftTs.value = L.ts
      leftCodes.value = L.codes
      leftHeatAesthetics.value = L.heatA
      leftHeatFeatures.value = L.heatF
      leftHeatPain.value = L.heatP

      rightKpis.value = R.kpis
      rightSent.value = R.sent
      rightTs.value = R.ts
      rightCodes.value = R.codes
      rightHeatAesthetics.value = R.heatA
      rightHeatFeatures.value = R.heatF
      rightHeatPain.value = R.heatP
    } catch (e) {
      error.value = e
      // eslint-disable-next-line no-console
      console.error(e)
    } finally {
      loading.value = false
    }
  }

  // filter changes can happen quickly (clicking several chips)...wait 200ms after the last change before calling load()
  let t: ReturnType<typeof setTimeout> | null = null
  function scheduleLoad() {
    if (t) clearTimeout(t)
    t = setTimeout(() => load(), 200)
  }

  watch([left.appIds, left.polarity, left.languages, right.appIds, right.polarity, right.languages], () => scheduleLoad(), {
    deep: true,
  })

  onBeforeUnmount(() => {
    if (t) clearTimeout(t)
  })

  // Everything returned here becomes accessible to the page/components.
  return {
    loading,
    error,
    load,

    left,
    right,

    leftKpis,
    leftSent,
    leftTs,
    leftCodes,
    leftHeatAesthetics,
    leftHeatFeatures,
    leftHeatPain,

    rightKpis,
    rightSent,
    rightTs,
    rightCodes,
    rightHeatAesthetics,
    rightHeatFeatures,
    rightHeatPain,
  }
}
