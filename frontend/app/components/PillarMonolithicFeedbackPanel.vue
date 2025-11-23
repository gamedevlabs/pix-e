<script setup lang="ts">
const pillars = usePillars()
const toast = useToast()

const isLoadingCoverage = ref(false)
const isLoadingContradictions = ref(false)
const isLoadingAdditions = ref(false)
const isLoadingAll = ref(false)
const acceptingSuggestion = ref<number | null>(null)

async function refreshCoverage() {
  isLoadingCoverage.value = true
  try {
    await pillars.getPillarsCompleteness()
  } finally {
    isLoadingCoverage.value = false
  }
}

async function refreshContradictions() {
  isLoadingContradictions.value = true
  try {
    await pillars.getPillarContradictions()
  } finally {
    isLoadingContradictions.value = false
  }
}

async function refreshAdditions() {
  isLoadingAdditions.value = true
  try {
    await pillars.getPillarsAdditions()
  } finally {
    isLoadingAdditions.value = false
  }
}

async function refreshAll() {
  isLoadingAll.value = true
  try {
    await pillars.getPillarsInContextFeedback()
  } finally {
    isLoadingAll.value = false
  }
}

async function handleAcceptAddition(suggestion: PillarDTO) {
  acceptingSuggestion.value = suggestion.pillarId
  try {
    await pillars.acceptAddition(suggestion.name, suggestion.description)
    await pillars.fetchAll()

    // Remove from suggestions list
    pillars.llmFeedback.value.proposedAdditions.additions =
      pillars.llmFeedback.value.proposedAdditions.additions.filter(
        (s) => s.pillarId !== suggestion.pillarId,
      )

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
  pillars.llmFeedback.value.proposedAdditions.additions =
    pillars.llmFeedback.value.proposedAdditions.additions.filter(
      (s) => s.pillarId !== suggestion.pillarId,
    )
  toast.add({
    title: 'Suggestion Declined',
    description: `"${suggestion.name}" has been dismissed.`,
    color: 'info',
  })
}

const hasCoverageData = computed(() => pillars.llmFeedback.value.coverage.pillarFeedback.length > 0)
const hasContradictionsData = computed(
  () => pillars.llmFeedback.value.contradictions.contradictions.length > 0,
)
const hasAdditionsData = computed(
  () => pillars.llmFeedback.value.proposedAdditions.additions.length > 0,
)
const hasAnyData = computed(
  () => hasCoverageData.value || hasContradictionsData.value || hasAdditionsData.value,
)
</script>

<template>
  <div class="space-y-6">
    <!-- Header with Refresh All Button -->
    <div class="flex items-center justify-between">
      <h2 class="text-2xl font-bold flex items-center gap-2">
        <UIcon name="i-heroicons-document-text" class="text-secondary-500" />
        Monolithic Feedback
      </h2>
      <UButton
        icon="i-lucide-refresh-cw"
        :label="isLoadingAll ? 'Loading...' : 'Refresh All'"
        color="secondary"
        :loading="isLoadingAll"
        @click="refreshAll"
      />
    </div>

    <!-- Results Grid -->
    <div v-if="hasAnyData" class="space-y-4">
      <!-- Coverage Section -->
      <UCard variant="subtle">
        <template #header>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <UIcon name="i-heroicons-puzzle-piece" class="text-blue-500" />
              <span class="font-semibold">Coverage</span>
            </div>
            <UButton
              size="xs"
              color="secondary"
              variant="ghost"
              icon="i-lucide-refresh-cw"
              :loading="isLoadingCoverage"
              @click="refreshCoverage"
            />
          </div>
        </template>

        <div v-if="hasCoverageData" class="space-y-3">
          <div
            v-for="feedback in pillars.llmFeedback.value.coverage.pillarFeedback"
            :key="feedback.pillarId"
            class="border-b border-gray-200 dark:border-gray-700 pb-3 last:border-0"
          >
            <h4 class="font-medium">{{ feedback.name }}</h4>
            <p class="text-sm text-gray-600 dark:text-gray-400">{{ feedback.reasoning }}</p>
          </div>
        </div>
        <p v-else class="text-sm text-gray-500">Click refresh to analyze pillar coverage.</p>
      </UCard>

      <!-- Contradictions Section -->
      <UCard variant="subtle">
        <template #header>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <UIcon name="i-heroicons-exclamation-triangle" class="text-red-500" />
              <span class="font-semibold">Contradictions</span>
            </div>
            <div class="flex items-center gap-2">
              <UBadge v-if="hasContradictionsData" color="error" variant="subtle" size="sm">
                {{ pillars.llmFeedback.value.contradictions.contradictions.length }} Found
              </UBadge>
              <UButton
                size="xs"
                color="secondary"
                variant="ghost"
                icon="i-lucide-refresh-cw"
                :loading="isLoadingContradictions"
                @click="refreshContradictions"
              />
            </div>
          </div>
        </template>

        <div v-if="hasContradictionsData" class="space-y-3">
          <div
            v-for="(contradiction, index) in pillars.llmFeedback.value.contradictions
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
        </div>
        <p v-else class="text-sm text-gray-500">
          Click refresh to detect contradictions between pillars.
        </p>
      </UCard>

      <!-- Additions Section -->
      <div>
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-2">
            <UIcon name="i-heroicons-plus-circle" class="text-primary-500" />
            <span class="font-semibold text-lg">Suggested Additions</span>
          </div>
          <div class="flex items-center gap-2">
            <UBadge v-if="hasAdditionsData" color="primary" variant="subtle" size="sm">
              {{ pillars.llmFeedback.value.proposedAdditions.additions.length }} Suggestions
            </UBadge>
            <UButton
              size="xs"
              color="secondary"
              variant="ghost"
              icon="i-lucide-refresh-cw"
              :loading="isLoadingAdditions"
              @click="refreshAdditions"
            />
          </div>
        </div>

        <div v-if="hasAdditionsData" class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <SuggestedPillarCard
            v-for="addition in pillars.llmFeedback.value.proposedAdditions.additions"
            :key="addition.pillarId"
            :suggestion="addition"
            :is-accepting="acceptingSuggestion === addition.pillarId"
            @accept="handleAcceptAddition"
            @decline="handleDeclineAddition"
          />
        </div>
        <p v-else class="text-sm text-gray-500">Click refresh to get pillar suggestions.</p>
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-else
      class="text-center py-12 text-gray-500 border border-dashed border-gray-300 dark:border-gray-700 rounded-lg"
    >
      <UIcon name="i-heroicons-document-text" class="text-4xl mb-2" />
      <p>Click "Refresh All" to run the monolithic feedback pipeline.</p>
      <p class="text-sm mt-1">Or use individual refresh buttons to check specific aspects.</p>

      <!-- Quick action buttons in empty state -->
      <div class="flex justify-center gap-2 mt-4">
        <UButton
          size="sm"
          color="secondary"
          variant="soft"
          icon="i-heroicons-puzzle-piece"
          label="Coverage"
          :loading="isLoadingCoverage"
          @click="refreshCoverage"
        />
        <UButton
          size="sm"
          color="secondary"
          variant="soft"
          icon="i-heroicons-exclamation-triangle"
          label="Contradictions"
          :loading="isLoadingContradictions"
          @click="refreshContradictions"
        />
        <UButton
          size="sm"
          color="secondary"
          variant="soft"
          icon="i-heroicons-plus-circle"
          label="Additions"
          :loading="isLoadingAdditions"
          @click="refreshAdditions"
        />
      </div>
    </div>
  </div>
</template>
