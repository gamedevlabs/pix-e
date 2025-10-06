type AspectSentimentRow = {
  dominant_aspect: string
  dominant_sentiment: 'positive' | 'neutral' | 'negative'
  count: number
}

type TrendRow = {
  month: string
  positive?: number
  neutral?: number
  negative?: number
}

type ConfusionRow = {
  pair: string
  count: number
}

const SENTIMENTS = ['positive', 'neutral', 'negative'] as const
const posterPalette = ['#27599e', '#a1d5cc', '#d9c85f', '#3b6cb2', '#69a89f'] as const
const sentimentColors: Record<(typeof SENTIMENTS)[number], string> = {
  positive: posterPalette[0],
  neutral: posterPalette[1],
  negative: posterPalette[2],
}

const confusionPaletteBase = [
  '#27599e',
  '#a1d5cc',
  '#d9c85f',
  '#3b6cb2',
  '#69a89f',
  '#f8ef9a',
  '#153b7a',
  '#8ac9c0',
  '#f2e686',
  '#27599e', // repeat ok
]

export function usePlayerExpectationCharts(baseUrl = 'http://localhost:8000/api') {
  // reactive chart state
  const aspectChartData = ref(null)
  const sentimentChartData = ref(null)
  const lineChartData = ref(null)
  const sentimentPieData = ref(null)
  const heatmapData = ref(null)
  const topConfusionsChartData = ref(null)

  const loading = ref(false)
  const error = ref<unknown>(null)

  // ---------- shaping helpers ----------
  function toAspectBar(data: Record<string, number>) {
    const labels = Object.keys(data)
    const values = Object.values(data)
    return {
      labels,
      datasets: [{ label: 'Mentions', data: values, backgroundColor: posterPalette }],
    }
  }

  function toAspectSentimentStacks(rows: AspectSentimentRow[]) {
    const labels = Array.from(new Set(rows.map((r) => r.dominant_aspect)))
    const map = new Map<string, Map<string, number>>()
    for (const s of SENTIMENTS) map.set(s, new Map())
    for (const r of rows) {
      map.get(r.dominant_sentiment)!.set(r.dominant_aspect, r.count)
    }
    return {
      labels,
      datasets: SENTIMENTS.map((s) => ({
        label: s,
        data: labels.map((a) => map.get(s)!.get(a) ?? 0),
        backgroundColor: sentimentColors[s],
      })),
    }
  }

  function toTrendLines(rows: TrendRow[]) {
    const labels = rows.map((r) => r.month)
    return {
      labels,
      datasets: SENTIMENTS.map((s) => ({
        label: s,
        data: rows.map((r) => r[s] ?? 0),
        borderColor: sentimentColors[s],
        fill: false,
      })),
    }
  }

  function toPie(data: Record<string, number>) {
    const labels = SENTIMENTS.filter((s) => data[s] !== undefined)
    const values = labels.map((l) => data[l])
    return {
      labels,
      datasets: [
        {
          data: values,
          backgroundColor: labels.map((l) => sentimentColors[l]),
        },
      ],
    }
  }

  function toConfusionsBar(rows: ConfusionRow[]) {
    const labels = rows.map((r) => r.pair)
    const values = rows.map((r) => r.count)
    const colors = confusionPaletteBase.slice(0, labels.length)
    return {
      labels,
      datasets: [{ label: 'Model → GPT', data: values, backgroundColor: colors }],
    }
  }

  // ---------- main load function ----------
  async function load() {
    loading.value = true
    error.value = null

    try {
      const [
        aspectFrequency,
        aspectSentiment,
        trendOverTime,
        sentimentPie,
        heatmap,
        topConfusions,
      ] = await Promise.all([
        $fetch<{ data: Record<string, number> }>(`${baseUrl}/aspect-frequency`),
        $fetch<{ data: AspectSentimentRow[] }>(`${baseUrl}/aspect-sentiment`),
        $fetch<{ data: TrendRow[] }>(`${baseUrl}/trend-over-time`),
        $fetch<{ data: Record<string, number> }>(`${baseUrl}/sentiment-pie`),
        $fetch<{ data: Record<string, Record<string, number>> }>(`${baseUrl}/heatmap`),
        $fetch<{ data: ConfusionRow[] }>(`${baseUrl}/top-confusions`),
      ])

      aspectChartData.value = toAspectBar(aspectFrequency.data)
      sentimentChartData.value = toAspectSentimentStacks(aspectSentiment.data)
      lineChartData.value = toTrendLines(trendOverTime.data)
      sentimentPieData.value = toPie(sentimentPie.data)
      heatmapData.value = heatmap.data
      topConfusionsChartData.value = toConfusionsBar(topConfusions.data)
    } catch (e) {
      error.value = e
      console.error('Error loading charts:', e)
    } finally {
      loading.value = false
    }
  }

  return {
    // state
    aspectChartData,
    sentimentChartData,
    lineChartData,
    sentimentPieData,
    heatmapData,
    topConfusionsChartData,
    loading,
    error,
    // action
    load,
  }
}
