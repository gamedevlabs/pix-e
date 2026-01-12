// frontend/app/composables/useDatasetExplorerViewModel.ts
/**
 * useDatasetExplorerViewModel (split from core for better overview9
 *
 * This file is a "view model" composable:
 * - The "core" composable (usePlayerExpectationsNewDatasetExplorer.ts) handles:
 *     state + filters + building query params + calling the backend (load()).
 * - This view model handles:
 *     UI-friendly helpers (formatting, truncation, highlighting),
 *     UI-only state (which review is selected),
 *     and UI behaviors (click handlers, search inside sidebar lists).
 */
import { isRef } from 'vue'
import type { Ref } from 'vue'

import {
  AESTHETIC_CODE_TO_TEXT,
  FEATURE_CODE_TO_TEXT,
  PAIN_CODE_TO_TEXT,
  type ReviewRow,
} from '~/composables/usePlayerExpectationsNewDatasetExplorer'

// what must the the core object provide
export type DatasetExplorerCore = {
  // data
  rows: Ref<ReviewRow[]>
  error: Ref<unknown> | unknown
  load: () => void | Promise<void>

  // paging
  page: Ref<number>
  pageSize: Ref<number>

  // filters
  q: Ref<string>
  recommended: Ref<'all' | 'recommended' | 'not_recommended'>
  sort: Ref<'newest' | 'oldest'>
  dateFrom: Ref<string>
  dateTo: Ref<string>
  minVotesUp: Ref<number | null>
  maxVotesUp: Ref<number | null>
  minVotesFunny: Ref<number | null>
  maxVotesFunny: Ref<number | null>
  minPlaytimeAtReview: Ref<number | null>
  maxPlaytimeAtReview: Ref<number | null>
  minPlaytimeForever: Ref<number | null>
  maxPlaytimeForever: Ref<number | null>

  // genres/games
  selectedGenres: Ref<Set<string>>
  selectedGames: Ref<Set<number>>
  visibleGames: Ref<number[]>
  toggleGenre: (genre: string) => void
  toggleGame: (appId: number) => void

  // codes
  selectedAestheticCodes: Ref<Set<number>>
  selectedFeatureCodes: Ref<Set<number>>
  selectedPainCodes: Ref<Set<number>>
  toggleCode: (which: 'aesthetic' | 'feature' | 'pain', code: number) => void

  // helper
  prettySentiment: (s: string | null) => string
}

// receives the core composable object and builds UI helpers on top of it.
export function useDatasetExplorerViewModel(core: DatasetExplorerCore) {
  //Which review is selected?
  const selectedRecId = ref<string | null>(null)

  //Find the selected review in the current page rows.
  const selectedReview = computed(
    () => core.rows.value.find((r) => r.recommendation_id === selectedRecId.value) || null
  )

  //error extraction fix
  const unwrappedError = computed(() => {
    return isRef(core.error) ? core.error.value : core.error
  })

  //converts error into string for error banner
  const errorText = computed(() => {
    const e: any = unwrappedError.value
    if (!e) return ''

    if (typeof e === 'string') return e
    if (e?.data?.detail) return String(e.data.detail)
    if (e?.data?.message) return String(e.data.message)
    if (e?.message) return String(e.message)
    if (e?.statusMessage) return String(e.statusMessage)

    try {
      return JSON.stringify(e, null, 2)
    } catch {
      return String(e)
    }
  })

  // shorten long review text so lists look clean.
  function truncate(text: string, n = 220) {
    const t = (text || '').trim()
    if (t.length <= n) return t
    return t.slice(0, n) + '…'
  }

  //convert unix seconds to a date string
  function formatUnix(ts: number) {
    if (!ts) return '—'
    const d = new Date(ts * 1000)
    return d.toLocaleDateString()
  }

  // - Quote highlighting ..inject html
  function escapeHtml(s: string) {
    return s
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;')
  } //turns <, >, &, etc. into safe entities..preventing injections

  //ensures characters like "." or "*" do not break the regex.
  function escapeRegex(s: string) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  }

  //Returns an HTML string where quote substrings are wrapped in <mark>.
  function highlightReviewHtml(reviewText: string, quotes: string[]) {
    const base = escapeHtml(reviewText || '')
    let out = base

    const uniq = Array.from(new Set(quotes.map((x) => (x || '').trim()).filter(Boolean)))
      .sort((a, b) => b.length - a.length)
      .slice(0, 50)

    for (const q of uniq) {
      const qEsc = escapeHtml(q)
      const pattern = new RegExp(escapeRegex(qEsc), 'g')
      out = out.replace(
        pattern,
        `<mark class="px-1 rounded bg-yellow-200/70 dark:bg-yellow-400/20 font-semibold">${qEsc}</mark>`
      )
    }
    return out
  }

  // The sidebar shows code filters. These arrays turn the code maps into UI-friendly lists
  const aestheticCodes = [
    { code: 1, label: `1 — ${AESTHETIC_CODE_TO_TEXT[1]}` },
    { code: 2, label: `2 — ${AESTHETIC_CODE_TO_TEXT[2]}` },
    { code: 3, label: `3 — ${AESTHETIC_CODE_TO_TEXT[3]}` },
    { code: 4, label: `4 — ${AESTHETIC_CODE_TO_TEXT[4]}` },
    { code: 5, label: `5 — ${AESTHETIC_CODE_TO_TEXT[5]}` },
    { code: 6, label: `6 — ${AESTHETIC_CODE_TO_TEXT[6]}` },
    { code: 7, label: `7 — ${AESTHETIC_CODE_TO_TEXT[7]}` },
    { code: 8, label: `8 — ${AESTHETIC_CODE_TO_TEXT[8]}` },
  ]

  //  Feature codes and Pain codes have a "top group" (like 10, 20, 30...). I have decided against using them but they remain here if changes are made
  const featureGroups = [
    { top: 10, subs: [11, 12, 13, 14] },
    { top: 20, subs: [21, 22, 23] },
    { top: 30, subs: [31, 32, 33, 34] },
    { top: 40, subs: [41, 42, 43] },
    { top: 50, subs: [51, 52] },
    { top: 60, subs: [61] },
    { top: 70, subs: [71, 72, 73, 74, 75] },
    {
      top: 800,
      subs: [
        801, 802, 803, 804, 805, 806, 807, 808, 809, 810, 811, 812, 813, 814, 815, 816, 817, 818, 819,
      ],
    },
    { top: 90, subs: [91, 92, 93, 94, 95] },
    { top: 100, subs: [101, 102] },
    { top: 110, subs: [111, 112] },
    { top: 120, subs: [121, 122, 123, 124, 125] },
    { top: 130, subs: [131, 132] },
  ].map((g) => ({
    top: g.top,
    label: `${g.top} — ${FEATURE_CODE_TO_TEXT[g.top] || 'UNKNOWN'}`,
    subs: g.subs.map((c) => ({ code: c, label: `${c} — ${FEATURE_CODE_TO_TEXT[c] || 'UNKNOWN'}` })),
  }))

  const painGroups = [
    { top: 10, subs: [11, 12, 13] },
    { top: 20, subs: [21, 22, 23] },
    { top: 30, subs: [31, 32] },
    { top: 40, subs: [41, 42, 43] },
    { top: 50, subs: [51, 52] },
    { top: 60, subs: [61, 62, 63] },
    { top: 70, subs: [71, 72, 73] },
    { top: 80, subs: [81, 82] },
    { top: 90, subs: [91, 92, 93] },
    { top: 100, subs: [101, 102, 103] },
    { top: 110, subs: [111, 112, 113, 114] },
    { top: 120, subs: [] },
    { top: 130, subs: [131, 132] },
    { top: 140, subs: [141, 142, 143] },
    { top: 150, subs: [151, 152, 153] },
  ].map((g) => ({
    top: g.top,
    label: `${g.top} — ${PAIN_CODE_TO_TEXT[g.top] || 'UNKNOWN'}`,
    subs: g.subs.map((c) => ({ code: c, label: `${c} — ${PAIN_CODE_TO_TEXT[c] || 'UNKNOWN'}` })),
  }))

  // text inputs for searching within the feature/pain lists in the sidebar
  const featureSearch = ref('')
  const painSearch = ref('')

  //Filter the feature groups based on keywoard search
  const filteredFeatureGroups = computed(() => {
    const t = featureSearch.value.trim().toLowerCase()
    if (!t) return featureGroups
    return featureGroups
      .map((g) => { //If you match the top label, keep the whole group.
        const topHit = g.label.toLowerCase().includes(t) || String(g.top).includes(t)
        const subs = g.subs.filter((s) => s.label.toLowerCase().includes(t) || String(s.code).includes(t))
        return topHit ? g : { ...g, subs }
      })
      .filter((g) => g.label.toLowerCase().includes(t) || g.subs.length > 0)
  })

  const filteredPainGroups = computed(() => {
    const t = painSearch.value.trim().toLowerCase()
    if (!t) return painGroups
    return painGroups
      .map((g) => {
        const topHit = g.label.toLowerCase().includes(t) || String(g.top).includes(t)
        const subs = g.subs.filter((s) => s.label.toLowerCase().includes(t) || String(s.code).includes(t))
        return topHit ? g : { ...g, subs }
      })
      .filter((g) => g.label.toLowerCase().includes(t) || g.subs.length > 0)
  })

  //Helper:: Selected chips: soft fill; unselected: outline.
  function chipVariant(selected: boolean) {
    return selected ? 'soft' : 'outline'
  }

  // click handlers (same logic as original page)
  /**
   * These functions are called by components when the user clicks something.
   *
   * Pattern:
   * 1) update selection in core (toggleX)
   * 2) reset to page 1 (because filters changed)
   * 3) reload from backend (core.load)
   */
  function clickGenre(genre: string) {
    core.toggleGenre(genre)
    core.page.value = 1
    core.load()
  }
  function clickGame(appId: number) {
    core.toggleGame(appId)
    core.page.value = 1
    core.load()
  }
  function clickCode(which: 'aesthetic' | 'feature' | 'pain', code: number) {
    core.toggleCode(which, code)
    core.page.value = 1
    core.load()
  }
  function setPolarity(v: 'all' | 'recommended' | 'not_recommended') {
    core.recommended.value = v
  }

  // auto-refresh on top filters (exact same dependency list + behavior)
  //  whenever ANY of these refs changes, update all
  watch(
    [
      core.q,
      core.recommended,
      core.sort,
      core.pageSize,
      core.dateFrom,
      core.dateTo,
      core.minVotesUp,
      core.maxVotesUp,
      core.minVotesFunny,
      core.maxVotesFunny,
      core.minPlaytimeAtReview,
      core.maxPlaytimeAtReview,
      core.minPlaytimeForever,
      core.maxPlaytimeForever,
    ],
    () => {
      core.page.value = 1
      core.load()
    }
  )

  //Anything returned here can be used in dataset-explorer.vue and its child components.
  return {
    selectedRecId,
    selectedReview,

    errorText,

    truncate,
    formatUnix,
    highlightReviewHtml,

    aestheticCodes,
    featureSearch,
    painSearch,
    filteredFeatureGroups,
    filteredPainGroups,

    chipVariant,

    clickGenre,
    clickGame,
    clickCode,
    setPolarity,
  }
}
