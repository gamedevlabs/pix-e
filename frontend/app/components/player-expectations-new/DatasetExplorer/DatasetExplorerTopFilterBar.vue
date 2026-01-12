<!-- frontend/app/components/playerExpectationsNewDatasetExplorer/DatasetExplorerTopFilterBar.vue -->
<script setup lang="ts">
/**
 * WHAT THIS COMPONENT IS
 *
 * This is the TOP filter bar on the Dataset Explorer page.
 *
 * Important:
 * does not fetch data
 * receives the current selection state as props (mostly Vue refs)
 * When the user clicks something, it calls handler functions (also passed as props)
 *    -> Those handlers live in the view-model/core and usually trigger core.load()
 */
import type { Ref } from 'vue'

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
//fyi v-model="q.value" directly updates the shared state in the parent composable. Because we receive refs
defineProps<{
  q: Ref<string>
  recommended: Ref<Recommended>
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

  pageSize: Ref<number>

  loading: Ref<boolean>
  meta: Ref<Meta | null>

  prevPage: () => void
  nextPage: () => void
  setPolarity: (v: Recommended) => void
}>()
</script>

<template>
  <UCard>
    <!-- Row 1: Search + polarity + date range -->
    <div class="grid grid-cols-12 gap-3 items-end">
      <div class="col-span-12 lg:col-span-4">
        <label class="block text-xs font-medium mb-1 text-slate-600 dark:text-slate-300">Search</label>
        <UInput v-model="q.value" placeholder="Search review text…" size="md" />
      </div>

      <div class="col-span-12 lg:col-span-4">
        <label class="block text-xs font-medium mb-1 text-slate-600 dark:text-slate-300">Polarity</label>

        <div class="segmented">
          <button
            type="button"
            class="seg-btn"
            :class="recommended.value === 'all' ? 'seg-btn--on' : 'seg-btn--off'"
            @click="setPolarity('all')"
            :aria-pressed="recommended.value === 'all'"
          >
            Any
          </button>
          <button
            type="button"
            class="seg-btn"
            :class="recommended.value === 'recommended' ? 'seg-btn--on' : 'seg-btn--off'"
            @click="setPolarity('recommended')"
            :aria-pressed="recommended.value === 'recommended'"
          >
            Recommended
          </button>
          <button
            type="button"
            class="seg-btn"
            :class="recommended.value === 'not_recommended' ? 'seg-btn--on' : 'seg-btn--off'"
            @click="setPolarity('not_recommended')"
            :aria-pressed="recommended.value === 'not_recommended'"
          >
            Not recommended
          </button>
        </div>
      </div>

      <div class="col-span-6 lg:col-span-2">
        <label class="block text-xs font-medium mb-1 text-slate-600 dark:text-slate-300">Time from</label>
        <UInput v-model="dateFrom.value" type="date" size="md" />
      </div>

      <div class="col-span-6 lg:col-span-2">
        <label class="block text-xs font-medium mb-1 text-slate-600 dark:text-slate-300">Time to</label>
        <UInput v-model="dateTo.value" type="date" size="md" />
      </div>
    </div>

    <!-- Row 2: numeric range filters -->
    <div class="grid grid-cols-12 gap-3 mt-4">
      <div class="col-span-12 lg:col-span-3">
        <label class="block text-xs font-medium mb-1 text-slate-600 dark:text-slate-300">Helpful votes</label>
        <div class="flex gap-2">
          <!-- v-model.number converts the input string to a number automatically -->
          <UInput v-model.number="minVotesUp.value" type="number" placeholder="min" size="sm" />
          <UInput v-model.number="maxVotesUp.value" type="number" placeholder="max" size="sm" />
        </div>
      </div>

      <div class="col-span-12 lg:col-span-3">
        <label class="block text-xs font-medium mb-1 text-slate-600 dark:text-slate-300">Funny votes</label>
        <div class="flex gap-2">
          <UInput v-model.number="minVotesFunny.value" type="number" placeholder="min" size="sm" />
          <UInput v-model.number="maxVotesFunny.value" type="number" placeholder="max" size="sm" />
        </div>
      </div>

      <div class="col-span-12 lg:col-span-3">
        <label class="block text-xs font-medium mb-1 text-slate-600 dark:text-slate-300">Playtime at review</label>
        <div class="flex gap-2">
          <UInput v-model.number="minPlaytimeAtReview.value" type="number" placeholder="min" size="sm" />
          <UInput v-model.number="maxPlaytimeAtReview.value" type="number" placeholder="max" size="sm" />
        </div>
      </div>

      <div class="col-span-12 lg:col-span-3">
        <label class="block text-xs font-medium mb-1 text-slate-600 dark:text-slate-300">Playtime forever</label>
        <div class="flex gap-2">
          <UInput v-model.number="minPlaytimeForever.value" type="number" placeholder="min" size="sm" />
          <UInput v-model.number="maxPlaytimeForever.value" type="number" placeholder="max" size="sm" />
        </div>
      </div>
    </div>

    <!-- Row 3: sort + page size + loading + pagination buttons -->
    <div class="mt-4 flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-3">
        <div>
          <label class="block text-xs font-medium mb-1 text-slate-600 dark:text-slate-300">Sort</label>
          <select
            v-model="sort.value"
            class="h-7 rounded-md border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 px-3 text-sm"
          >
            <option value="newest">Newest</option>
            <option value="oldest">Oldest</option>
          </select>
        </div>

        <div>
          <label class="block text-xs font-medium mb-1 text-slate-600 dark:text-slate-300">Page size</label>
          <select
            v-model.number="pageSize.value"
            class="h-7 rounded-md border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 px-3 text-sm"
          >
            <option :value="100">100</option>
            <option :value="50">50</option>
            <option :value="200">200</option>
          </select>
        </div>

        <!-- Loading indicator  -->
        <div class="text-sm text-slate-500 dark:text-slate-400 mt-5">
          <span v-if="loading.value">Loading…</span>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <div v-if="meta.value" class="text-sm text-slate-600 dark:text-slate-300">
          Results: {{ meta.value.total.toLocaleString() }} — Page {{ meta.value.page }} / {{ meta.value.total_pages }}
        </div>

        <div class="flex gap-2">
          <UButton
            color="neutral"
            variant="outline"
            size="sm"
            @click="prevPage"
            :disabled="!meta.value || meta.value.page <= 1"
          >
            Prev
          </UButton>
          <UButton
            color="neutral"
            variant="outline"
            size="sm"
            @click="nextPage"
            :disabled="!meta.value || meta.value.page >= meta.value.total_pages"
          >
            Next
          </UButton>
        </div>
      </div>
    </div>
  </UCard>
</template>
