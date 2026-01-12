// frontend/app/utils/playerExpectationsNewDashboard.ts

//main tasks
//shared types + helpers file for the dashboard frontend.
//defines TypeScript types that match the JSON the backend
//also has formatting helpers

export type DashboardPolarity = 'any' | 'rec' | 'nrec'

export type DashboardLanguage = 'all' | 'english' | 'schinese'
export type CodeLevel = 'top' | 'all'

export type CompareScope = {
  appIds: number[]
  polarity: DashboardPolarity
  languages: DashboardLanguage[]
}

export type CompareKpis = {
  reviews: number
  recommended_rate: number
  mentions_total: number
  mentions_per_review: number
}

export type SentimentBuckets = {
  positive: number
  neutral: number
  negative: number
  missing: number
}

// Sentiment distribution response from /compare/sentiments
export type CompareSentiments = {
  total: number
  buckets: SentimentBuckets
  shares: Record<keyof SentimentBuckets, number>
  detailed: Record<string, number>
}

// One point in the monthly time series returned by /compare/timeseries
export type TimeseriesPoint = {
  month: string
  reviews: number
  recommended_rate: number
  mentions: SentimentBuckets
}

export type CompareTimeseries = {
  data: TimeseriesPoint[]
}

export type TopCodeRow = {
  coarse_category: string
  code_int: number
  code_text: string
  total: number
  positive: number
  neutral: number
  negative: number
  missing: number
  net: number
}

export type CompareTopCodes = {
  level: CodeLevel
  limit: number
  table: TopCodeRow[]
  top_positive: TopCodeRow[]
  top_negative: TopCodeRow[]
}

export type DimensionKey = 'aesthetics' | 'features' | 'pain'

export type DimensionSummaryRow = {
  parent_code_int: number
  parent_text: string
  total: number
  buckets: SentimentBuckets
  shares: Record<keyof SentimentBuckets, number>
  net: number
}

export type CompareDimensionSummary = {
  dimension: DimensionKey
  rows: DimensionSummaryRow[]
}

export type HeatmapCodeRow = {
  code_int: number
  code_text: string
  total: number
  buckets: SentimentBuckets
  shares: Record<keyof SentimentBuckets, number>
  net: number
}

export type CompareHeatmapCodes = {
  dimension: DimensionKey
  rows: HeatmapCodeRow[]
}

// helper functions

export function clamp01(x: number): number {
  if (x < 0) return 0
  if (x > 1) return 1
  return x
}

export function pct(x: number, digits = 1): string {
  return `${(clamp01(x) * 100).toFixed(digits)}%`
}

export function fmtInt(n: number): string {
  return (n ?? 0).toLocaleString()
}

export function fmtFloat(n: number, digits = 2): string {
  return (n ?? 0).toFixed(digits)
}

export function errorToText(e: unknown): string {
  if (!e) return ''
  if (typeof e === 'string') return e
  const anyE = e as any
  if (anyE?.data?.detail) return String(anyE.data.detail)
  if (anyE?.data?.message) return String(anyE.data.message)
  if (anyE?.statusMessage) return String(anyE.statusMessage)
  if (anyE?.message) return String(anyE.message)
  try {
    return JSON.stringify(e, null, 2)
  } catch {
    return String(e)
  }
}
