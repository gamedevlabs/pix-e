<script setup lang="ts">
import type { ProjectTargetPlatform } from '~/utils/project.d'
import { genreSuggestions } from '~/utils/platformConfig'
import TargetPlatformPicker from '~/components/TargetPlatformPicker.vue'

const genre = defineModel<string[]>('genre', { required: true })
const targetPlatform = defineModel<ProjectTargetPlatform[]>('targetPlatform', { required: true })

defineProps<{
  submitting?: boolean
  errors: { genre: string; targetPlatform: string }
}>()

function selectGenre(g: string) {
  if (!genre.value.includes(g)) {
    genre.value = [...genre.value, g]
  }
}
</script>

<template>
  <div class="space-y-6">
    <div>
      <h2 class="text-xl font-semibold mb-4">Project Details</h2>
      <p class="text-gray-600 dark:text-gray-400 mb-6">
        Tell us more about your project's genre and target platform
      </p>
    </div>

    <UFormField label="Genre" required>
      <UInputTags
        v-model="genre"
        :placeholder="genre.length === 0 ? 'e.g., Action, Adventure, RPG...' : ''"
        size="lg"
        :disabled="submitting"
        icon="i-heroicons-tag"
        :highlight="false"
      />
      <template #hint>
        <p class="text-xs text-gray-500">Add one or more genres that describe your game.</p>
      </template>

      <div class="mt-2">
        <div class="flex flex-wrap gap-2">
          <UButton
            v-for="g in genreSuggestions"
            :key="g"
            size="xs"
            color="neutral"
            variant="soft"
            :label="g"
            @click="selectGenre(g)"
          />
        </div>
      </div>
    </UFormField>

    <UFormField label="Target Platforms" required :error="errors.targetPlatform">
      <TargetPlatformPicker
        v-model="targetPlatform"
        :disabled="submitting"
        required
        :error="errors.targetPlatform"
        hint="Select the platforms you intend to release your game on."
      />
    </UFormField>
  </div>
</template>
