// frontend/app/composables/usePlayerExpectationsNewDatasetExplorer.ts
/**
 * Dataset Explorer composable
 *
 * it does the following:
 * 1) stores filters (search text, selected games, selected codes, ranges, dates)
 * 2) stores paging state (page, pageSize)
 * 3) calls the backend endpoint in views.py:
 *      GET {baseUrl}/dataset-explorer/reviews/?...query params...
 * 4) stores the response in `rows` and `meta` so the UI can render it.
 *
 * Big picture:
 * UI changes -> update refs -> toQueryParams() -> load() -> backend returns JSON -> rows/meta updated.
 */
// export ... makes availble for other files
    //  Record<K, V>, key, value pairs
export const GAME_NAMES: Record<number, string> = {
  367520: 'Hollow Knight',
  620: 'Portal 2',
  268910: 'Cuphead',
  1057090: 'Ori and the Will of the Wisps',
  238460: 'BattleBlock Theater',
  255710: 'Cities: Skylines',
  813780: 'Age of Empires II',
  323190: 'Frostpunk',
  949230: 'Cities: Skylines II',
  1363080: 'Manor Lords',
  774171: 'Muse Dash',
  977950: 'A Dance of Fire and Ice',
  1817230: 'Hi-Fi RUSH',
  960170: 'DJMAX RESPECT V',
  774181: 'Rhythm Doctor',
  646570: 'Slay the Spire',
  2379780: 'Balatro',
  1092790: 'Inscryption',
  1449850: 'Yu-Gi-Oh! Master Duel',
  544810: 'KARDS',
  291550: 'Brawlhalla',
  678950: 'DRAGON BALL FighterZ',
  1364780: 'Street Fighter 6',
  1384160: 'GUILTY GEAR -STRIVE-',
  310950: 'Street Fighter V',
}

export const GENRE_APPIDS: Record<string, number[]> = {
  Platformer: [367520, 620, 268910, 1057090, 238460],
  'City Builder': [255710, 813780, 323190, 949230, 1363080],
  Rhythm: [774171, 977950, 1817230, 960170, 774181],
  'Card Game': [646570, 2379780, 1092790, 1449850, 544810],
  '2D Fighter': [291550, 678950, 1364780, 1384160, 310950],
}

// code -> text maps for labels in the filter sidebar.
export const AESTHETIC_CODE_TO_TEXT: Record<number, string> = {
  1: 'Sensation',
  2: 'Fantasy',
  3: 'Narrative',
  4: 'Challenge',
  5: 'Fellowship',
  6: 'Discovery',
  7: 'Expression',
  8: 'Submission',
}

export const FEATURE_CODE_TO_TEXT: Record<number, string> = {
  10: 'Sound',
  11: 'Realistic sound effects',
  12: 'Speaking characters',
  13: 'Background music',
  14: 'Narration',
  20: 'Graphics',
  21: 'High-quality realistic graphics',
  22: 'Cartoon-style graphics',
  23: 'Full Motion Video (FMV)',
  30: 'Background and Setting',
  31: 'Based on a story',
  32: 'Based on film or TV',
  33: 'Realistic settings',
  34: 'Fantasy settings',
  40: 'Duration of Game',
  41: 'Long (months or years)',
  42: 'Medium (days or weeks)',
  43: 'Short (one session)',
  50: 'Rate of Play',
  51: 'Rapid absorption rate',
  52: 'Rapid advancement rate',
  60: 'Use of Humor',
  61: 'Presence of humor',
  70: 'Control Options',
  71: 'Sound settings',
  72: 'Graphic settings',
  73: 'Skill/level settings',
  74: 'Choice of control methods',
  75: 'Physical feedback',
  800: 'Game Dynamics',
  801: 'Exploring new areas',
  802: 'Elements of surprise',
  803: 'Fulfilling quests',
  804: 'Skill development',
  805: 'Sophisticated AI interactions',
  806: 'Finding things (secret doors, levers)',
  807: 'Surviving against the odds',
  808: 'Shooting (enemies, targets, etc.)',
  809: 'Different ending options',
  810: 'Different modes of transport',
  811: 'Collecting things (objects, keys)',
  812: 'Solving puzzles',
  813: 'Beating times',
  814: 'Cheats / Easter eggs',
  815: 'Avoiding things',
  816: 'Solving time-limited problems',
  817: 'Building environments',
  818: 'Mapping',
  819: 'Linear / non-linear game format',
  90: 'Winning and Losing Features',
  91: 'Potential to lose points',
  92: 'Points accumulation',
  93: 'Finding bonuses',
  94: 'Having to start level again',
  95: 'Ability to save regularly',
  100: 'Character Development',
  101: 'Character development over time',
  102: 'Character customization',
  110: 'Brand Assurance',
  111: 'Brand loyalty',
  112: 'Celebrity endorsement',
  120: 'Multiplayer Features',
  121: 'Multiplayer option (online)',
  122: 'Multiplayer (LAN)',
  123: 'Multiplayer communication',
  124: 'Building alliances',
  125: 'Beating other players or NPCs',
  130: 'Price and Value',
  131: 'Game price and perceived value',
  132: 'In-game monetisation',
}

export const PAIN_CODE_TO_TEXT: Record<number, string> = {
  10: 'Unpredictable / inconsistent response',
  11: 'poor hit detection',
  12: 'poor in-game physics',
  13: 'inconsistent response to input',
  20: 'Does not allow enough customization',
  21: 'cannot change video or audio settings',
  22: 'cannot change difficulty',
  23: 'cannot change game speed',
  30: 'Artificial intelligence problems',
  31: 'problems with pathfinding',
  32: 'problems with computer-controlled teammates',
  40: 'Mismatch between camera/view and action',
  41: 'bad camera angle',
  42: 'view is obstructed',
  43: 'view does not adjust quickly enough',
  50: 'Does not let user skip non-playable content',
  51: 'cannot skip video or audio clips',
  52: 'frequently repeated non-playable sequences',
  60: 'Clumsy input scheme',
  61: 'bad input mappings',
  62: 'limited device support',
  63: 'limited control customization',
  70: 'Difficult to control actions in the game',
  71: 'oversensitive controls',
  72: 'unnatural controls',
  73: 'unresponsive controls',
  80: 'Does not provide enough information on game status',
  81: 'does not provide adequate information',
  82: 'visual indicators, icons, and maps are inadequate',
  90: 'Does not provide adequate training and help',
  91: 'does not provide default or recommended choices',
  92: 'does not provide suggestions or help',
  93: 'does not provide adequate documentation',
  100: 'Command sequences are too complex',
  101: 'learning curve is too steep',
  102: 'requires too much micromanagement',
  103: 'command sequences are complex, lengthy, or awkward',
  110: 'Visual representations are difficult to interpret',
  111: 'bad visualization of information',
  112: 'too much screen clutter',
  113: 'too many elements on screen',
  114: 'difficult to visually distinguish interactive content',
  120: "Response to user's action not timely enough",
  130: 'Translation and localization issues',
  131: 'inadequate or missing localization',
  132: 'incorrect or misleading translation',
  140: 'Performance and technical stability',
  141: 'low or unstable frame rate',
  142: 'excessive loading times',
  143: 'crashes or freezes',
  150: 'Connectivity and online stability',
  151: 'frequent disconnects',
  152: 'matchmaking or queue issues',
  153: 'server instability or downtime',
}


// These TypeScript "types" describe the JSON we get from the backend.
export type CodeRow = {
  coarse_category: string
  code_int: number
  code_text: string
  sentiment_v2: string
}
export type QuoteRow = {
  quote_id: number
  coarse_category: string
  quote_text: string
  codes: CodeRow[]
}
export type ReviewRow = {
  recommendation_id: string
  app_id: number
  game_name: string
  timestamp_created: number
  voted_up: number
  votes_up: number
  votes_funny: number
  playtime_at_review: number
  playtime_forever: number
  review_text_en: string
  quotes: QuoteRow[]
}
export type ReviewsResponse = {
  meta: {
    page: number
    page_size: number
    total: number
    total_pages: number
  }
  data: ReviewRow[]
}


//Helper file: converts the date string from an <input type="date"> into unix seconds.
// Scraped data is in unix seconds  and the users input is a date string
function dateStrToUnixSeconds(dateStr: string, endOfDay: boolean) {
  // dateStr is "YYYY-MM-DD"
  if (!dateStr) return undefined
  const d = new Date(dateStr + 'T00:00:00')
  if (Number.isNaN(d.getTime())) return undefined
  if (endOfDay) d.setHours(23, 59, 59, 999)
  // Convert milliseconds -> seconds (backend uses seconds).
  return Math.floor(d.getTime() / 1000)
}


//Main composable function.
export function usePlayerExpectationsNewDatasetExplorer(
  baseUrl = 'http://localhost:8000/api/player-expectations-new') {
  const loading = ref(false)
  // ref creates a reactive value...if the value changes, Vue will automatically update the UI.
  //access the real value via .value
  const error = ref<unknown>(null)

  // paging
  const page = ref(1)
  const pageSize = ref(100)

  // top filters
  const q = ref('') // keyword search, start empty
  const recommended = ref<'all' | 'recommended' | 'not_recommended'>('all')
  const sort = ref<'newest' | 'oldest'>('newest')

  // date input as YYYY-MM-DD strings
  const dateFrom = ref<string>('')
  const dateTo = ref<string>('')

  // numeric ranges
  const minVotesUp = ref<number | null>(null)
  const maxVotesUp = ref<number | null>(null)
  const minVotesFunny = ref<number | null>(null)
  const maxVotesFunny = ref<number | null>(null)

  const minPlaytimeAtReview = ref<number | null>(null)
  const maxPlaytimeAtReview = ref<number | null>(null)
  const minPlaytimeForever = ref<number | null>(null)
  const maxPlaytimeForever = ref<number | null>(null)

  // genres/games selections in Sets (cannot contain duplicates)
  const selectedGenres = ref<Set<string>>(new Set())
  const selectedGames = ref<Set<number>>(new Set())

  /**
   * computed(...) creates a value that automatically recalculates when its dependencies change.
   * Here: visibleGames changes when selectedGenres changes.
   */
  const visibleGames = computed(() => {
  // If no genre filter is selected, show ALL games (so UI looks unselected but still shows everything)
  if (selectedGenres.value.size === 0) {
    return Array.from(new Set(Object.values(GENRE_APPIDS).flat())).sort((a, b) => a - b)
  }

  // Otherwise, show only games in the selected genres
  const ids = new Set<number>()
  for (const g of selectedGenres.value) {
    for (const id of GENRE_APPIDS[g] || []) ids.add(id)
  }
  return Array.from(ids).sort((a, b) => a - b)
})


  function toggleGenre(genre: string) {
    // Toggle means: if selected -> unselect; if unselected -> select
    const nextGenres = new Set(selectedGenres.value)
    if (nextGenres.has(genre)) nextGenres.delete(genre)
    else nextGenres.add(genre)
    selectedGenres.value = nextGenres

    // selecting a genre also selects all its games auto
    const nextGames = new Set(selectedGames.value)
    const ids = GENRE_APPIDS[genre] || []
    const genreNowSelected = nextGenres.has(genre)
    for (const id of ids) {
      if (genreNowSelected) nextGames.add(id)
      else nextGames.delete(id)
    }
    selectedGames.value = nextGames
  }

  // Toggle a single appId (game)
  function toggleGame(appId: number) {
    const next = new Set(selectedGames.value)
    if (next.has(appId)) next.delete(appId)
    else next.add(appId)
    selectedGames.value = next
  }

  // code filters
  const selectedAestheticCodes = ref<Set<number>>(new Set())
  const selectedFeatureCodes = ref<Set<number>>(new Set())
  const selectedPainCodes = ref<Set<number>>(new Set())

  function toggleCode(which: 'aesthetic' | 'feature' | 'pain', code: number) {
    // Choose which Set we should update based on the category
    const target =
      which === 'aesthetic'
        ? selectedAestheticCodes
        : which === 'feature'
          ? selectedFeatureCodes
          : selectedPainCodes

    // Toggle the code in that set
    const next = new Set(target.value)
    if (next.has(code)) next.delete(code)
    else next.add(code)
    target.value = next
  }

  // data from backend
  const rows = ref<ReviewRow[]>([])
  const meta = ref<ReviewsResponse['meta'] | null>(null)

  // small UI helper: "very_positive" -> "very positive"
  function prettySentiment(s: string | null) {
    if (!s) return '—'
    return s.replaceAll('_', ' ')
  }

//Converts current filter state into query params for the backend (must match views.py)
  function toQueryParams() {
    const params: Record<string, any> = {
      page: page.value,
      page_size: pageSize.value,
      recommended: recommended.value,
    }

    // Keyword search
    if (q.value.trim()) params.q = q.value.trim()

    // send app ids based on selectedGames
    const apps = Array.from(selectedGames.value)
    if (apps.length) params.app_ids = apps.join(',')

    // dates: convert YYYY-MM-DD -> unix seconds
    const df = dateStrToUnixSeconds(dateFrom.value, false)
    const dt = dateStrToUnixSeconds(dateTo.value, true)
    if (df !== undefined) params.date_from = df
    if (dt !== undefined) params.date_to = dt

    // sort (backend must support; if not, you can ignore this param)
    params.sort = sort.value

    // ranges
    if (minVotesUp.value != null) params.min_votes_up = minVotesUp.value
    if (maxVotesUp.value != null) params.max_votes_up = maxVotesUp.value
    if (minVotesFunny.value != null) params.min_votes_funny = minVotesFunny.value
    if (maxVotesFunny.value != null) params.max_votes_funny = maxVotesFunny.value

    if (minPlaytimeAtReview.value != null) params.min_playtime_at_review = minPlaytimeAtReview.value
    if (maxPlaytimeAtReview.value != null) params.max_playtime_at_review = maxPlaytimeAtReview.value
    if (minPlaytimeForever.value != null) params.min_playtime_forever = minPlaytimeForever.value
    if (maxPlaytimeForever.value != null) params.max_playtime_forever = maxPlaytimeForever.value

    // code filtes
    const a = Array.from(selectedAestheticCodes.value)
    const f = Array.from(selectedFeatureCodes.value)
    const p = Array.from(selectedPainCodes.value)
    if (a.length) params.aesthetic_codes = a.join(',')
    if (f.length) params.feature_codes = f.join(',')
    if (p.length) params.pain_codes = p.join(',')

    return params
  }

  async function load() {
    loading.value = true
    error.value = null
    try {
      const res = await $fetch<ReviewsResponse>(`${baseUrl}/dataset-explorer/reviews/`, {
        params: toQueryParams(),
      })
      // Save response into reactive state so UI updates.
      rows.value = res.data
      meta.value = res.meta
    } catch (e) {
      error.value = e
      console.error(e)
    } finally {
      loading.value = false
    }
  }

  function nextPage() {
    // Go to next page only if it exists.
    if (!meta.value) return
    if (page.value < meta.value.total_pages) {
      page.value += 1
      load()
    }
  }

  function prevPage() {
    if (page.value > 1) {
      page.value -= 1
      load()
    }
  }

  /**
   * This return object is what components will use.
   * If you return something here, a component can read/change it.
   */
  return {
    // data
    rows,
    meta,
    loading,
    error,

    // actions
    load,
    nextPage,
    prevPage,

    // paging
    page,
    pageSize,

    // filters
    q,
    recommended,
    sort,
    dateFrom,
    dateTo,
    minVotesUp,
    maxVotesUp,
    minVotesFunny,
    maxVotesFunny,
    minPlaytimeAtReview,
    maxPlaytimeAtReview,
    minPlaytimeForever,
    maxPlaytimeForever,

    // genres/games
    selectedGenres,
    selectedGames,
    visibleGames,
    toggleGenre,
    toggleGame,

    // codes
    selectedAestheticCodes,
    selectedFeatureCodes,
    selectedPainCodes,
    toggleCode,

    // helper
    prettySentiment,
  }
}
