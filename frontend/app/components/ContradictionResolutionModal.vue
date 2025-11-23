<script setup lang="ts">
defineProps<{
  resolution: ContradictionResolutionResponse
}>()

const emit = defineEmits<{
  close: []
}>()
</script>

<template>
  <UModal
    class="max-w-4xl w-full"
    :close="{ onClick: () => emit('close') }"
    title="Contradiction Resolution Suggestions"
    :dismissible="true"
  >
    <template #body>
      <div class="space-y-6">
        <!-- Overall Recommendation -->
        <UCard v-if="resolution.overallRecommendation" variant="subtle">
          <template #header>
            <div class="flex items-center gap-2">
              <UIcon name="i-heroicons-light-bulb" class="text-yellow-500" />
              <span class="font-semibold">Overall Recommendation</span>
            </div>
          </template>
          <p class="text-sm">{{ resolution.overallRecommendation }}</p>
        </UCard>

        <!-- Resolution Suggestions -->
        <div class="space-y-4">
          <h3 class="font-semibold text-lg">Resolution Strategies</h3>

          <div
            v-for="(suggestion, index) in resolution.resolutions"
            :key="index"
            class="border rounded-lg p-4 space-y-3"
          >
            <!-- Pillars involved -->
            <div class="flex items-center gap-2 text-sm">
              <UBadge color="error" variant="subtle">
                {{ suggestion.pillarOneTitle }}
              </UBadge>
              <UIcon name="i-heroicons-arrows-right-left" class="text-gray-400" />
              <UBadge color="error" variant="subtle">
                {{ suggestion.pillarTwoTitle }}
              </UBadge>
            </div>

            <!-- Resolution Strategy -->
            <div class="border-l-2 border-primary-500 pl-4">
              <p class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
                Resolution Strategy:
              </p>
              <p class="text-sm">{{ suggestion.resolutionStrategy }}</p>
            </div>

            <!-- Suggested Changes -->
            <div v-if="suggestion.suggestedChanges.length">
              <p class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                Suggested Changes:
              </p>
              <ul class="list-disc list-inside space-y-1">
                <li
                  v-for="(change, changeIndex) in suggestion.suggestedChanges"
                  :key="changeIndex"
                  class="text-sm"
                >
                  {{ change }}
                </li>
              </ul>
            </div>

            <!-- Alternative Approach -->
            <div
              v-if="suggestion.alternativeApproach"
              class="bg-gray-50 dark:bg-gray-800 rounded p-3"
            >
              <p class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
                Alternative Approach:
              </p>
              <p class="text-sm italic">{{ suggestion.alternativeApproach }}</p>
            </div>
          </div>
        </div>

        <!-- Close Button -->
        <div class="flex justify-center pt-4">
          <UButton color="neutral" variant="outline" size="lg" @click="emit('close')">
            Close
          </UButton>
        </div>
      </div>
    </template>
  </UModal>
</template>
