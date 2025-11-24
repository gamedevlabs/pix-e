<script setup lang="ts">
import { formatAspectName } from '~/composables/useSparcV2'

const props = defineProps<{
  synthesis: SPARCSynthesis
}>()

const overallStatusColor = computed(() => {
  switch (props.synthesis.overall_status) {
    case 'ready':
      return 'success'
    case 'nearly_ready':
      return 'warning'
    case 'needs_work':
      return 'error'
    default:
      return 'neutral'
  }
})

const overallStatusLabel = computed(() => {
  switch (props.synthesis.overall_status) {
    case 'ready':
      return 'Ready for Prototyping'
    case 'nearly_ready':
      return 'Nearly Ready'
    case 'needs_work':
      return 'Needs Work'
    default:
      return 'Unknown'
  }
})

const overallStatusIcon = computed(() => {
  switch (props.synthesis.overall_status) {
    case 'ready':
      return 'i-heroicons-check-circle'
    case 'nearly_ready':
      return 'i-heroicons-clock'
    case 'needs_work':
      return 'i-heroicons-exclamation-triangle'
    default:
      return 'i-heroicons-question-mark-circle'
  }
})
</script>

<template>
  <UCard>
    <template #header>
      <div class="flex items-center justify-between">
        <h2 class="text-lg font-semibold">Synthesis</h2>
        <UBadge :color="overallStatusColor" :label="overallStatusLabel" size="lg">
          <template #leading>
            <UIcon :name="overallStatusIcon" />
          </template>
        </UBadge>
      </div>
    </template>

    <div class="space-y-4">
      <!-- Overall Reasoning -->
      <p>
        {{ synthesis.overall_reasoning }}
      </p>

      <!-- Strongest & Weakest -->
      <div
        :class="[
          'grid gap-4',
          synthesis.weakest_aspects.length > 0 ? 'grid-cols-1 md:grid-cols-2' : 'grid-cols-1',
        ]"
      >
        <!-- Strongest Aspects -->
        <div class="p-3 rounded-lg border border-green-800/50">
          <h4 class="text-sm font-medium text-green-400 mb-2 flex items-center gap-1">
            <UIcon name="i-heroicons-arrow-trending-up" />
            Strongest Aspects
          </h4>
          <ul class="space-y-1">
            <li v-for="aspect in synthesis.strongest_aspects" :key="aspect" class="text-sm">
              {{ formatAspectName(aspect) }}
            </li>
          </ul>
        </div>

        <!-- Weakest Aspects (only show if there are any) -->
        <div
          v-if="synthesis.weakest_aspects.length > 0"
          class="p-3 rounded-lg border border-red-800/50"
        >
          <h4 class="text-sm font-medium text-red-400 mb-2 flex items-center gap-1">
            <UIcon name="i-heroicons-arrow-trending-down" />
            Weakest Aspects
          </h4>
          <ul class="space-y-1">
            <li v-for="aspect in synthesis.weakest_aspects" :key="aspect" class="text-sm">
              {{ formatAspectName(aspect) }}
            </li>
          </ul>
        </div>
      </div>

      <!-- Critical Gaps -->
      <div
        v-if="synthesis.critical_gaps.length > 0"
        class="p-3 rounded-lg border border-yellow-800/50"
      >
        <h4 class="text-sm font-medium text-yellow-400 mb-2 flex items-center gap-1">
          <UIcon name="i-heroicons-exclamation-circle" />
          Critical Gaps (Blockers)
        </h4>
        <div class="flex flex-wrap gap-2">
          <span v-for="gap in synthesis.critical_gaps" :key="gap" class="text-sm">
            {{ formatAspectName(gap) }}
          </span>
        </div>
      </div>

      <!-- Next Steps -->
      <div>
        <h4 class="text-sm font-medium text-blue-400 mb-2 flex items-center gap-1">
          <UIcon name="i-heroicons-list-bullet" />
          Next Steps
        </h4>
        <ol class="space-y-2 list-decimal list-inside">
          <li v-for="(step, index) in synthesis.next_steps" :key="index" class="text-sm">
            {{ step }}
          </li>
        </ol>
      </div>

      <!-- Consistency Notes -->
      <div v-if="synthesis.consistency_notes" class="p-3 bg-neutral-800/50 rounded-lg">
        <h4 class="text-sm font-medium text-neutral-400 mb-1">Consistency Notes</h4>
        <p class="text-sm text-neutral-300">
          {{ synthesis.consistency_notes }}
        </p>
      </div>
    </div>
  </UCard>
</template>
