<script setup lang="ts">
const {
  gameConcept,
  quickScanResult,
  monolithicResult,
  isLoadingQuickScan,
  isLoadingMonolithic,
  runQuickScan,
  runMonolithic,
} = useSparc()

const selectedTab = ref<'quick_scan' | 'monolithic'>('quick_scan')

function getReadinessColor(status: SPARCReadinessStatus) {
  switch (status) {
    case 'Ready':
      return 'text-green-500'
    case 'Nearly Ready':
      return 'text-blue-500'
    case 'Needs Work':
      return 'text-yellow-500'
    case 'Not Ready':
      return 'text-red-500'
    default:
      return 'text-gray-500'
  }
}

function getScoreColor(score: number) {
  if (score >= 80) return 'text-green-500'
  if (score >= 60) return 'text-blue-500'
  if (score >= 40) return 'text-yellow-500'
  return 'text-red-500'
}

function handleQuickScan() {
  runQuickScan()
  selectedTab.value = 'quick_scan'
}

function handleMonolithic() {
  runMonolithic()
  selectedTab.value = 'monolithic'
}
</script>

<template>
  <div class="space-y-6">
    <!-- Evaluation Controls -->
    <UCard>
      <div class="flex gap-4 flex-wrap">
        <UButton
          icon="i-lucide-zap"
          label="Quick Scan (10 Agents)"
          color="primary"
          variant="solid"
          size="lg"
          :loading="isLoadingQuickScan"
          :disabled="!gameConcept || isLoadingQuickScan || isLoadingMonolithic"
          @click="handleQuickScan"
        />
        <UButton
          icon="i-lucide-cpu"
          label="Monolithic"
          color="neutral"
          variant="solid"
          size="lg"
          :loading="isLoadingMonolithic"
          :disabled="!gameConcept || isLoadingQuickScan || isLoadingMonolithic"
          @click="handleMonolithic"
        />
      </div>

      <!-- Progress Indicator -->
      <div v-if="isLoadingQuickScan || isLoadingMonolithic" class="mt-4">
        <div class="flex items-center gap-3">
          <UProgress animation="carousel" class="flex-1" />
          <span class="text-sm text-neutral-400">
            {{ isLoadingQuickScan ? 'Running 10 agents in parallel...' : 'Processing...' }}
          </span>
        </div>
      </div>
    </UCard>

    <!-- Results Sub-Tabs -->
    <div class="border-b border-neutral-800">
      <div class="flex gap-4">
        <button
          :class="[
            'px-4 py-2 font-semibold transition-colors',
            selectedTab === 'quick_scan'
              ? 'border-b-2 border-primary-500 text-primary-500'
              : 'text-neutral-400 hover:text-neutral-200',
          ]"
          @click="selectedTab = 'quick_scan'"
        >
          Quick Scan Results
        </button>
        <button
          :class="[
            'px-4 py-2 font-semibold transition-colors',
            selectedTab === 'monolithic'
              ? 'border-b-2 border-primary-500 text-primary-500'
              : 'text-neutral-400 hover:text-neutral-200',
          ]"
          @click="selectedTab = 'monolithic'"
        >
          Monolithic Results
        </button>
      </div>
    </div>

    <!-- Quick Scan Results -->
    <div v-if="selectedTab === 'quick_scan'" class="space-y-6">
      <div v-if="quickScanResult" class="space-y-6">
        <!-- Overall Assessment -->
        <UCard>
          <template #header>
            <h2 class="text-xl font-bold">Overall Readiness</h2>
          </template>
          <div class="grid grid-cols-2 gap-6">
            <div>
              <p class="text-sm text-neutral-400 mb-1">Readiness Score</p>
              <p :class="['text-4xl font-bold', getScoreColor(quickScanResult.readiness_score)]">
                {{ quickScanResult.readiness_score }}/100
              </p>
            </div>
            <div>
              <p class="text-sm text-neutral-400 mb-1">Status</p>
              <p
                :class="['text-2xl font-bold', getReadinessColor(quickScanResult.readiness_status)]"
              >
                {{ quickScanResult.readiness_status }}
              </p>
            </div>
          </div>
          <div class="mt-4">
            <p class="text-sm text-neutral-400 mb-1">Estimated Time to Ready</p>
            <p class="text-lg font-semibold">{{ quickScanResult.estimated_time_to_ready }}</p>
          </div>
        </UCard>

        <!-- Aspect Scores -->
        <UCard>
          <template #header>
            <h2 class="text-xl font-bold">Aspect Scores</h2>
          </template>
          <div class="grid grid-cols-2 gap-4">
            <div
              v-for="aspectScore in quickScanResult.aspect_scores"
              :key="aspectScore.aspect"
              class="p-3 bg-neutral-800/50 rounded-lg"
            >
              <p class="text-sm text-neutral-400 mb-1">{{ aspectScore.aspect }}</p>
              <p :class="['text-2xl font-bold', getScoreColor(aspectScore.score)]">
                {{ aspectScore.score }}/100
              </p>
            </div>
          </div>
        </UCard>

        <!-- Strengths and Gaps -->
        <div class="grid grid-cols-2 gap-4">
          <UCard class="border-green-900">
            <template #header>
              <h3 class="text-lg font-bold text-green-500">Strongest Aspects</h3>
            </template>
            <ul class="list-disc list-inside space-y-1">
              <li v-for="aspect in quickScanResult.strongest_aspects" :key="aspect">
                {{ aspect }}
              </li>
            </ul>
          </UCard>
          <UCard class="border-red-900">
            <template #header>
              <h3 class="text-lg font-bold text-red-500">Weakest Aspects</h3>
            </template>
            <ul class="list-disc list-inside space-y-1">
              <li v-for="aspect in quickScanResult.weakest_aspects" :key="aspect">
                {{ aspect }}
              </li>
            </ul>
          </UCard>
        </div>

        <!-- Critical Gaps -->
        <UCard v-if="quickScanResult.critical_gaps.length > 0" class="border-yellow-900">
          <template #header>
            <h3 class="text-lg font-bold text-yellow-500">Critical Gaps</h3>
          </template>
          <ul class="list-disc list-inside space-y-1">
            <li v-for="gap in quickScanResult.critical_gaps" :key="gap">{{ gap }}</li>
          </ul>
        </UCard>

        <!-- Next Steps -->
        <UCard class="border-blue-900">
          <template #header>
            <h3 class="text-lg font-bold text-blue-500">Next Steps</h3>
          </template>
          <ol class="list-decimal list-inside space-y-1">
            <li v-for="step in quickScanResult.next_steps" :key="step">{{ step }}</li>
          </ol>
        </UCard>
      </div>

      <div v-else class="text-center text-neutral-400 py-12">
        <UIcon name="i-heroicons-document-magnifying-glass" class="w-12 h-12 mx-auto mb-4" />
        <p class="text-lg">No quick scan results yet</p>
        <p class="text-sm">Click "Quick Scan" to run evaluation</p>
      </div>
    </div>

    <!-- Monolithic Results -->
    <div v-if="selectedTab === 'monolithic'" class="space-y-6">
      <div v-if="monolithicResult" class="space-y-6">
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
      </div>

      <div v-else class="text-center text-neutral-400 py-12">
        <UIcon name="i-heroicons-document-magnifying-glass" class="w-12 h-12 mx-auto mb-4" />
        <p class="text-lg">No monolithic results yet</p>
        <p class="text-sm">Click "Monolithic" to run evaluation</p>
      </div>
    </div>
  </div>
</template>
