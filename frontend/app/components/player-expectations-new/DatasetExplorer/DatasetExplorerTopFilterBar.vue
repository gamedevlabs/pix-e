<!-- frontend/app/components/playerExpectationsNewDatasetExplorer/DatasetExplorerTopFilterBar.vue -->
<script setup lang="ts">
/**
 * WHAT THIS COMPONENT IS
 *
 * This is the TOP filter bar on the Dataset Explorer page.
 *
 * Important:
 * does not fetch data
 * receives the current selection state as props (plain values)
 * uses v-model emitters to update parent state without mutating props
 * pagination buttons call prevPage/nextPage from parent
 * polarity buttons ALSO call setPolarity (if provided) so parent can trigger load/reset page, etc.
 */
import { computed } from 'vue'

//recommended can only be one of these three strings
type Recommended = 'all' | 'recommended' | 'not_recommended'

//describes the pagination info returned by the backend
//shown in the "Results: ... Page .../...
type Meta = {
  page: number
  page_size: number
  total: number
  total_pages: number
}

//declares what props this component expects.
const props = defineProps<{
  q: string
  recommended: Recommended
  sort: 'newest' | 'oldest'
  dateFrom: string
  dateTo: string

  minVotesUp: number | null
  maxVotesUp: number | null
  minVotesFunny: number | null
  maxVotesFunny: number | null
  minPlaytimeAtReview: number | null
  maxPlaytimeAtReview: number | null
  minPlaytimeForever: number | null
  maxPlaytimeForever: number | null

  pageSize: number
  loading: boolean
  meta: Meta | null

  prevPage: () => void
  nextPage: () => void

  setPolarity?: (v: Recommended) => void
}>()

type Emits = {
  'update:q': [string]
  'update:recommended': [Recommended]
  'update:sort': ['newest' | 'oldest']
  'update:dateFrom': [string]
  'update:dateTo': [string]

  'update:minVotesUp': [number | null]
  'update:maxVotesUp': [number | null]
  'update:minVotesFunny': [number | null]
  'update:maxVotesFunny': [number | null]
  'update:minPlaytimeAtReview': [number | null]
  'update:maxPlaytimeAtReview': [number | null]
  'update:minPlaytimeForever': [number | null]
  'update:maxPlaytimeForever': [number | null]

  'update:pageSize': [number]
}

const emit = defineEmits<Emits>()

// Helpers: computed setter wrappers so v-model works without mutating props
const qModel = computed({
  get: () => props.q,
  set: (v: string) => emit('update:q', v),
})

const sortModel = computed({
  get: () => props.sort,
  set: (v: 'newest' | 'oldest') => emit('update:sort', v),
})

const dateFromModel = computed({
  get: () => props.dateFrom,
  set: (v: string) => emit('update:dateFrom', v),
})

const dateToModel = computed({
  get: () => props.dateTo,
  set: (v: string) => emit('update:dateTo', v),
})

const pageSizeModel = computed({
  get: () => props.pageSize,
  set: (v: number) => emit('update:pageSize', v),
})

function numOrNull(v: unknown): number | null {
  if (v === '' || v === null || v === undefined) return null
  const n = Number(v)
  return Number.isFinite(n) ? n : null
}

const minVotesUpModel = computed({
  get: () => props.minVotesUp,
  set: (v: unknown) => emit('update:minVotesUp', numOrNull(v)),
})
const maxVotesUpModel = computed({
  get: () => props.maxVotesUp,
  set: (v: unknown) => emit('update:maxVotesUp', numOrNull(v)),
})
const minVotesFunnyModel = computed({
  get: () => props.minVotesFunny,
  set: (v: unknown) => emit('update:minVotesFunny', numOrNull(v)),
})
const maxVotesFunnyModel = computed({
  get: () => props.maxVotesFunny,
  set: (v: unknown) => emit('update:maxVotesFunny', numOrNull(v)),
})
const minPlaytimeAtReviewModel = computed({
  get: () => props.minPlaytimeAtReview,
  set: (v: unknown) => emit('update:minPlaytimeAtReview', numOrNull(v)),
})
const maxPlaytimeAtReviewModel = computed({
  get: () => props.maxPlaytimeAtReview,
  set: (v: unknown) => emit('update:maxPlaytimeAtReview', numOrNull(v)),
})
const minPlaytimeForeverModel = computed({
  get: () => props.minPlaytimeForever,
  set: (v: unknown) => emit('update:minPlaytimeForever', numOrNull(v)),
})
const maxPlaytimeForeverModel = computed({
  get: () => props.maxPlaytimeForever,
  set: (v: unknown) => emit('update:maxPlaytimeForever', numOrNull(v)),
})

function clickPolarity(v: Recommended) {
  emit('update:recommended', v)
  props.setPolarity?.(v)
}
</script>

<template>
  <UCard>
    <!-- Row 1: Search + polarity + date range -->
    <div class="grid grid-cols-12 gap-3 items-end">
      <div class="col-span-12 lg:col-span-4">
        <label class="block text-xs font-medium mb-1 text-slate-600 dark:text-slate-300">Search</label>
        <UInput v-model="qModel" placeholder="Search review text…" size="md" />
      </div>

      <div class="col-span-12 lg:col-span-4">
        <label class="block text-xs font-medium mb-1 text-slate-600 dark:text-slate-300">Polarity</label>

        <div class="segmented">
          <button
            type="button"
            class="seg-btn"
            :class="recommended === 'all' ? 'seg-btn--on' : 'seg-btn--off'"
            :aria-pressed="recommended === 'all'"
            @click="clickPolarity('all')"
          >
            Any
          </button>
          <button
            type="button"
            class="seg-btn"
            :class="recommended === 'recommended' ? 'seg-btn--on' : 'seg-btn--off'"
            :aria-pressed="recommended === 'recommended'"
            @click="clickPolarity('recommended')"
          >
            Recommended
          </button>
          <button
            type="button"
            class="seg-btn"
            :class="recommended === 'not_recommended' ? 'seg-btn--on' : 'seg-btn--off'"
            :aria-pressed="recommended === 'not_recommended'"
            @click="clickPolarity('not_recommended')"
          >
            Not recommended
          </button>
        </div>
      </div>

      <div class="col-span-6 lg:col-span-2">
        <label class="block text-xs font-medium mb-1 text-slate-600 dark:text-slate-300">Time from</label>
        <UInput v-model="dateFromModel" type="date" size="md" />
      </div>

      <div class="col-span-6 lg:col-span-2">
        <label class="block text-xs font-medium mb-1 text-slate-600 dark:text-slate-300">Time to</label>
        <UInput v-model="dateToModel" type="date" size="md" />
      </div>
    </div>

    <!-- Row 2: numeric range filters -->
    <div class="grid grid-cols-12 gap-3 mt-4">
      <div class="col-span-12 lg:col-span-3">
        <label class="block text-xs font-medium mb-1 text-slate-600 dark:text-slate-300">Helpful votes</label>
        <div class="flex gap-2">
          <!-- v-model.number converts the input string to a number automatically -->
          <UInput v-model="minVotesUpModel" type="number" placeholder="min" size="sm" />
          <UInput v-model="maxVotesUpModel" type="number" placeholder="max" size="sm" />
        </div>
      </div>

      <div class="col-span-12 lg:col-span-3">
        <label class="block text-xs font-medium mb-1 text-slate-600 dark:text-slate-300">Funny votes</label>
        <div class="flex gap-2">
          <UInput v-model="minVotesFunnyModel" type="number" placeholder="min" size="sm" />
          <UInput v-model="maxVotesFunnyModel" type="number" placeholder="max" size="sm" />
        </div>
      </div>

      <div class="col-span-12 lg:col-span-3">
        <label class="block text-xs font-medium mb-1 text-slate-600 dark:text-slate-300">Playtime at review</label>
        <div class="flex gap-2">
          <UInput v-model="minPlaytimeAtReviewModel" type="number" placeholder="min" size="sm" />
          <UInput v-model="maxPlaytimeAtReviewModel" type="number" placeholder="max" size="sm" />
        </div>
      </div>

      <div class="col-span-12 lg:col-span-3">
        <label class="block text-xs font-medium mb-1 text-slate-600 dark:text-slate-300">Playtime forever</label>
        <div class="flex gap-2">
          <UInput v-model="minPlaytimeForeverModel" type="number" placeholder="min" size="sm" />
          <UInput v-model="maxPlaytimeForeverModel" type="number" placeholder="max" size="sm" />
        </div>
      </div>
    </div>

    <!-- Row 3: sort + page size + loading + pagination buttons -->
    <div class="mt-4 flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-3">
        <div>
          <label class="block text-xs font-medium mb-1 text-slate-600 dark:text-slate-300">Sort</label>
          <select
            v-model="sortModel"
            class="h-7 rounded-md border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 px-3 text-sm"
          >
            <option value="newest">Newest</option>
            <option value="oldest">Oldest</option>
          </select>
        </div>

        <div>
          <label class="block text-xs font-medium mb-1 text-slate-600 dark:text-slate-300">Page size</label>
          <select
            v-model.number="pageSizeModel"
            class="h-7 rounded-md border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 px-3 text-sm"
          >
            <option :value="100">100</option>
            <option :value="50">50</option>
            <option :value="200">200</option>
          </select>
        </div>

        <!-- Loading indicator  -->
        <div class="text-sm text-slate-500 dark:text-slate-400 mt-5">
          <span v-if="loading">Loading…</span>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <div v-if="meta" class="text-sm text-slate-600 dark:text-slate-300">
          Results: {{ meta.total.toLocaleString() }} — Page {{ meta.page }} / {{ meta.total_pages }}
        </div>

        <div class="flex gap-2">
          <UButton color="neutral" variant="outline" size="sm" :disabled="!meta || meta.page <= 1" @click="prevPage">
            Prev
          </UButton>
          <UButton
            color="neutral"
            variant="outline"
            size="sm"
            :disabled="!meta || meta.page >= meta.total_pages"
            @click="nextPage"
          >
            Next
          </UButton>
        </div>
      </div>
    </div>
  </UCard>
</template>
