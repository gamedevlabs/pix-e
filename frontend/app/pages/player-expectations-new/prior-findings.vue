<script setup lang="ts">
const {
  selectedPaperId,
  keyword,
  selectedTags,
  paperOptions,
  allTags,
  groupedFindings,
  filteredFindings,
  resultsSubtitle,
  toggleTag,
  clearTags,
} = usePriorFindings()
</script>

<template>
  <div class="p-6 space-y-6">
    <div class="space-y-1">
      <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-100">Prior Findings</h1>
      <p class="text-sm text-gray-600 dark:text-gray-300">
        Filter literature findings by paper, keyword, and tags.
      </p>
    </div>

    <!-- Desktop two-column layout, for control (left) and results (right)) -->
    <div class="flex items-start gap-6">
      <!-- Left: Filters + Tags (always visible) -->
      <UCard class="w-80 shrink-0">
        <template #header>
          <div class="space-y-5">
            <div>
              <label class="text-sm font-medium text-gray-700 dark:text-gray-200">Paper</label>
              <USelectMenu
                v-model="selectedPaperId"
                value-key="id"
                :items="paperOptions"
                :search-input="false"
                class="w-full mt-2"
              />
            </div>

            <div>
              <label class="text-sm font-medium text-gray-700 dark:text-gray-200">Keyword</label>
              <UInput
                v-model="keyword"
                placeholder="Search in findings…"
                class="w-full mt-2"
                size="lg"
              />  <!-- linked to keyword memore var...every update here triggers the logi in usepr... -->
            </div>
          </div>
        </template>

        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <h2 class="text-sm font-semibold text-gray-700 dark:text-gray-200">Tags</h2>
            <UButton
              size="xs"
              variant="ghost"
              :disabled="selectedTags.size === 0"
              @click="clearTags"
            >
              Clear
            </UButton>
          </div>

          <div class="flex flex-wrap gap-2">
            <UButton
              v-for="tag in allTags"
              :key="tag"
              size="xs"
              :variant="selectedTags.has(tag) ? 'solid' : 'soft'"
              @click="toggleTag(tag)"
            >        <!-- FOr every tag, loop and buld  button for each -->
              {{ tag }}
            </UButton>
          </div>

          <p class="text-xs text-gray-500 dark:text-gray-400">
            A finding must contain all selected tags to be shown.
          </p>
        </div>
      </UCard>

      <!-- Right: Results -->
      <div class="flex-1">
        <UCard>
          <template #header>
            <div class="flex items-start justify-between gap-4">
              <div class="space-y-1">
                <h2 class="text-xl font-semibold text-primary">Findings</h2>
                <p class="text-sm text-gray-600 dark:text-gray-300">
                  {{ resultsSubtitle }}
                </p>
              </div>
              <UBadge v-if="filteredFindings.length" variant="soft">
                {{ filteredFindings.length }}
              </UBadge>
            </div>
          </template>

          <div v-if="groupedFindings.length" class="space-y-6">
            <section v-for="group in groupedFindings" :key="group.paper.id" class="space-y-3">
              <div class="space-y-0.5">
                <h3 class="text-base font-semibold text-gray-900 dark:text-gray-100">
                  {{ group.paper.citation }} ({{ group.paper.year }})
                </h3>
                <p class="text-sm text-gray-600 dark:text-gray-300">
                  {{ group.paper.title }}
                </p>
              </div>

              <ul class="space-y-3">
                <li
                  v-for="f in group.findings"
                  :key="f.id"
                  class="rounded-md border border-gray-200 dark:border-gray-700 p-4"
                >
                  <p class="text-gray-900 dark:text-gray-100 leading-relaxed">
                    {{ f.quote }}
                  </p>

                  <div class="mt-3 flex flex-wrap gap-2">
                    <UBadge v-for="t in f.tags" :key="t" variant="soft">
                      {{ t }}
                    </UBadge>
                  </div>
                </li>
              </ul>
            </section>
          </div>

          <div v-else class="text-gray-600 dark:text-gray-300">
            No findings match the current filters.
          </div>
        </UCard>
      </div>
    </div>
  </div>
</template>
