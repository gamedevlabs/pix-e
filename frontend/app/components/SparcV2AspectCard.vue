<script setup lang="ts">
import { formatAspectName, getStatusColor } from '~/composables/useSparcV2'

const props = defineProps<{
  aspectName: string
  result: SimplifiedAspectResponse
  isReEvaluating?: boolean
}>()

const emit = defineEmits<{
  (event: 'reEvaluate'): void
}>()

const showAllSuggestions = ref(false)

const displayedSuggestions = computed(() => {
  if (showAllSuggestions.value || props.result.suggestions.length <= 2) {
    return props.result.suggestions
  }
  return props.result.suggestions.slice(0, 2)
})

const hasMoreSuggestions = computed(() => props.result.suggestions.length > 2)

const statusLabel = computed(() => {
  switch (props.result.status) {
    case 'well_defined':
      return 'Well Defined'
    case 'needs_work':
      return 'Needs Work'
    case 'not_provided':
      return 'Not Provided'
    default:
      return 'Unknown'
  }
})
</script>

<template>
  <UCard
    class="h-full"
    :ui="{
      root: 'flex flex-col',
      body: 'flex-1',
    }"
  >
    <template #header>
      <div class="flex items-center justify-between gap-2">
        <h3 class="font-semibold text-base">
          {{ formatAspectName(aspectName) }}
        </h3>
        <UBadge :color="getStatusColor(result.status)" :label="statusLabel" size="sm" />
      </div>
    </template>

    <div class="space-y-3">
      <!-- Reasoning -->
      <p class="text-sm text-neutral-400">
        {{ result.reasoning }}
      </p>

      <!-- Suggestions -->
      <div v-if="result.suggestions.length > 0">
        <h4 class="text-xs font-medium text-neutral-500 mb-1">Suggestions</h4>
        <ul class="space-y-1">
          <li
            v-for="(suggestion, index) in displayedSuggestions"
            :key="index"
            class="text-sm flex items-start gap-1.5"
          >
            <UIcon name="i-heroicons-light-bulb" class="text-yellow-500 mt-0.5 shrink-0" />
            <span>{{ suggestion }}</span>
          </li>
        </ul>
        <UButton
          v-if="hasMoreSuggestions"
          size="xs"
          variant="ghost"
          color="neutral"
          class="mt-1"
          :label="showAllSuggestions ? 'Show less' : `+${result.suggestions.length - 2} more`"
          @click="showAllSuggestions = !showAllSuggestions"
        />
      </div>
    </div>

    <template #footer>
      <UButton
        size="sm"
        variant="subtle"
        color="neutral"
        icon="i-lucide-refresh-cw"
        label="Re-evaluate"
        :loading="isReEvaluating"
        block
        @click="emit('reEvaluate')"
      />
    </template>
  </UCard>
</template>
