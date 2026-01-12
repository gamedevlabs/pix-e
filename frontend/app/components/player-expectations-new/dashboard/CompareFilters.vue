<!-- frontend/app/components/player-expectations-new/dashboard/CompareFilters.vue
renders the filter controls for ONE side of the compare dashboard
does not store state itself; it receives current values as props
When the user clicks buttons, it emits "update:*" events so the parent can update state -->
<script setup lang="ts">
import { computed } from 'vue'
import type { DashboardLanguage, DashboardPolarity } from '~/utils/playerExpectationsNewDashboard'

type Props = {
  title: string
  // UI sources
  genreToAppIds: Record<string, number[]>
  gameNames: Record<number, string>

  // v-model targets
  appIds: number[]
  polarity: DashboardPolarity
  languages: DashboardLanguage[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:appIds', v: number[]): void
  (e: 'update:polarity', v: DashboardPolarity): void
  (e: 'update:languages', v: DashboardLanguage[]): void
}>()

const genres = computed(() => Object.keys(props.genreToAppIds))

function setPolarity(v: DashboardPolarity) {
  emit('update:polarity', v)
}

function toggleLanguage(l: DashboardLanguage) {
  if (l === 'all') {
    emit('update:languages', ['all'])
    return
  }
  const cur = new Set(props.languages.filter((x) => x !== 'all'))
  if (cur.has(l)) cur.delete(l)
  else cur.add(l)
  const out = Array.from(cur)
  emit('update:languages', out.length ? out : ['all'])
}

/**
 * Toggle a whole genre.
 * If ANY game in that genre is already selected -> remove them all.
 * Otherwise -> add them all.
 */
function toggleGenre(genre: string) {
  const ids = props.genreToAppIds[genre] || []
  const cur = new Set(props.appIds)
  const anySelected = ids.some((id) => cur.has(id))
  if (anySelected) ids.forEach((id) => cur.delete(id))
  else ids.forEach((id) => cur.add(id))
  emit('update:appIds', Array.from(cur))
}

function toggleGame(appId: number) {
  const cur = new Set(props.appIds)
  if (cur.has(appId)) cur.delete(appId)
  else cur.add(appId)
  emit('update:appIds', Array.from(cur))
}

const visibleGames = computed(() => {
  const all = new Set<number>()
  for (const ids of Object.values(props.genreToAppIds)) ids.forEach((x) => all.add(x))
  return Array.from(all).sort((a, b) => a - b)
})

function chipVariant(selected: boolean) {
  return selected ? 'soft' : 'outline'
}

/** change color to make more vis */
function chipColor(selected: boolean) {
  return selected ? 'primary' : 'neutral'
}

/** same as above */
function segStyle(selected: boolean) {
  return selected
    ? { backgroundColor: 'var(--ui-primary)', color: 'white', fontWeight: '600' }
    : {}
}

// Helper: is a specific app ID currently selected?
function hasApp(id: number) {
  return props.appIds.includes(id)
}

// Helper: does this genre contain at least one selected app ID?
function hasAnyGenreSelected(genre: string) {
  const ids = props.genreToAppIds[genre] || []
  return ids.some((id) => hasApp(id))
}
</script>

<template>
  <div class="space-y-3">
    <!-- Title + selected count -->
    <div class="flex items-center justify-between">
      <h3 class="font-semibold">{{ title }}</h3>
      <div class="text-xs text-slate-500 dark:text-slate-400">
        {{ appIds.length }} game(s)
      </div>
    </div>

    <!-- Recommendation/ polarity -->
    <div>
      <div class="text-xs font-medium mb-1 text-slate-600 dark:text-slate-300">Recommendation</div>
      <div class="segmented">
        <button
          type="button"
          class="seg-btn"
          :class="polarity === 'any' ? 'seg-on' : 'seg-off'"
          :style="segStyle(polarity === 'any')"
          @click="setPolarity('any')"
        >
          Any
        </button>
        <button
          type="button"
          class="seg-btn"
          :class="polarity === 'rec' ? 'seg-on' : 'seg-off'"
          :style="segStyle(polarity === 'rec')"
          @click="setPolarity('rec')"
        >
          Recommended
        </button>
        <button
          type="button"
          class="seg-btn"
          :class="polarity === 'nrec' ? 'seg-on' : 'seg-off'"
          :style="segStyle(polarity === 'nrec')"
          @click="setPolarity('nrec')"
        >
          Not recommended
        </button>
      </div>
    </div>

    <!-- Language  (multiple selection, with "all" as the reset state-->
    <div>
      <div class="text-xs font-medium mb-1 text-slate-600 dark:text-slate-300">Language</div>
      <div class="flex gap-2">
        <UButton
          size="xs"
          :color="chipColor(languages.includes('all'))"
          :variant="chipVariant(languages.includes('all'))"
          @click="toggleLanguage('all')"
        >
          All
        </UButton>
        <UButton
          size="xs"
          :color="chipColor(languages.includes('english'))"
          :variant="chipVariant(languages.includes('english'))"
          @click="toggleLanguage('english')"
        >
          English
        </UButton>
        <UButton
          size="xs"
          :color="chipColor(languages.includes('schinese'))"
          :variant="chipVariant(languages.includes('schinese'))"
          @click="toggleLanguage('schinese')"
        >
          Chinese
        </UButton>
      </div>
    </div>

    <!-- Genre filters -->
    <div>
      <div class="text-xs font-medium mb-1 text-slate-600 dark:text-slate-300">Genres</div>
      <div class="flex flex-wrap gap-2">
        <UButton
          v-for="g in genres"
          :key="g"
          size="xs"
          :color="chipColor(hasAnyGenreSelected(g))"
          :variant="chipVariant(hasAnyGenreSelected(g))"
          @click="toggleGenre(g)"
        >
          {{ g }}
        </UButton>
      </div>
    </div>

    <!-- Individual game filter (OR logic: selecting more games expands the set) -->
    <div>
      <div class="text-xs font-medium mb-1 text-slate-600 dark:text-slate-300">Games (OR)</div>
      <div class="flex flex-wrap gap-2 max-h-44 overflow-y-auto pr-1">
        <UButton
          v-for="id in visibleGames"
          :key="id"
          size="xs"
          :color="chipColor(hasApp(id))"
          :variant="chipVariant(hasApp(id))"
          @click="toggleGame(id)"
        >
          {{ gameNames[id] || `App ${id}` }}
        </UButton>
      </div>
    </div>
  </div>
</template>

<style scoped>
.segmented {
  height: 30px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.22);
  background: rgba(148, 163, 184, 0.08);
}
.seg-btn {
  height: 30px;
  font-size: 0.82rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-right: 1px solid rgba(148, 163, 184, 0.22);
}
.seg-btn:last-child {
  border-right: none;
}

/* Selected state (primary) */
.seg-on {
  background: var(--ui-primary);
  color: white;
  font-weight: 600;
}

/* Non-selected */
.seg-off {
  background: transparent;
  opacity: 0.9;
}
</style>
