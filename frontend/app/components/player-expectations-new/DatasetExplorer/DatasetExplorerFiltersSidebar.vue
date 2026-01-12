<!-- frontend/app/components/playerExpectationsNewDatasetExplorer/DatasetExplorerFiltersSidebar.vue -->
<script setup lang="ts">
/**
 * WHAT THIS COMPONENT IS
 *
 * This component renders the LEFT sidebar: genres, games, and code filters
 */

import { isRef } from 'vue'
import type { Ref } from 'vue'
import { GENRE_APPIDS, GAME_NAMES } from '~/composables/usePlayerExpectationsNewDatasetExplorer'

//describe the shape of the code lists used in the UI.
type CodeBtn = { code: number; label: string }
type Group = { top: number; label: string; subs: { code: number; label: string }[] }

// declares what props this component expects
const props = defineProps<{
  selectedGenres: Ref<Set<string>>
  selectedGames: Ref<Set<number>>
  visibleGames: Ref<number[]>

  selectedAestheticCodes: Ref<Set<number>>
  selectedFeatureCodes: Ref<Set<number>>
  selectedPainCodes: Ref<Set<number>>

  aestheticCodes: CodeBtn[]
  featureSearch: Ref<string>
  painSearch: Ref<string>
  filteredFeatureGroups: Group[]
  filteredPainGroups: Group[]

  clickGenre: (genre: string) => void
  clickGame: (appId: number) => void
  clickCode: (which: 'aesthetic' | 'feature' | 'pain', code: number) => void

  chipVariant: (selected: boolean) => 'soft' | 'outline'
}>()

//supports hasInSet functionality both for ref and a  normal set
function hasInSet<T>(setOrRef: Set<T> | Ref<Set<T>> | null | undefined, value: T): boolean {
  if (!setOrRef) return false
  const s = isRef(setOrRef) ? setOrRef.value : setOrRef
  return s.has(value)
}

// make tags more visible
function chipColor(selected: boolean) {
  return selected ? 'primary' : 'neutral'
}


</script>

<template>
  <div>
    <div class="card-header">
      <h3 class="font-semibold">Filters</h3>
    </div>

    <div class="card-scroll">
      <div class="space-y-6">
        <!-- GENRES -->
        <div>
          <h4 class="font-semibold mb-2">Genres</h4>
          <!-- Render one button per genre.-->
          <div class="flex flex-wrap gap-2">
            <UButton
              v-for="(_, genre) in GENRE_APPIDS"
              :key="genre"
              size="sm"
              :color="chipColor(hasInSet(selectedGenres, genre))"
              :variant="chipVariant(hasInSet(selectedGenres, genre))"
              @click="props.clickGenre(genre)"
            >
              {{ genre }}
            </UButton>
          </div>
        </div>

        <!-- GAMES -->
        <div>
          <h4 class="font-semibold mb-2">Games</h4>
          <div class="flex flex-wrap gap-2">
            <!-- visibleGames is a Ref<number[]>, so we use visibleGames.value -->
            <UButton
              v-for="id in visibleGames.value"
              :key="id"
              size="sm"
              :color="chipColor(hasInSet(selectedGames, id))"
              :variant="chipVariant(hasInSet(selectedGames, id))"
              @click="props.clickGame(id)"
            >
              {{ GAME_NAMES[id] || `App ${id}` }}
            </UButton>
          </div>
        </div>

        <!-- CODES -->
        <div>
          <h4 class="font-semibold mb-2">Content filters</h4>

          <!-- AESTHETICS: simple flat list -->
          <UAccordion :items="[{ label: 'Game Aesthetics', slot: 'aesthetics' }]">
            <template #aesthetics>
              <div class="mt-2 flex flex-col gap-1">
                <UButton
                  v-for="c in props.aestheticCodes"
                  :key="c.code"
                  size="xs"
                  :color="chipColor(hasInSet(selectedAestheticCodes, c.code))"
                  class="justify-start"
                  :variant="chipVariant(hasInSet(selectedAestheticCodes, c.code))"
                  @click="props.clickCode('aesthetic', c.code)"
                >
                  {{ c.label }}
                </UButton>
              </div>
            </template>
          </UAccordion>

          <!-- FEATURES: grouped list + search -->
          <UAccordion class="mt-3" :items="[{ label: 'Game Features', slot: 'features' }]">
            <template #features>
              <div class="mt-2 space-y-3">
                <UInput v-model="featureSearch.value" size="sm" placeholder="Quick search codes…" />
                <div class="space-y-3">
                  <div
                    v-for="g in props.filteredFeatureGroups"
                    :key="g.top"
                    class="border rounded p-2 border-slate-200 dark:border-slate-800"
                  >
                    <div class="flex items-center justify-between gap-2">
                      <UButton
                        size="xs"
                        class="justify-start"
                        :color="chipColor(hasInSet(selectedFeatureCodes, g.top))"
                        :variant="chipVariant(hasInSet(selectedFeatureCodes, g.top))"
                        @click="props.clickCode('feature', g.top)"
                      >
                        {{ g.label }}
                      </UButton>
                    </div>

                    <div v-if="g.subs.length" class="mt-2 flex flex-col gap-1">
                      <UButton
                        v-for="s in g.subs"
                        :key="s.code"
                        size="xs"
                        :color="chipColor(hasInSet(selectedFeatureCodes, s.code))"
                        class="justify-start"
                        :variant="chipVariant(hasInSet(selectedFeatureCodes, s.code))"
                        @click="props.clickCode('feature', s.code)"
                      >
                        {{ s.label }}
                      </UButton>
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </UAccordion>

          <!-- PAIN POINTS: grouped list + search -->
          <UAccordion class="mt-3" :items="[{ label: 'Pain Points', slot: 'pain' }]">
            <template #pain>
              <div class="mt-2 space-y-3">
                <UInput v-model="painSearch.value" size="sm" placeholder="Quick search codes…" />
                <div class="space-y-3">
                  <div
                    v-for="g in props.filteredPainGroups"
                    :key="g.top"
                    class="border rounded p-2 border-slate-200 dark:border-slate-800"
                  >
                    <div class="flex items-center justify-between gap-2">
                      <UButton
                        size="xs"
                        color="neutral"
                        class="justify-start"
                        :variant="chipVariant(hasInSet(selectedPainCodes, g.top))"
                        @click="props.clickCode('pain', g.top)"
                      >
                        {{ g.label }}
                      </UButton>
                    </div>

                    <div v-if="g.subs.length" class="mt-2 flex flex-col gap-1">
                      <UButton
                        v-for="s in g.subs"
                        :key="s.code"
                        size="xs"
                        color="neutral"
                        class="justify-start"
                        :variant="chipVariant(hasInSet(selectedPainCodes, s.code))"
                        @click="props.clickCode('pain', s.code)"
                      >
                        {{ s.label }}
                      </UButton>
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </UAccordion>
        </div>
      </div>
    </div>
  </div>
</template>
