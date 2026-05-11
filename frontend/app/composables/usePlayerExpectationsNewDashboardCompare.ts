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
import { useApi } from '~/composables/useApi'

// Turn [10, 20, 30] into "10,20,30" for query params.
function toCsv(nums: number[]): string | undefined {
  return nums.length ? nums.join(',') : undefined
}

// Convert languages array into a CSV string, but ignore "all".
function toLangCsv(langs: DashboardLanguage[]): string | undefined {
  const xs = langs.filter((x) => x !== 'all')
  return xs.length ? xs.join(',') : undefined
}

// Runtime config can optionally provide a different API origin (e.g. another domain).
// this was done for the ngrok usecase where basepath differed
export function usePlayerExpectationsNewDashboardCompare() {
  const { apiFetch } = useApi()

  const alive = ref(true)

  let controller: AbortController | null = null

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

  async function fetchJson<T>(url: string, params: Record<string, string | number | undefined>) {
    // controller is created per load()
    return await apiFetch<T>(url, { query: params, signal: controller?.signal })
  }

  // Load one heatmap (aesthetics/features/pain) for a given scope
  async function loadHeatmap(scope: CompareScope, dimension: DimensionKey) {
    const p = scopeParams(scope)
    return await fetchJson<CompareHeatmapCodes>(`/api/player-expectations-new/dashboard/compare/heatmap-codes/`, {
      ...p,
      dimension,
    })
  }

  // Load all data blocks needed for one side (Left OR Right).
  // We fetch in parallel because they are independent requests.
  async function loadSide(scope: CompareScope) {
    const p = scopeParams(scope)

    const [kpis, sent, ts, codes, heatA, heatF, heatP] = await Promise.all([
      fetchJson<CompareKpis>(`/api/player-expectations-new/dashboard/compare/kpis/`, p),
      fetchJson<CompareSentiments>(`/api/player-expectations-new/dashboard/compare/sentiments/`, p),

      // NEW: timeline
      fetchJson<CompareTimeseries>(`/api/player-expectations-new/dashboard/compare/timeseries/`, p),

      // Drivers table should be “most mentioned aspects regardless of level”
      fetchJson<CompareTopCodes>(`/api/player-expectations-new/dashboard/compare/top-codes/`, {
        ...p,
        level: 'all',
        limit: 20,
      }),

      loadHeatmap(scope, 'aesthetics'),
      loadHeatmap(scope, 'features'),
      loadHeatmap(scope, 'pain'),
    ])

    return { kpis, sent, ts, codes, heatA, heatF, heatP }
  }

  // filter changes can happen quickly (clicking several chips)...wait 200ms after the last change before calling load()
  let t: ReturnType<typeof setTimeout> | null = null
  function scheduleLoad() {
    if (t) clearTimeout(t)
    t = setTimeout(() => load(), 10)
  }

  const stopWatch = watch(
    [left.appIds, left.polarity, left.languages, right.appIds, right.polarity, right.languages],
    () => scheduleLoad(),
    { deep: true },
  )

  // Load BOTH sides, then write the results into the refs used by components.
  async function load() {
    controller?.abort()
    controller = new AbortController()

    //console.count('LOAD') // just a bug fix var

    loading.value = true
    error.value = null
    try {
      const [L, R] = await Promise.all([loadSide(leftScope.value), loadSide(rightScope.value)])
      if (!alive.value) return

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
    } catch (e: unknown) {
      // Abort is expected on navigation or when a new load starts
      if (e instanceof DOMException && e.name === 'AbortError') return
      if (
        typeof e === 'object' &&
        e !== null &&
        'name' in e &&
        (e as { name?: unknown }).name === 'AbortError'
      )
        return

      // ofetch often throws FetchError with a nested cause = AbortError
      if (
        typeof e === 'object' &&
        e !== null &&
        'cause' in e &&
        (e as { cause?: unknown }).cause instanceof DOMException &&
        (e as { cause: DOMException }).cause.name === 'AbortError'
      ) {
        return
      }

      error.value = e
      console.error(e)
    } finally {
      if (alive.value) loading.value = false
    }
  }

  onBeforeUnmount(() => {
    alive.value = false
    stopWatch()
    controller?.abort()
    controller = null
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
