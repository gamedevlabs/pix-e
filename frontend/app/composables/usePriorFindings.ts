import type { Finding, Paper } from '~/utils/priorFindings'
import { papers, findings } from '~/utils/priorFindingsData'

type PaperOption = { id: string; label: string }

function normalizeText(s: string) { // for the keyword search, make sure you can compare without considereing capitalization
  return (s || '').toLowerCase().trim()
}

export function usePriorFindings() {
  //a ll the memmory/const are refs..so they are reactive and when changed update straight away
  // UI state
  const selectedPaperId = ref<string>('all')// asumme you wwant to see all papers initially
  const keyword = ref<string>('') //keyword starts empty

  // tags: use Set for easy toggle
  const selectedTags = ref<Set<string>>(new Set()) // since tags dcant have uplicates -> set

  // Options for the dropdown...turns papers into a list
  const paperOptions = computed<PaperOption[]>(() => [
    { id: 'all', label: 'All papers' },
    ...papers.map((p) => ({
      id: p.id,
      label: `${p.citation}  -  ${p.title}`,
    })),
  ])

  // its an alphab. sorted list of all unique tags , that exist in my findings
  const allTags = computed<string[]>(() => {
    const s = new Set<string>()
    for (const f of findings) for (const t of f.tags) s.add(t)
    return Array.from(s).sort((a, b) => a.localeCompare(b))
  })

  // Filtering, filters based on tags, keyword or selected papers
  const filteredFindings = computed<Finding[]>(() => {
    const k = normalizeText(keyword.value)
    const paperId = selectedPaperId.value
    const requiredTags = selectedTags.value

    return findings.filter((f) => {
      if (paperId !== 'all' && f.paperId !== paperId) return false

      if (k) {
        const hay = normalizeText(f.quote)
        if (!hay.includes(k)) return false
      }

      if (requiredTags.size > 0) {
        // AND logic: finding must include *all* selected tags
        for (const t of requiredTags) {
          if (!f.tags.includes(t)) return false
        }
      }

      // AND logic, so only if for the paper all req. are true..retrun true

      return true
    })
  })

  // Group results by paper...so after the filteredFinding Logic, group the findings per paper for better readability
  const groupedFindings = computed(() => {
    const byPaper = new Map<string, Finding[]>()
    for (const f of filteredFindings.value) {
      if (!byPaper.has(f.paperId)) byPaper.set(f.paperId, [])
      byPaper.get(f.paperId)!.push(f)
    }

    const groups: Array<{ paper: Paper; findings: Finding[] }> = []
    for (const p of papers) {
      const fs = byPaper.get(p.id)
      if (fs && fs.length) groups.push({ paper: p, findings: fs })
    }

    // If someone selects "all" but you have findings for papers not in `papers`, they won't show.
    // (Keep papers list complete and this stays fine.)
    return groups
  })

  // UI actions..so buttons user interacts with



  function toggleTag(tag: string) {//
    const s = new Set(selectedTags.value)
    if (s.has(tag)) s.delete(tag)
    else s.add(tag)
    selectedTags.value = s
  }

  function clearTags() {//turns of all tags
    selectedTags.value = new Set()
  }

  const resultsSubtitle = computed(() => { //generates the summarry/sentence that is on the right below findings
    const paperLabel =
      selectedPaperId.value === 'all'
        ? 'All papers'
        : papers.find((p) => p.id === selectedPaperId.value)?.citation ?? 'Selected paper'

    const tagPart =
      selectedTags.value.size === 0
        ? 'No tag filter'
        : `Tags: ${Array.from(selectedTags.value).join(', ')}`

    const keywordPart = keyword.value.trim() ? `Keyword: "${keyword.value.trim()}"` : 'No keyword'

    return `${paperLabel} • ${tagPart} • ${keywordPart}`
  })

  return {
    // state
    selectedPaperId,
    keyword,
    selectedTags,

    // data/options
    paperOptions,
    allTags,
    filteredFindings,
    groupedFindings,
    resultsSubtitle,

    // actions
    toggleTag,
    clearTags,
  }
}
