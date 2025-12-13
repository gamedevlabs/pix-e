<script setup lang="ts">
/**
 * Context Strategy Panel
 *
 * UI for comparing 4 context engineering strategies:
 * - Structural Memory (Zeng et al. 2024)
 * - Hierarchical Graph (deterministic)
 * - H-MEM (Sun & Zeng 2025)
 * - Combined
 */

import type {
  ComparisonResult,
  StrategyEvaluationResult,
  StrategyInfo,
  StrategyType,
} from '~/composables/useContextStrategies'

const props = defineProps<{
  chartId: string
  nodeId: string
  nodeName?: string
}>()

const emit = defineEmits<{
  (e: 'evaluation-complete', result: StrategyEvaluationResult): void
  (e: 'comparison-complete', result: ComparisonResult): void
}>()

const {
  availableStrategies,
  loading,
  lastEvaluation,
  lastComparison,
  fetchStrategies,
  evaluate,
  compare,
  clearResults,
  strategiesAgreement,
  bestStrategy,
} = useContextStrategies()

const selectedStrategy = ref<StrategyType>('structural_memory')
const showContextPreview = ref(false)
const activeTab = ref<'evaluate' | 'compare'>('evaluate')

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

function getStrategyColor(strategyId: string): string {
  const colors: Record<string, string> = {
    structural_memory: 'primary',
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

function getCoherenceColor(isCoherent: boolean): string {
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
            <UBadge :color="getStrategyColor(lastEvaluation.strategy)" variant="subtle">
              {{ lastEvaluation.strategy }}
            </UBadge>
          </div>

          <!-- Issues List -->
          <div v-if="lastEvaluation.issues.length > 0" class="space-y-2">
            <UAlert
              v-for="(issue, idx) in lastEvaluation.issues"
              :key="idx"
              :color="getSeverityColor(issue.severity)"
              variant="subtle"
              :title="issue.type"
              :description="issue.description"
            />
          </div>

          <!-- Context Metadata -->
          <UButton
            variant="ghost"
            size="xs"
            :icon="showContextPreview ? 'i-heroicons-chevron-up' : 'i-heroicons-chevron-down'"
            @click="showContextPreview = !showContextPreview"
          >
            {{ showContextPreview ? 'Hide' : 'Show' }} Context Metadata
          </UButton>

          <pre
            v-if="showContextPreview"
            class="text-xs bg-gray-100 dark:bg-gray-800 p-2 rounded overflow-auto max-h-48"
            >{{ JSON.stringify(lastEvaluation.context_metadata, null, 2) }}</pre
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
