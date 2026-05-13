<script setup lang="ts">
import type { ProjectTargetPlatform } from '~/utils/project.d'
import { genreSuggestions } from '~/utils/platformConfig'
import TargetPlatformPicker from '~/components/TargetPlatformPicker.vue'

const genre = defineModel<string[]>('genre', { required: true })
const targetPlatform = defineModel<ProjectTargetPlatform[]>('targetPlatform', { required: true })

function selectGenre(g: string) {
  if (!genre.value.includes(g)) {
    genre.value = [...genre.value, g]
  }
}
</script>

<template>
  <UCard
    class="border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900"
    :ui="{ body: 'p-0' }"
  >
    <template #header>
      <div class="flex items-center gap-3">
        <div class="h-5 w-1 rounded-full bg-secondary-500" />
        <h2 class="text-base font-bold text-gray-900 dark:text-gray-100">Project Details</h2>
      </div>
    </template>

    <div class="px-5 pb-5 space-y-5">
      <UFormField label="Genre">
        <div class="space-y-2 w-full">
          <UInputTags
            v-model="genre"
            :placeholder="genre.length === 0 ? 'e.g. Action, Adventure, RPG…' : ''"
            size="md"
            icon="i-lucide-tag"
            :highlight="false"
            class="w-full"
          />
          <div class="flex flex-wrap gap-1.5">
            <UButton
              v-for="g in genreSuggestions"
              :key="g"
              size="xs"
              color="neutral"
              variant="soft"
              :label="g"
              :disabled="genre.includes(g)"
              @click="selectGenre(g)"
            />
          </div>
        </div>
      </UFormField>

      <TargetPlatformPicker v-model="targetPlatform" label="Target Platform" />
    </div>
  </UCard>
</template>
