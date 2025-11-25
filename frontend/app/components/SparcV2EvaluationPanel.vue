<script setup lang="ts">
const {
  v2Result,
  isEvaluating,
  evaluationError,
  reEvaluatingAspect,
  progressMessage,
  progressCurrent,
  progressTotal,
  pillarMode,
  runV2Evaluation,
  runAspectEvaluation,
  sortedAspectResults,
  wellDefinedCount,
  needsWorkCount,
  notProvidedCount,
} = useSparcV2()

const pillarModeOptions = [
  {
    value: 'smart',
    label: 'Smart',
    description: 'Intelligent pillar assignment per aspect',
  },
  { value: 'all', label: 'All', description: 'All pillars to all aspects' },
  { value: 'none', label: 'None', description: 'No pillar context' },
]

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}
</script>

<template>
  <div class="space-y-6">
    <!-- Controls -->
    <UCard>
      <div class="space-y-4">
        <!-- Action bar -->
        <div class="flex items-center justify-between gap-4 flex-wrap">
          <div class="flex items-center gap-4">
            <UButton
              size="lg"
              color="primary"
              icon="i-heroicons-play"
              label="Run Full Evaluation"
              :loading="isEvaluating"
              @click="runV2Evaluation"
            />

            <!-- Status counts -->
            <div v-if="v2Result" class="flex items-center gap-3 text-sm">
              <span class="text-green-400">
                <UIcon name="i-heroicons-check-circle" class="mr-1" />
                {{ wellDefinedCount }} defined
              </span>
              <span class="text-yellow-400">
                <UIcon name="i-heroicons-exclamation-triangle" class="mr-1" />
                {{ needsWorkCount }} need work
              </span>
              <span class="text-neutral-400">
                <UIcon name="i-heroicons-minus-circle" class="mr-1" />
                {{ notProvidedCount }} missing
              </span>
            </div>
          </div>

          <!-- Metadata -->
          <div v-if="v2Result" class="flex items-center gap-4 text-sm text-neutral-400">
            <span>
              <UIcon name="i-heroicons-clock" class="mr-1" />
              {{ formatDuration(v2Result.execution_time_ms) }}
            </span>
            <span>
              <UIcon name="i-heroicons-cpu-chip" class="mr-1" />
              {{ v2Result.total_tokens.toLocaleString() }} tokens
            </span>
            <span v-if="v2Result.estimated_cost_eur > 0">
              <UIcon name="i-heroicons-currency-euro" class="mr-1" />
              {{ v2Result.estimated_cost_eur.toFixed(4) }}
            </span>
            <span v-if="v2Result.pillars_count > 0" class="text-blue-400">
              <UIcon name="i-heroicons-square-3-stack-3d" class="mr-1" />
              {{ v2Result.pillars_count }} pillars
            </span>
          </div>
        </div>

        <!-- Pillar Mode Selector -->
        <div class="flex items-center gap-3">
          <label class="text-sm text-neutral-400 font-medium">Pillar Mode:</label>
          <USelect
            v-model="pillarMode"
            :items="pillarModeOptions"
            value-key="value"
            label-key="label"
            :disabled="isEvaluating"
            size="sm"
          />
          <span class="text-xs text-neutral-500">
            {{ pillarModeOptions.find((o) => o.value === pillarMode)?.description }}
          </span>
        </div>
      </div>

      <!-- Agent Execution Details (Collapsible) -->
      <UAccordion
        v-if="v2Result?.agent_execution_details"
        :items="[
          {
            label: 'Agent Execution Details',
            icon: 'i-heroicons-rectangle-group',
            defaultOpen: false,
            slot: 'agent-details',
          },
        ]"
        class="mt-4"
      >
        <template #agent-details>
          <SparcV2AgentDetailsAccordion :agent-details="v2Result.agent_execution_details" />
        </template>
      </UAccordion>

      <!-- Loading state with real-time progress -->
      <div v-if="isEvaluating" class="mt-4">
        <div class="flex items-center justify-between gap-2 text-sm mb-2">
          <div class="flex items-center gap-2 text-neutral-400">
            <UIcon name="i-heroicons-arrow-path" class="animate-spin" />
            {{ progressMessage || 'Running evaluation...' }}
          </div>
          <span v-if="progressCurrent > 0" class="text-neutral-500 text-xs">
            {{ progressCurrent }}/{{ progressTotal }}
          </span>
        </div>
        <UProgress
          :value="progressCurrent"
          :max="progressTotal"
          :color="progressCurrent === progressTotal ? 'success' : 'primary'"
        />
      </div>

      <!-- Error state -->
      <UAlert
        v-if="evaluationError"
        class="mt-4"
        color="error"
        variant="subtle"
        title="Evaluation Failed"
        :description="evaluationError"
      />
    </UCard>

    <!-- Results -->
    <template v-if="v2Result">
      <!-- Synthesis -->
      <SparcV2SynthesisCard v-if="v2Result.synthesis" :synthesis="v2Result.synthesis" />

      <!-- Aspect Results -->
      <div>
        <h2 class="text-lg font-semibold mb-4">Aspect Results</h2>
        <SparcV2AspectGrid
          :results="sortedAspectResults"
          :re-evaluating-aspect="reEvaluatingAspect"
          @re-evaluate="runAspectEvaluation"
        />
      </div>
    </template>

    <!-- Empty state -->
    <div v-else-if="!isEvaluating" class="text-center py-12 text-neutral-500">
      <UIcon name="i-heroicons-document-magnifying-glass" class="w-12 h-12 mx-auto mb-4" />
      <p class="text-lg">No evaluation results yet</p>
      <p class="text-sm mt-1">Enter a game concept and click "Run Full Evaluation" to start</p>
    </div>
  </div>
</template>
