<script setup lang="ts">
import { ContradictionResolutionModal } from '#components'

const pillars = usePillars()
const toast = useToast()
const overlay = useOverlay()

const acceptingSuggestion = ref<number | null>(null)

async function handleAcceptAddition(suggestion: PillarDTO) {
  acceptingSuggestion.value = suggestion.pillarId
  try {
    await pillars.acceptAddition(suggestion.name, suggestion.description)
    await pillars.fetchAll()

    // Remove from suggestions list
    if (pillars.evaluationResult.value?.additions) {
      pillars.evaluationResult.value.additions.additions =
        pillars.evaluationResult.value.additions.additions.filter(
          (s) => s.pillarId !== suggestion.pillarId,
        )
    }

    toast.add({
      title: 'Pillar Added',
      description: `"${suggestion.name}" has been added to your pillars.`,
      color: 'success',
    })
  } catch (err) {
    console.error('Error accepting suggestion:', err)
    toast.add({
      title: 'Error',
      description: 'Failed to add pillar. Please try again.',
      color: 'error',
    })
  } finally {
    acceptingSuggestion.value = null
  }
}

function handleDeclineAddition(suggestion: PillarDTO) {
  if (pillars.evaluationResult.value?.additions) {
    pillars.evaluationResult.value.additions.additions =
      pillars.evaluationResult.value.additions.additions.filter(
        (s) => s.pillarId !== suggestion.pillarId,
      )
  }
  toast.add({
    title: 'Suggestion Declined',
    description: `"${suggestion.name}" has been dismissed.`,
    color: 'info',
  })
}

function openResolutionModal() {
  if (!pillars.evaluationResult.value?.resolution) return

  const modal = overlay.create(ContradictionResolutionModal, {
    props: {
      resolution: pillars.evaluationResult.value.resolution,
      onClose: () => modal.close(),
    },
  })
  modal.open()
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header with Evaluate Button -->
    <div class="flex items-center justify-between">
      <h2 class="text-2xl font-bold flex items-center gap-2">
        <UIcon name="i-heroicons-sparkles" class="text-primary-500" />
        Agentic Evaluation
      </h2>
      <UButton
        icon="i-heroicons-play"
        :label="pillars.isEvaluating.value ? 'Evaluating...' : 'Evaluate All'"
        color="primary"
        :loading="pillars.isEvaluating.value"
        @click="pillars.evaluateAll"
      />
    </div>

    <!-- Error State -->
    <UAlert
      v-if="pillars.evaluationError.value"
      color="error"
      variant="subtle"
      :title="pillars.evaluationError.value"
      :close-button="{ onClick: () => pillars.clearEvaluation() }"
    />

    <!-- Loading State -->
    <div v-if="pillars.isEvaluating.value" class="space-y-4">
      <UCard variant="subtle">
        <div class="flex items-center gap-4">
          <UIcon name="i-heroicons-sparkles" class="text-primary-500 animate-pulse text-2xl" />
          <div>
            <p class="font-semibold">Running evaluation agents...</p>
            <p class="text-sm text-gray-500">
              Analyzing concept fit, detecting contradictions, and generating suggestions.
            </p>
          </div>
        </div>
        <div class="mt-4 space-y-2">
          <USkeleton class="h-4 w-full rounded" />
          <USkeleton class="h-4 w-3/4 rounded" />
          <USkeleton class="h-4 w-1/2 rounded" />
        </div>
      </UCard>
    </div>

    <!-- Results -->
    <div v-else-if="pillars.evaluationResult.value" class="space-y-6">
      <!-- Metadata -->
      <div class="flex items-center gap-4 text-sm text-gray-500">
        <span>
          <UIcon name="i-heroicons-clock" class="mr-1" />
          {{ pillars.evaluationResult.value.metadata.execution_time_ms }}ms
        </span>
        <span>
          <UIcon name="i-heroicons-cpu-chip" class="mr-1" />
          {{ pillars.evaluationResult.value.metadata.agents_run.length }} agents
        </span>
        <UBadge
          :color="pillars.evaluationResult.value.metadata.all_succeeded ? 'success' : 'warning'"
          variant="subtle"
          size="xs"
        >
          {{
            pillars.evaluationResult.value.metadata.all_succeeded ? 'All Succeeded' : 'Some Failed'
          }}
        </UBadge>
      </div>

      <!-- Concept Fit Section -->
      <UCard v-if="pillars.evaluationResult.value.concept_fit" variant="subtle">
        <template #header>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <UIcon name="i-heroicons-puzzle-piece" class="text-blue-500" />
              <span class="font-semibold">Concept Fit</span>
            </div>
            <UBadge
              :color="pillars.evaluationResult.value.concept_fit.hasGaps ? 'warning' : 'success'"
              variant="subtle"
              size="sm"
            >
              {{
                pillars.evaluationResult.value.concept_fit.hasGaps ? 'Gaps Found' : 'Good Coverage'
              }}
            </UBadge>
          </div>
        </template>

        <div class="space-y-3">
          <div
            v-for="feedback in pillars.evaluationResult.value.concept_fit.pillarFeedback"
            :key="feedback.pillarId"
            class="border-b border-gray-200 dark:border-gray-700 pb-3 last:border-0"
          >
            <h4 class="font-medium">{{ feedback.name }}</h4>
            <p class="text-sm text-gray-600 dark:text-gray-400">{{ feedback.reasoning }}</p>
          </div>

          <div
            v-if="pillars.evaluationResult.value.concept_fit.missingAspects.length"
            class="mt-4 pt-4 border-t"
          >
            <p class="text-sm font-medium mb-2">Missing Aspects:</p>
            <div class="flex flex-wrap gap-2">
              <UBadge
                v-for="aspect in pillars.evaluationResult.value.concept_fit.missingAspects"
                :key="aspect"
                color="warning"
                variant="subtle"
              >
                {{ aspect }}
              </UBadge>
            </div>
          </div>
        </div>
      </UCard>

      <!-- Contradictions Section -->
      <UCard v-if="pillars.evaluationResult.value.contradictions" variant="subtle">
        <template #header>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <UIcon name="i-heroicons-exclamation-triangle" class="text-red-500" />
              <span class="font-semibold">Contradictions</span>
            </div>
            <div class="flex items-center gap-2">
              <UBadge
                :color="
                  pillars.evaluationResult.value.contradictions.hasContradictions
                    ? 'error'
                    : 'success'
                "
                variant="subtle"
                size="sm"
              >
                {{
                  pillars.evaluationResult.value.contradictions.hasContradictions
                    ? `${pillars.evaluationResult.value.contradictions.contradictions.length} Found`
                    : 'None Found'
                }}
              </UBadge>
              <UButton
                v-if="pillars.evaluationResult.value.resolution"
                size="xs"
                color="primary"
                variant="soft"
                icon="i-heroicons-light-bulb"
                label="View Resolutions"
                @click="openResolutionModal"
              />
            </div>
          </div>
        </template>

        <div class="space-y-3">
          <div
            v-for="(contradiction, index) in pillars.evaluationResult.value.contradictions
              .contradictions"
            :key="index"
            class="border-b border-gray-200 dark:border-gray-700 pb-3 last:border-0"
          >
            <div class="flex items-center gap-2 mb-1">
              <span class="font-medium">{{ contradiction.pillarOneTitle }}</span>
              <UIcon name="i-heroicons-arrows-right-left" class="text-gray-400" />
              <span class="font-medium">{{ contradiction.pillarTwoTitle }}</span>
            </div>
            <p class="text-sm text-gray-600 dark:text-gray-400">{{ contradiction.reason }}</p>
          </div>

          <p
            v-if="!pillars.evaluationResult.value.contradictions.contradictions.length"
            class="text-sm text-gray-500"
          >
            No contradictions detected between your pillars.
          </p>
        </div>
      </UCard>

      <!-- Suggested Additions Section -->
      <div v-if="pillars.evaluationResult.value.additions?.additions.length">
        <h3 class="font-semibold text-lg mb-3 flex items-center gap-2">
          <UIcon name="i-heroicons-plus-circle" class="text-primary-500" />
          Suggested Additions
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <SuggestedPillarCard
            v-for="suggestion in pillars.evaluationResult.value.additions.additions"
            :key="suggestion.pillarId"
            :suggestion="suggestion"
            :is-accepting="acceptingSuggestion === suggestion.pillarId"
            @accept="handleAcceptAddition"
            @decline="handleDeclineAddition"
          />
        </div>
      </div>

      <!-- Clear Results -->
      <div class="flex justify-center pt-4">
        <UButton
          color="neutral"
          variant="ghost"
          size="sm"
          icon="i-heroicons-x-mark"
          label="Clear Results"
          @click="pillars.clearEvaluation"
        />
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-else
      class="text-center py-12 text-gray-500 border border-dashed border-gray-300 dark:border-gray-700 rounded-lg"
    >
      <UIcon name="i-heroicons-sparkles" class="text-4xl mb-2" />
      <p>Click "Evaluate All" to run the agentic evaluation pipeline.</p>
      <p class="text-sm mt-1">
        This will analyze concept fit, detect contradictions, and suggest improvements.
      </p>
    </div>
  </div>
</template>
