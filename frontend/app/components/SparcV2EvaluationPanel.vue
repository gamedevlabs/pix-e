<script setup lang="ts">
const {
  v2Result,
  isEvaluating,
  evaluationError,
  reEvaluatingAspect,
  progressMessage,
  progressCurrent,
  progressTotal,
  evaluationMode,
  pillarMode,
  contextStrategy,
  uploadedDocument,
  runV2Evaluation,
  runAspectEvaluation,
  sortedAspectResults,
  wellDefinedCount,
  needsWorkCount,
  notProvidedCount,
  monolithicResult,
} = useSparcV2()

const evaluationModeOptions = [
  {
    value: 'agentic',
    label: 'Agentic',
    description: 'Multi-agent evaluation with per-aspect breakdown',
  },
  {
    value: 'monolithic',
    label: 'Monolithic',
    description: 'Single-pass evaluation for quick synthesis',
  },
]

const pillarModeOptions = [
  {
    value: 'smart',
    label: 'Smart',
    description: 'Intelligent pillar assignment per aspect',
  },
  { value: 'all', label: 'All', description: 'All pillars to all aspects' },
  { value: 'none', label: 'None', description: 'No pillar context' },
]

const contextStrategyOptions = [
  {
    value: 'router',
    label: 'Router',
    description: 'Router extracts aspect-specific context (default)',
  },
  {
    value: 'full_text',
    label: 'Full Text',
    description: 'All aspects receive the full game text',
  },
]
const fileInputRef = ref<HTMLInputElement | null>(null)
const fileError = ref<string>('')

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]

  if (!file) return

  // Validate file type
  const allowedTypes = ['pdf', 'docx', 'txt', 'md']
  const fileExt = file.name.split('.').pop()?.toLowerCase()

  if (!fileExt || !allowedTypes.includes(fileExt)) {
    fileError.value = `Invalid file type. Allowed: ${allowedTypes.join(', ')}`
    uploadedDocument.value = null
    return
  }

  // Validate file size (10MB)
  const maxSize = 10 * 1024 * 1024
  if (file.size > maxSize) {
    fileError.value = 'File too large. Maximum size is 10MB'
    uploadedDocument.value = null
    return
  }

  fileError.value = ''
  uploadedDocument.value = file
}

const isMonolithic = computed(() => evaluationMode.value === 'monolithic')

function clearFile() {
  uploadedDocument.value = null
  fileError.value = ''
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
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
            <div v-if="v2Result && !isMonolithic" class="flex items-center gap-3 text-sm">
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
          <div
            v-if="v2Result && !isMonolithic"
            class="flex items-center gap-4 text-sm text-neutral-400"
          >
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

        <!-- Evaluation Mode Selector -->
        <div class="flex items-center gap-3">
          <label class="text-sm text-neutral-400 font-medium">Evaluation Mode:</label>
          <USelect
            v-model="evaluationMode"
            :items="evaluationModeOptions"
            value-key="value"
            label-key="label"
            :disabled="isEvaluating"
            size="sm"
          />
          <span class="text-xs text-neutral-500">
            {{ evaluationModeOptions.find((o) => o.value === evaluationMode)?.description }}
          </span>
        </div>

        <!-- Pillar Mode Selector -->
        <div v-if="!isMonolithic" class="flex items-center gap-3">
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

        <div v-if="!isMonolithic" class="flex items-center gap-3">
          <label class="text-sm text-neutral-400 font-medium">Context Strategy:</label>
          <USelect
            v-model="contextStrategy"
            :items="contextStrategyOptions"
            value-key="value"
            label-key="label"
            :disabled="isEvaluating"
            size="sm"
          />
          <span class="text-xs text-neutral-500">
            {{ contextStrategyOptions.find((o) => o.value === contextStrategy)?.description }}
          </span>
        </div>

        <!-- Document Upload -->
        <div v-if="!isMonolithic" class="space-y-2">
          <label class="text-sm text-neutral-400 font-medium flex items-center gap-2">
            <UIcon name="i-heroicons-document-text" />
            Design Document (Optional)
          </label>
          <div class="flex items-center gap-3">
            <input
              ref="fileInputRef"
              type="file"
              accept=".pdf,.docx,.txt,.md"
              :disabled="isEvaluating"
              class="block w-full text-sm text-neutral-400 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-primary-500 file:text-white hover:file:bg-primary-600 file:cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              @change="handleFileChange"
            />
          </div>

          <!-- File preview -->
          <div
            v-if="uploadedDocument"
            class="flex items-center justify-between p-3 bg-neutral-800 rounded-lg"
          >
            <div class="flex items-center gap-3">
              <UIcon name="i-heroicons-document" class="text-primary-400" />
              <div>
                <p class="text-sm font-medium text-neutral-200">{{ uploadedDocument.name }}</p>
                <p class="text-xs text-neutral-500">{{ formatFileSize(uploadedDocument.size) }}</p>
              </div>
            </div>
            <UButton
              icon="i-heroicons-x-mark"
              color="neutral"
              variant="ghost"
              size="xs"
              :disabled="isEvaluating"
              @click="clearFile"
            />
          </div>

          <!-- File error -->
          <UAlert
            v-if="fileError"
            color="error"
            variant="subtle"
            :description="fileError"
            class="text-sm"
          />

          <p class="text-xs text-neutral-500">Supported: PDF, DOCX, TXT, MD • Max 10MB</p>
        </div>
      </div>

      <!-- Agent Execution Details (Collapsible) -->
      <UAccordion
        v-if="v2Result?.agent_execution_details && !isMonolithic"
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
            {{
              progressMessage ||
              (isMonolithic ? 'Running monolithic evaluation...' : 'Running evaluation...')
            }}
          </div>
          <span v-if="!isMonolithic && progressCurrent > 0" class="text-neutral-500 text-xs">
            {{ progressCurrent }}/{{ progressTotal }}
          </span>
        </div>
        <UProgress
          v-if="!isMonolithic"
          :value="progressCurrent"
          :max="progressTotal"
          :color="progressCurrent === progressTotal ? 'success' : 'primary'"
        />
        <UProgress v-else animation="carousel" />
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
    <template v-if="!isMonolithic && v2Result">
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

    <template v-else-if="isMonolithic && monolithicResult">
      <UCard>
        <template #header>
          <h2 class="text-xl font-bold">Overall Assessment</h2>
        </template>
        <p>{{ monolithicResult.overall_assessment }}</p>
      </UCard>

      <UCard>
        <template #header>
          <h2 class="text-xl font-bold">Readiness Verdict</h2>
        </template>
        <p>{{ monolithicResult.readiness_verdict }}</p>
      </UCard>

      <UCard>
        <template #header>
          <h2 class="text-xl font-bold">Aspects Evaluated</h2>
        </template>
        <div class="grid grid-cols-2 gap-4">
          <div
            v-for="aspect in monolithicResult.aspects_evaluated"
            :key="aspect.aspect_name"
            class="p-3 bg-neutral-800/50 rounded-lg"
          >
            <h4 class="font-semibold mb-1">{{ aspect.aspect_name }}</h4>
            <p class="text-sm text-neutral-300">{{ aspect.assessment }}</p>
          </div>
        </div>
      </UCard>

      <UCard v-if="monolithicResult.missing_aspects.length > 0" class="border-red-900">
        <template #header>
          <h3 class="text-lg font-bold text-red-500">Missing Aspects</h3>
        </template>
        <ul class="list-disc list-inside space-y-1">
          <li v-for="aspect in monolithicResult.missing_aspects" :key="aspect">
            {{ aspect }}
          </li>
        </ul>
      </UCard>

      <UCard class="border-blue-900">
        <template #header>
          <h3 class="text-lg font-bold text-blue-500">Suggestions</h3>
        </template>
        <ul class="list-disc list-inside space-y-1">
          <li v-for="suggestion in monolithicResult.suggestions" :key="suggestion">
            {{ suggestion }}
          </li>
        </ul>
      </UCard>
    </template>

    <!-- Empty state -->
    <div v-else-if="!isEvaluating" class="text-center py-12 text-neutral-500">
      <UIcon name="i-heroicons-document-magnifying-glass" class="w-12 h-12 mx-auto mb-4" />
      <p class="text-lg">
        {{ isMonolithic ? 'No monolithic results yet' : 'No evaluation results yet' }}
      </p>
      <p class="text-sm mt-1">
        {{
          isMonolithic
            ? 'Enter a game concept and run a monolithic evaluation to start'
            : 'Enter a game concept and click "Run Full Evaluation" to start'
        }}
      </p>
    </div>
  </div>
</template>
