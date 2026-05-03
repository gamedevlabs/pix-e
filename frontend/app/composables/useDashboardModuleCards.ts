const PREVIEW_MAX = 2

/**
 * Loads the underlying data for the dashboard's module cards (Design Pillars,
 * Player Experience charts, Player Expectations) and exposes a small preview
 * shape per module: a list of preview items + a "more" label that doubles as
 * the empty-state hint when there's nothing to show yet.
 */
export function useDashboardModuleCards() {
  const { items: pillars, fetchAll: fetchPillars } = usePillars()
  const { items: pxCharts, fetchAll: fetchPxCharts } = usePxCharts()
  const {
    aspectChartData,
    sentimentPieData,
    load: loadExpectations,
  } = usePlayerExpectationCharts('http://localhost:8000/api')

  onMounted(() => {
    fetchPillars()
    fetchPxCharts()
    loadExpectations()
  })

  // ─── Pillars ───────────────────────────────────────────────────────────────
  const pillarPreviewItems = computed(() =>
    pillars.value.slice(0, PREVIEW_MAX).map((p) => ({ text: p.name, icon: 'i-lucide-layers' })),
  )
  const pillarMoreLabel = computed(() => {
    const rest = pillars.value.length - PREVIEW_MAX
    if (pillars.value.length === 0) return 'No pillars yet — add your first one'
    if (rest <= 0) return undefined
    return `+${rest} more ${rest === 1 ? 'pillar' : 'pillars'}`
  })

  // ─── PX Charts ─────────────────────────────────────────────────────────────
  const chartPreviewItems = computed(() =>
    pxCharts.value
      .slice(0, PREVIEW_MAX)
      .map((c) => ({ text: c.name, icon: 'i-lucide-chart-network' })),
  )
  const chartMoreLabel = computed(() => {
    const rest = pxCharts.value.length - PREVIEW_MAX
    if (pxCharts.value.length === 0) return 'No charts yet — create your first one'
    if (rest <= 0) return undefined
    return `+${rest} more ${rest === 1 ? 'chart' : 'charts'}`
  })

  // ─── Player Expectations ──────────────────────────────────────────────────
  // Surface the top-2 most-mentioned aspects + the dominant sentiment as a
  // mini summary, so the dashboard hints at the data without rendering charts.
  const expectationsPreviewItems = computed(() => {
    const items: { text: string; icon: string }[] = []

    const aspectData = aspectChartData.value as {
      labels: string[]
      datasets: { data: number[] }[]
    } | null
    if (aspectData?.labels?.length) {
      const paired = aspectData.labels.map((label, i) => ({
        label,
        count: aspectData.datasets[0]?.data[i] ?? 0,
      }))
      paired
        .sort((a, b) => b.count - a.count)
        .slice(0, PREVIEW_MAX)
        .forEach(({ label, count }) => {
          items.push({ text: `${label} — ${count} mentions`, icon: 'i-lucide-tag' })
        })
    }

    const pieData = sentimentPieData.value as {
      labels: string[]
      datasets: { data: number[] }[]
    } | null
    if (pieData?.labels?.length) {
      const total = pieData.datasets[0]?.data.reduce((a, b) => a + b, 0) ?? 0
      if (total > 0) {
        const maxIdx = pieData.datasets[0]!.data.indexOf(Math.max(...pieData.datasets[0]!.data))
        const dominant = pieData.labels[maxIdx]
        const pct = Math.round((pieData.datasets[0]!.data[maxIdx]! / total) * 100)
        const icon =
          dominant === 'positive'
            ? 'i-lucide-smile'
            : dominant === 'negative'
              ? 'i-lucide-frown'
              : 'i-lucide-meh'
        items.push({ text: `${pct}% ${dominant} sentiment`, icon })
      }
    }

    return items
  })

  const expectationsMoreLabel = computed(() => {
    if (!expectationsPreviewItems.value.length) return 'No data loaded yet'
    return undefined
  })

  return {
    pillarPreviewItems,
    pillarMoreLabel,
    chartPreviewItems,
    chartMoreLabel,
    expectationsPreviewItems,
    expectationsMoreLabel,
  }
}
