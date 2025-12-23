<script setup lang="ts">
/**
 * Context Strategy Panel
 *
 * UI for comparing context engineering strategies:
 * - Structural Memory (Zeng et al. 2024)
 * - Simple SM (summaries + triples + facts only)
 * - Hierarchical Graph (deterministic)
 * - H-MEM (Sun & Zeng 2025)
 * - Combined
 */

import {
  isAgenticResult,
  type AgenticEvaluationResult,
  type ComparisonResult,
  type EvaluationResult,
  type StrategyInfo,
  type StrategyType,
} from '~/composables/useContextStrategies'

const props = defineProps<{
  chartId: string
  nodeId: string
  nodeName?: string
}>()

const emit = defineEmits<{
  (e: 'evaluation-complete', result: EvaluationResult): void
  (e: 'comparison-complete', result: ComparisonResult): void
}>()

// Computed helpers for handling both result types
const evaluationStrategy = computed(() => {
  if (!lastEvaluation.value) return null
  return isAgenticResult(lastEvaluation.value)
    ? lastEvaluation.value.strategy_used
    : lastEvaluation.value.strategy
})

const evaluationIssues = computed(() => {
  if (!lastEvaluation.value) return []
  if (isAgenticResult(lastEvaluation.value)) {
    // Convert agentic critical_issues to display format
    return lastEvaluation.value.critical_issues.map((issue) => ({
      type: 'agentic',
      severity: 'warning' as const,
      description: issue,
      affected_nodes: [],
    }))
  }
  return lastEvaluation.value.issues
})

const evaluationScore = computed(() => {
  if (!lastEvaluation.value) return null
  return isAgenticResult(lastEvaluation.value) ? lastEvaluation.value.overall_score : null
})

const isAgentic = computed(() => {
  return lastEvaluation.value && isAgenticResult(lastEvaluation.value)
})

const agenticResult = computed(() => {
  if (!lastEvaluation.value || !isAgenticResult(lastEvaluation.value)) return null
  return lastEvaluation.value as AgenticEvaluationResult
})

const {
  availableStrategies,
  loading,
  lastEvaluation,
  lastComparison,
  executionMode,
  fetchStrategies,
  evaluate,
  compare,
  clearResults,
  setExecutionMode,
  strategiesAgreement,
  bestStrategy,
} = useContextStrategies()

const selectedStrategy = ref<StrategyType>('structural_memory')
const showContextPreview = ref(false)
const activeTab = ref<'evaluate' | 'compare'>('evaluate')

// Agent selection and expansion state for agentic mode
type AgentKey =
  | 'prerequisite_alignment'
  | 'forward_setup'
  | 'internal_consistency'
  | 'contextual_fit'
const selectedAgent = ref<AgentKey>('prerequisite_alignment')
const showIssues = ref(true)
const showSuggestions = ref(false)
const showReasoning = ref(false)

const agentLabels: Record<AgentKey, string> = {
  prerequisite_alignment: 'Prerequisite Alignment',
  forward_setup: 'Forward Setup',
  internal_consistency: 'Internal Consistency',
  contextual_fit: 'Contextual Fit',
}

const selectedAgentResult = computed(() => {
  if (!agenticResult.value) return null
  return agenticResult.value[selectedAgent.value]
})

// Fetch strategies on mount
onMounted(async () => {
  await fetchStrategies()
})

async function handleEvaluate() {
  const result = await evaluate({
    nodeId: props.nodeId,
    chartId: props.chartId,
    strategy: selectedStrategy.value,
  })

  if (result) {
    emit('evaluation-complete', result)
  }
}

async function handleCompareAll() {
  const result = await compare({
    nodeId: props.nodeId,
    chartId: props.chartId,
  })

  if (result) {
    emit('comparison-complete', result)
  }
}

type ColorType = 'primary' | 'secondary' | 'success' | 'info' | 'warning' | 'error' | 'neutral'

function getStrategyColor(strategyId: string): ColorType {
  const colors: Record<string, ColorType> = {
    structural_memory: 'primary',
    simple_sm: 'secondary',
    hierarchical_graph: 'success',
    hmem: 'warning',
    combined: 'info',
  }
  return colors[strategyId] || 'neutral'
}

function getSeverityColor(severity: string): 'error' | 'warning' | 'info' {
  const colors: Record<string, 'error' | 'warning' | 'info'> = {
    error: 'error',
    warning: 'warning',
    info: 'info',
  }
  return colors[severity] || 'info'
}

function getCoherenceIcon(isCoherent: boolean): string {
  return isCoherent ? 'i-heroicons-check-circle' : 'i-heroicons-x-circle'
}

function getCoherenceColor(isCoherent: boolean): 'success' | 'error' {
  return isCoherent ? 'success' : 'error'
}
</script>

<template>
  <UCard>
    <template #header>
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <UIcon name="i-heroicons-cpu-chip" class="text-lg" />
          <h3 class="font-semibold">Context Strategy Analysis</h3>
        </div>
        <UBadge v-if="nodeName" color="neutral" variant="subtle">
          {{ nodeName }}
        </UBadge>
      </div>
    </template>

    <template #default>
      <!-- Tab Buttons -->
      <div class="flex mb-4 border rounded-lg overflow-hidden">
        <button
          class="flex-1 flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium transition-colors"
          :class="
            activeTab === 'evaluate'
              ? 'bg-primary-500 text-white'
              : 'bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700'
          "
          @click="activeTab = 'evaluate'"
        >
          <UIcon name="i-heroicons-beaker" />
          Single Strategy
        </button>
        <button
          class="flex-1 flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium transition-colors"
          :class="
            activeTab === 'compare'
              ? 'bg-primary-500 text-white'
              : 'bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700'
          "
          @click="activeTab = 'compare'"
        >
          <UIcon name="i-heroicons-scale" />
          Compare All
        </button>
      </div>

      <!-- Execution Mode Toggle -->
      <div class="mb-4 flex items-center gap-3">
        <span class="text-sm text-gray-600 dark:text-gray-400">Execution Mode:</span>
        <div class="inline-flex rounded-md shadow-sm">
          <UButton
            :color="executionMode === 'monolithic' ? 'primary' : 'neutral'"
            :variant="executionMode === 'monolithic' ? 'solid' : 'outline'"
            icon="i-heroicons-cube"
            label="Monolithic"
            size="xs"
            class="rounded-r-none"
            @click="setExecutionMode('monolithic')"
          />
          <UButton
            :color="executionMode === 'agentic' ? 'primary' : 'neutral'"
            :variant="executionMode === 'agentic' ? 'solid' : 'outline'"
            icon="i-heroicons-cpu-chip"
            label="Agentic (4 Agents)"
            size="xs"
            class="rounded-l-none -ml-px"
            @click="setExecutionMode('agentic')"
          />
        </div>
      </div>

      <!-- Single Strategy Evaluation -->
      <div v-if="activeTab === 'evaluate'" class="space-y-4">
        <!-- Strategy Selector -->
        <div class="flex gap-2 flex-wrap">
          <UButton
            v-for="strategy in availableStrategies"
            :key="strategy.id"
            :color="selectedStrategy === strategy.id ? getStrategyColor(strategy.id) : 'neutral'"
            :variant="selectedStrategy === strategy.id ? 'solid' : 'outline'"
            size="sm"
            @click="selectedStrategy = strategy.id"
          >
            {{ strategy.name }}
          </UButton>
        </div>

        <!-- Strategy Description -->
        <div v-if="selectedStrategy" class="text-sm text-gray-600 dark:text-gray-400">
          {{
            availableStrategies.find((s: StrategyInfo) => s.id === selectedStrategy)?.description
          }}
        </div>

        <!-- Evaluate Button -->
        <UButton color="primary" :loading="loading" icon="i-heroicons-play" @click="handleEvaluate">
          Evaluate with
          {{ availableStrategies.find((s: StrategyInfo) => s.id === selectedStrategy)?.name }}
          ({{ executionMode === 'agentic' ? '4 agents' : 'single call' }})
        </UButton>

        <!-- Single Evaluation Result -->
        <div v-if="lastEvaluation" class="mt-4 space-y-3">
          <div class="flex items-center gap-2">
            <UIcon
              :name="getCoherenceIcon(lastEvaluation.is_coherent)"
              :class="`text-${getCoherenceColor(lastEvaluation.is_coherent)}-500`"
              class="text-xl"
            />
            <span class="font-medium">
              {{ lastEvaluation.is_coherent ? 'Coherent' : 'Issues Found' }}
            </span>
            <UBadge
              v-if="evaluationStrategy"
              :color="getStrategyColor(evaluationStrategy)"
              variant="subtle"
            >
              {{ evaluationStrategy }}
            </UBadge>
            <UBadge v-if="evaluationScore" color="info" variant="outline">
              Score: {{ evaluationScore }}/6
            </UBadge>
          </div>

          <!-- Agentic Mode: Selectable Agent Cards -->
          <div v-if="isAgentic && agenticResult" class="space-y-4">
            <!-- Agent Selector Grid -->
            <div class="grid grid-cols-4 gap-1">
              <button
                v-for="agentKey in [
                  'prerequisite_alignment',
                  'forward_setup',
                  'internal_consistency',
                  'contextual_fit',
                ] as AgentKey[]"
                :key="agentKey"
                class="p-2 rounded border text-center transition-all cursor-pointer"
                :class="
                  selectedAgent === agentKey
                    ? 'border-primary-500 bg-primary-50 dark:bg-primary-950 ring-2 ring-primary-500'
                    : 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 hover:border-primary-300'
                "
                @click="selectedAgent = agentKey"
              >
                <div class="text-[10px] font-medium truncate">{{ agentLabels[agentKey] }}</div>
                <div
                  v-if="agenticResult[agentKey]"
                  class="text-lg font-bold"
                  :class="
                    agenticResult[agentKey]!.score >= 4 ? 'text-green-600' : 'text-orange-500'
                  "
                >
                  {{ agenticResult[agentKey]!.score }}/6
                </div>
                <div v-if="agenticResult[agentKey]" class="text-[10px] text-gray-500">
                  {{ agenticResult[agentKey]!.issues.length }} issues
                </div>
              </button>
            </div>

            <!-- Selected Agent Details -->
            <div v-if="selectedAgentResult" class="border rounded-lg overflow-hidden">
              <div class="bg-primary-50 dark:bg-primary-950 px-3 py-2 border-b">
                <div class="flex items-center justify-between">
                  <span class="font-medium text-sm">{{ agentLabels[selectedAgent] }}</span>
                  <UBadge
                    :color="selectedAgentResult.score >= 4 ? 'success' : 'warning'"
                    variant="solid"
                  >
                    Score: {{ selectedAgentResult.score }}/6
                  </UBadge>
                </div>
              </div>

              <div class="p-3 space-y-3">
                <!-- Issues Section -->
                <div class="border rounded">
                  <button
                    class="w-full flex items-center justify-between px-3 py-2 text-sm font-medium bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700"
                    @click="showIssues = !showIssues"
                  >
                    <span class="flex items-center gap-2">
                      <UIcon name="i-heroicons-exclamation-triangle" class="text-orange-500" />
                      Issues ({{ selectedAgentResult.issues.length }})
                    </span>
                    <UIcon
                      :name="showIssues ? 'i-heroicons-chevron-up' : 'i-heroicons-chevron-down'"
                    />
                  </button>
                  <div
                    v-if="showIssues && selectedAgentResult.issues.length > 0"
                    class="p-2 space-y-1"
                  >
                    <div
                      v-for="(issue, idx) in selectedAgentResult.issues"
                      :key="idx"
                      class="text-sm p-2 bg-orange-50 dark:bg-orange-950 rounded text-orange-800 dark:text-orange-200"
                    >
                      {{ issue }}
                    </div>
                  </div>
                  <div v-else-if="showIssues" class="p-2 text-sm text-gray-500 italic">
                    No issues found
                  </div>
                </div>

                <!-- Suggestions Section -->
                <div class="border rounded">
                  <button
                    class="w-full flex items-center justify-between px-3 py-2 text-sm font-medium bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700"
                    @click="showSuggestions = !showSuggestions"
                  >
                    <span class="flex items-center gap-2">
                      <UIcon name="i-heroicons-light-bulb" class="text-blue-500" />
                      Suggestions ({{ selectedAgentResult.suggestions.length }})
                    </span>
                    <UIcon
                      :name="
                        showSuggestions ? 'i-heroicons-chevron-up' : 'i-heroicons-chevron-down'
                      "
                    />
                  </button>
                  <div
                    v-if="showSuggestions && selectedAgentResult.suggestions.length > 0"
                    class="p-2 space-y-1"
                  >
                    <div
                      v-for="(suggestion, idx) in selectedAgentResult.suggestions"
                      :key="idx"
                      class="text-sm p-2 bg-blue-50 dark:bg-blue-950 rounded text-blue-800 dark:text-blue-200"
                    >
                      {{ suggestion }}
                    </div>
                  </div>
                  <div v-else-if="showSuggestions" class="p-2 text-sm text-gray-500 italic">
                    No suggestions
                  </div>
                </div>

                <!-- Reasoning Section -->
                <div class="border rounded">
                  <button
                    class="w-full flex items-center justify-between px-3 py-2 text-sm font-medium bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700"
                    @click="showReasoning = !showReasoning"
                  >
                    <span class="flex items-center gap-2">
                      <UIcon name="i-heroicons-document-text" class="text-purple-500" />
                      Reasoning
                    </span>
                    <UIcon
                      :name="showReasoning ? 'i-heroicons-chevron-up' : 'i-heroicons-chevron-down'"
                    />
                  </button>
                  <div
                    v-if="showReasoning"
                    class="p-3 text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap"
                  >
                    {{ selectedAgentResult.reasoning }}
                  </div>
                </div>
              </div>
            </div>

            <!-- Execution Metadata -->
            <div class="text-xs text-gray-500 flex gap-4">
              <span>Execution: {{ agenticResult.execution_time_ms }}ms</span>
              <span>Tokens: {{ agenticResult.total_tokens }}</span>
            </div>
          </div>

          <!-- Monolithic Mode: Issues List -->
          <div v-if="!isAgentic && evaluationIssues.length > 0" class="space-y-2">
            <UAlert
              v-for="(issue, idx) in evaluationIssues"
              :key="idx"
              :color="getSeverityColor(issue.severity)"
              variant="subtle"
              :title="issue.type"
              :description="issue.description"
            />
          </div>

          <!-- Context Metadata Toggle -->
          <UButton
            variant="ghost"
            size="xs"
            :icon="showContextPreview ? 'i-heroicons-chevron-up' : 'i-heroicons-chevron-down'"
            @click="showContextPreview = !showContextPreview"
          >
            {{ showContextPreview ? 'Hide' : 'Show' }} Raw Result
          </UButton>

          <pre
            v-if="showContextPreview"
            class="text-xs bg-gray-100 dark:bg-gray-800 p-2 rounded overflow-auto max-h-48"
            >{{ JSON.stringify(lastEvaluation, null, 2) }}</pre
          >
        </div>
      </div>

      <!-- Compare All Strategies -->
      <div v-if="activeTab === 'compare'" class="space-y-4">
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Compare all 4 context strategies to see which performs best for this node. This is useful
          for thesis research on context engineering approaches.
        </p>

        <UButton
          color="primary"
          :loading="loading"
          icon="i-heroicons-scale"
          @click="handleCompareAll"
        >
          Compare All Strategies
        </UButton>

        <!-- Comparison Results -->
        <div v-if="lastComparison" class="mt-4 space-y-4">
          <!-- Summary -->
          <UCard>
            <template #header>
              <div class="flex items-center justify-between">
                <span class="font-medium">Comparison Summary</span>
                <UBadge :color="strategiesAgreement ? 'success' : 'warning'" variant="solid">
                  {{ strategiesAgreement ? 'All Agree' : 'Disagreement' }}
                </UBadge>
              </div>
            </template>

            <div class="space-y-2">
              <div v-if="bestStrategy" class="flex items-center gap-2">
                <span class="text-sm text-gray-600 dark:text-gray-400">Best performing:</span>
                <UBadge :color="getStrategyColor(bestStrategy)" variant="solid">
                  {{ bestStrategy }}
                </UBadge>
              </div>

              <!-- Strategy Grid -->
              <div class="grid grid-cols-2 gap-2 mt-3">
                <div
                  v-for="(result, strategyName) in lastComparison.strategies"
                  :key="strategyName"
                  class="p-3 rounded-lg border"
                  :class="
                    result.is_coherent
                      ? 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950'
                      : 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950'
                  "
                >
                  <div class="flex items-center justify-between mb-1">
                    <UBadge :color="getStrategyColor(strategyName as string)" size="xs">
                      {{ strategyName }}
                    </UBadge>
                    <UIcon
                      :name="getCoherenceIcon(result.is_coherent)"
                      :class="result.is_coherent ? 'text-green-500' : 'text-red-500'"
                    />
                  </div>
                  <div class="text-xs text-gray-600 dark:text-gray-400">
                    {{ result.issues.length }} issue(s)
                  </div>
                </div>
              </div>
            </div>
          </UCard>

          <!-- Detailed Results Per Strategy -->
          <UAccordion
            :items="
              Object.entries(lastComparison.strategies).map(([name, result]) => ({
                label: `${name} - ${result.is_coherent ? 'Coherent' : result.issues.length + ' issues'}`,
                slot: name,
                defaultOpen: !result.is_coherent,
              }))
            "
          >
            <template
              v-for="(result, strategyName) in lastComparison.strategies"
              :key="strategyName"
              #[strategyName]
            >
              <div class="space-y-2 p-2">
                <div v-if="result.issues.length === 0" class="text-sm text-green-600">
                  No issues found with this strategy.
                </div>
                <UAlert
                  v-for="(issue, idx) in result.issues"
                  :key="idx"
                  :color="getSeverityColor(issue.severity)"
                  variant="subtle"
                  :title="issue.type"
                  :description="issue.description"
                  size="xs"
                />
              </div>
            </template>
          </UAccordion>
        </div>
      </div>
    </template>

    <template #footer>
      <div class="flex justify-between items-center">
        <UButton
          v-if="lastEvaluation || lastComparison"
          variant="ghost"
          size="sm"
          icon="i-heroicons-trash"
          @click="clearResults"
        >
          Clear Results
        </UButton>
        <div class="text-xs text-gray-500">Thesis Research: Context Engineering Strategies</div>
      </div>
    </template>
  </UCard>
</template>
