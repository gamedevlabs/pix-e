<script setup lang="ts">
import { v4 } from 'uuid'

definePageMeta({
  middleware: 'authentication',
})

const {
  items: pxNodes,
  fetchAll: fetchPxNodes,
  createItem: createPxNode,
  deleteItem: deletePxNode,
} = usePxNodes()

const { items: pxCharts, fetchAll: fetchPxCharts } = usePxCharts()

const {
  loading: generatingMemory,
  evaluating: evaluatingCoherence,
  lastResult: memoryResult,
  lastEvaluation: evaluationResult,
  stats: chartStats,
  generate: generateMemory,
  getStats: getMemoryStats,
  evaluate: evaluateCoherence,
  clearEvaluation,
} = useStructuralMemory()

const state = ref({
  name: '',
  description: '',
})

// Structural memory generation state
const selectedChartIds = ref<string[]>([])
const showMemoryPanel = ref(false)
const forceRegenerate = ref(false)

// Computed chart options for multi-select
const chartOptions = computed(() =>
  pxCharts.value.map((chart) => ({
    label: chart.name,
    value: chart.id,
  })),
)

// Get stats for selected charts
const selectedChartStats = computed(() =>
  chartStats.value.filter((s) => selectedChartIds.value.includes(s.chart_id)),
)

const totalPendingNodes = computed(() =>
  selectedChartStats.value.reduce((sum, s) => sum + s.pending_nodes, 0),
)

const totalProcessedNodes = computed(() =>
  selectedChartStats.value.reduce((sum, s) => sum + s.processed_nodes, 0),
)

onMounted(async () => {
  await Promise.all([fetchPxNodes(), fetchPxCharts()])
})

async function handleCreate() {
  const newUuid = v4()
  await createPxNode({ id: newUuid, ...state.value })
  state.value.name = ''
  state.value.description = ''
}

// Not particularly efficient, but works for now.
// Problem is that I do not get the specified PxNodeCard to reload its components from here
async function handleForeignAddComponent() {
  pxNodes.value = []
  await fetchPxNodes()
}

// Structural Memory functions
function toggleMemoryPanel() {
  showMemoryPanel.value = !showMemoryPanel.value
  if (showMemoryPanel.value && selectedChartIds.value.length > 0) {
    refreshStats()
  }
}

async function refreshStats() {
  if (selectedChartIds.value.length > 0) {
    await getMemoryStats(selectedChartIds.value)
  }
}

async function handleGenerateMemory() {
  if (selectedChartIds.value.length === 0) {
    return
  }

  await generateMemory({
    chartIds: selectedChartIds.value,
    forceRegenerate: forceRegenerate.value,
  })

  // Refresh stats after generation
  await refreshStats()
}

// Watch for chart selection changes to refresh stats
watch(selectedChartIds, async (newIds) => {
  if (newIds.length > 0 && showMemoryPanel.value) {
    await refreshStats()
  }
  // Clear evaluation when charts change
  clearEvaluation()
})

// Evaluation function - only works with single chart selection
async function handleEvaluateCoherence() {
  if (selectedChartIds.value.length !== 1) {
    return
  }

  await evaluateCoherence({
    chartId: selectedChartIds.value[0],
  })
}

// Get severity badge color
function getSeverityColor(severity: string): string {
  switch (severity) {
    case 'error':
      return 'red'
    case 'warning':
      return 'amber'
    case 'info':
      return 'blue'
    default:
      return 'neutral'
  }
}

// Get issue type badge color
function getIssueTypeColor(type: string): string {
  switch (type) {
    case 'prerequisite':
      return 'red'
    case 'pacing':
      return 'amber'
    case 'story':
      return 'violet'
    case 'category':
      return 'cyan'
    default:
      return 'neutral'
  }
}
</script>

<template>
  <div class="p-4">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">Px Nodes</h1>
      <UButton
        :color="showMemoryPanel ? 'primary' : 'neutral'"
        variant="soft"
        icon="i-lucide-brain"
        @click="toggleMemoryPanel"
      >
        Structural Memory
      </UButton>
    </div>

    <!-- Structural Memory Panel -->
    <UCard v-if="showMemoryPanel" class="mb-6">
      <template #header>
        <div class="flex items-center gap-2">
          <UIcon name="i-lucide-brain" class="text-primary" />
          <span class="font-semibold">Generate Structural Memory</span>
        </div>
      </template>

      <div class="space-y-4">
        <!-- Chart Selection -->
        <div>
          <label class="block text-sm font-medium mb-2">Select Charts to Process</label>
          <USelectMenu
            v-model="selectedChartIds"
            :items="chartOptions"
            multiple
            placeholder="Select charts..."
            class="w-full md:w-1/2"
            value-key="value"
          />
        </div>

        <!-- Stats Display -->
        <div
          v-if="selectedChartIds.length > 0 && selectedChartStats.length > 0"
          class="grid grid-cols-2 md:grid-cols-4 gap-4"
        >
          <div class="bg-neutral-100 dark:bg-neutral-800 rounded-lg p-3">
            <div class="text-2xl font-bold text-primary">{{ totalPendingNodes }}</div>
            <div class="text-sm text-neutral-500">Pending Nodes</div>
          </div>
          <div class="bg-neutral-100 dark:bg-neutral-800 rounded-lg p-3">
            <div class="text-2xl font-bold text-green-600">{{ totalProcessedNodes }}</div>
            <div class="text-sm text-neutral-500">Up to Date</div>
          </div>
          <div class="bg-neutral-100 dark:bg-neutral-800 rounded-lg p-3">
            <div class="text-2xl font-bold">
              {{ selectedChartStats.reduce((sum, s) => sum + s.total_triples, 0) }}
            </div>
            <div class="text-sm text-neutral-500">Triples</div>
          </div>
          <div class="bg-neutral-100 dark:bg-neutral-800 rounded-lg p-3">
            <div class="text-2xl font-bold">
              {{ selectedChartStats.reduce((sum, s) => sum + s.total_facts, 0) }}
            </div>
            <div class="text-sm text-neutral-500">Facts</div>
          </div>
        </div>

        <!-- Options -->
        <div class="flex items-center gap-4">
          <UCheckbox v-model="forceRegenerate" label="Force regenerate all nodes" />
          <UButton
            variant="ghost"
            size="sm"
            icon="i-lucide-refresh-cw"
            :loading="generatingMemory"
            @click="refreshStats"
          >
            Refresh Stats
          </UButton>
        </div>

        <!-- Action Buttons -->
        <div class="flex gap-2 flex-wrap">
          <UButton
            color="primary"
            :loading="generatingMemory"
            :disabled="selectedChartIds.length === 0"
            icon="i-lucide-sparkles"
            @click="handleGenerateMemory"
          >
            {{ generatingMemory ? 'Generating...' : 'Generate Structural Memory' }}
          </UButton>

          <UButton
            color="violet"
            variant="soft"
            :loading="evaluatingCoherence"
            :disabled="selectedChartIds.length !== 1 || totalProcessedNodes === 0"
            icon="i-lucide-scan-search"
            @click="handleEvaluateCoherence"
          >
            {{ evaluatingCoherence ? 'Evaluating...' : 'Evaluate Coherence' }}
          </UButton>
          <span v-if="selectedChartIds.length > 1" class="text-sm text-neutral-500 self-center">
            (Select single chart to evaluate)
          </span>
        </div>

        <!-- Last Result -->
        <div v-if="memoryResult" class="mt-4 p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
          <div class="font-medium text-green-800 dark:text-green-200 mb-2">Generation Complete</div>
          <div class="text-sm text-green-700 dark:text-green-300 space-y-1">
            <p>Charts processed: {{ memoryResult.summary.charts_processed }}</p>
            <p>Nodes processed: {{ memoryResult.summary.nodes_processed }}</p>
            <p>Nodes skipped (unchanged): {{ memoryResult.summary.nodes_skipped }}</p>
            <p>Triples generated: {{ memoryResult.summary.total_triples }}</p>
            <p>Facts extracted: {{ memoryResult.summary.total_facts }}</p>
            <p>Embeddings stored: {{ memoryResult.summary.total_embeddings }}</p>
          </div>
        </div>

        <!-- Evaluation Results -->
        <div v-if="evaluationResult" class="mt-4">
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-2">
              <UIcon name="i-lucide-scan-search" class="text-violet-600" />
              <span class="font-semibold"
                >Coherence Evaluation: {{ evaluationResult.chart_name }}</span
              >
            </div>
            <UButton variant="ghost" size="xs" icon="i-lucide-x" @click="clearEvaluation" />
          </div>

          <!-- Summary -->
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            <div class="bg-violet-50 dark:bg-violet-900/20 rounded-lg p-3">
              <div class="text-2xl font-bold text-violet-700 dark:text-violet-300">
                {{ evaluationResult.summary.total_nodes }}
              </div>
              <div class="text-sm text-violet-600 dark:text-violet-400">Total Nodes</div>
            </div>
            <div class="bg-green-50 dark:bg-green-900/20 rounded-lg p-3">
              <div class="text-2xl font-bold text-green-700 dark:text-green-300">
                {{ evaluationResult.summary.coherent_nodes }}
              </div>
              <div class="text-sm text-green-600 dark:text-green-400">Coherent</div>
            </div>
            <div class="bg-red-50 dark:bg-red-900/20 rounded-lg p-3">
              <div class="text-2xl font-bold text-red-700 dark:text-red-300">
                {{ evaluationResult.summary.total_errors }}
              </div>
              <div class="text-sm text-red-600 dark:text-red-400">Errors</div>
            </div>
            <div class="bg-amber-50 dark:bg-amber-900/20 rounded-lg p-3">
              <div class="text-2xl font-bold text-amber-700 dark:text-amber-300">
                {{ evaluationResult.summary.total_warnings }}
              </div>
              <div class="text-sm text-amber-600 dark:text-amber-400">Warnings</div>
            </div>
          </div>

          <!-- Node Results -->
          <div class="space-y-3 max-h-96 overflow-y-auto">
            <div
              v-for="nodeResult in evaluationResult.nodes"
              :key="nodeResult.node_id"
              class="border rounded-lg p-3"
              :class="
                nodeResult.is_coherent
                  ? 'border-green-200 dark:border-green-800 bg-green-50/50 dark:bg-green-900/10'
                  : 'border-red-200 dark:border-red-800 bg-red-50/50 dark:bg-red-900/10'
              "
            >
              <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-2">
                  <UIcon
                    :name="
                      nodeResult.is_coherent ? 'i-lucide-check-circle' : 'i-lucide-alert-circle'
                    "
                    :class="nodeResult.is_coherent ? 'text-green-600' : 'text-red-600'"
                  />
                  <span class="font-medium">{{ nodeResult.node_name }}</span>
                </div>
                <UBadge :color="nodeResult.is_coherent ? 'green' : 'red'" variant="soft" size="sm">
                  {{ nodeResult.is_coherent ? 'Coherent' : 'Issues Found' }}
                </UBadge>
              </div>

              <!-- Issues -->
              <div v-if="nodeResult.issues.length > 0" class="space-y-2 mt-3">
                <div
                  v-for="(issue, idx) in nodeResult.issues"
                  :key="idx"
                  class="bg-white dark:bg-neutral-900 rounded p-2 text-sm"
                >
                  <div class="flex items-center gap-2 mb-1">
                    <UBadge :color="getSeverityColor(issue.severity)" variant="solid" size="xs">
                      {{ issue.severity.toUpperCase() }}
                    </UBadge>
                    <UBadge :color="getIssueTypeColor(issue.type)" variant="soft" size="xs">
                      {{ issue.type }}
                    </UBadge>
                  </div>
                  <p class="text-neutral-700 dark:text-neutral-300">{{ issue.description }}</p>
                  <div v-if="issue.affected_nodes.length > 0" class="text-xs text-neutral-500 mt-1">
                    Affected: {{ issue.affected_nodes.join(', ') }}
                  </div>
                </div>
              </div>

              <!-- Error -->
              <div v-if="nodeResult.error" class="mt-2 text-sm text-red-600 dark:text-red-400">
                Error: {{ nodeResult.error }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </UCard>

    <!-- Create Form -->
    <UForm :state="state" class="mb-6 space-y-4" @submit.prevent="handleCreate">
      <UFormField>
        <UInput v-model="state.name" type="text" placeholder="Name" class="w-full xl:w-1/2" />
      </UFormField>

      <UFormField>
        <UTextarea v-model="state.description" placeholder="Description" class="w-full xl:w-1/2" />
      </UFormField>

      <UButton type="submit">Create Node</UButton>
    </UForm>

    <!-- Cards Section -->
    <section class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6 items-start">
      <PxNodeCard
        v-for="node in pxNodes"
        :key="node.id"
        :node-id="node.id"
        :visualization-style="'detailed'"
        @delete="deletePxNode"
        @add-foreign-component="handleForeignAddComponent"
      />
    </section>
  </div>
</template>
