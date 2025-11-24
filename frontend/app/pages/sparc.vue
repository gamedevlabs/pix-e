<script setup lang="ts">
definePageMeta({
  middleware: 'authentication',
})

const {
  gameConcept,
  context,
  quickScanResult,
  monolithicResult,
  isLoadingQuickScan,
  isLoadingMonolithic,
  fetchGameConcept,
  runQuickScan,
  runMonolithic,
  loadEvaluations,
} = useSparc()

await fetchGameConcept()
await loadEvaluations()

const selectedTab = ref<'quick_scan' | 'monolithic'>('quick_scan')

// Get readiness status color
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

// Get score color based on value
function getScoreColor(score: number) {
  if (score >= 80) return 'text-green-500'
  if (score >= 60) return 'text-blue-500'
  if (score >= 40) return 'text-yellow-500'
  return 'text-red-500'
}

// Handler functions for button clicks
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
  <div class="flex -m-10">
    <!-- Main Content -->
    <div class="flex-1 min-w-0 p-10">
      <h1 class="text-3xl font-bold mb-6">SPARC Evaluation</h1>

      <!-- Evaluation Controls -->
      <div class="mb-8 p-6 border border-neutral-800 rounded-lg">
        <h2 class="text-2xl font-bold mb-4">Run Evaluation</h2>
        <div class="flex gap-4">
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
            color="secondary"
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
            <div class="w-full bg-neutral-800 rounded-full h-2.5">
              <div class="bg-blue-600 h-2.5 rounded-full animate-pulse" style="width: 100%" />
            </div>
            <span class="text-sm text-neutral-400">
              {{ isLoadingQuickScan ? 'Running 10 agents in parallel...' : 'Processing...' }}
            </span>
          </div>
        </div>
      </div>

      <!-- Results Tabs -->
      <div class="border-b border-neutral-800 mb-6">
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
          <div class="p-6 border border-neutral-800 rounded-lg">
            <h2 class="text-2xl font-bold mb-4">Overall Readiness</h2>
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
                  :class="[
                    'text-2xl font-bold',
                    getReadinessColor(quickScanResult.readiness_status),
                  ]"
                >
                  {{ quickScanResult.readiness_status }}
                </p>
              </div>
            </div>

            <div class="mt-6">
              <p class="text-sm text-neutral-400 mb-2">Estimated Time to Ready</p>
              <p class="text-lg font-semibold">{{ quickScanResult.estimated_time_to_ready }}</p>
            </div>
          </div>

          <!-- Aspect Scores -->
          <div class="p-6 border border-neutral-800 rounded-lg">
            <h2 class="text-2xl font-bold mb-4">Aspect Scores</h2>
            <div class="grid grid-cols-2 gap-4">
              <div
                v-for="aspectScore in quickScanResult.aspect_scores"
                :key="aspectScore.aspect"
                class="p-4 rounded-lg"
              >
                <p class="text-sm text-neutral-400 mb-1">{{ aspectScore.aspect }}</p>
                <p :class="['text-2xl font-bold', getScoreColor(aspectScore.score)]">
                  {{ aspectScore.score }}/100
                </p>
              </div>
            </div>
          </div>

          <!-- Strengths and Gaps -->
          <div class="grid grid-cols-2 gap-6">
            <div class="p-6 border border-green-900 rounded-lg">
              <h3 class="text-xl font-bold mb-4 text-green-500">Strongest Aspects</h3>
              <ul class="list-disc list-inside space-y-2">
                <li v-for="aspect in quickScanResult.strongest_aspects" :key="aspect">
                  {{ aspect }}
                </li>
              </ul>
            </div>
            <div class="p-6 border border-red-900 rounded-lg">
              <h3 class="text-xl font-bold mb-4 text-red-500">Weakest Aspects</h3>
              <ul class="list-disc list-inside space-y-2">
                <li v-for="aspect in quickScanResult.weakest_aspects" :key="aspect">
                  {{ aspect }}
                </li>
              </ul>
            </div>
          </div>

          <!-- Critical Gaps -->
          <div class="p-6 border border-yellow-900 rounded-lg">
            <h3 class="text-xl font-bold mb-4 text-yellow-500">Critical Gaps</h3>
            <ul class="list-disc list-inside space-y-2">
              <li v-for="gap in quickScanResult.critical_gaps" :key="gap">
                {{ gap }}
              </li>
            </ul>
          </div>

          <!-- Next Steps -->
          <div class="p-6 border border-blue-900 rounded-lg">
            <h3 class="text-xl font-bold mb-4 text-blue-500">Next Steps</h3>
            <ol class="list-decimal list-inside space-y-2">
              <li v-for="step in quickScanResult.next_steps" :key="step">
                {{ step }}
              </li>
            </ol>
          </div>

          <!-- Individual Aspect Results -->
          <div class="p-6 border border-neutral-800 rounded-lg">
            <h2 class="text-2xl font-bold mb-6">Detailed Aspect Analysis</h2>
            <div class="space-y-6">
              <div
                v-for="aspect in [
                  'player_experience',
                  'theme',
                  'gameplay',
                  'place',
                  'unique_features',
                  'story_narrative',
                  'goals_challenges_rewards',
                  'art_direction',
                  'purpose',
                  'opportunities_risks',
                ]"
                :key="aspect"
              >
                <div
                  v-if="quickScanResult[aspect as keyof SPARCQuickScanResponse]"
                  class="p-4 rounded-lg"
                >
                  <h3 class="text-lg font-semibold mb-3 capitalize">
                    {{ aspect.replace(/_/g, ' ') }}
                    <span
                      :class="[
                        'ml-2',
                        getScoreColor(
                          (
                            quickScanResult[
                              aspect as keyof SPARCQuickScanResponse
                            ] as SPARCAspectResult
                          ).score,
                        ),
                      ]"
                    >
                      {{
                        (
                          quickScanResult[
                            aspect as keyof SPARCQuickScanResponse
                          ] as SPARCAspectResult
                        ).score
                      }}/100
                    </span>
                  </h3>

                  <div class="space-y-3">
                    <!-- Suggestions (common to all aspects) -->
                    <div
                      v-if="
                        (
                          quickScanResult[
                            aspect as keyof SPARCQuickScanResponse
                          ] as SPARCAspectResult
                        ).suggestions?.length
                      "
                    >
                      <p class="text-sm font-semibold text-blue-400 mb-2">Suggestions</p>
                      <ul class="list-disc list-inside text-sm space-y-1">
                        <li
                          v-for="suggestion in (
                            quickScanResult[
                              aspect as keyof SPARCQuickScanResponse
                            ] as SPARCAspectResult
                          ).suggestions"
                          :key="suggestion"
                        >
                          {{ suggestion }}
                        </li>
                      </ul>
                    </div>

                    <!-- Issues/Gaps (varies by aspect) -->
                    <div
                      v-if="
                        (
                          quickScanResult[
                            aspect as keyof SPARCQuickScanResponse
                          ] as SPARCAspectResult
                        ).issues?.length
                      "
                    >
                      <p class="text-sm font-semibold text-red-400 mb-2">Issues</p>
                      <ul class="list-disc list-inside text-sm space-y-1">
                        <li
                          v-for="issue in (
                            quickScanResult[
                              aspect as keyof SPARCQuickScanResponse
                            ] as SPARCAspectResult
                          ).issues"
                          :key="issue"
                        >
                          {{ issue }}
                        </li>
                      </ul>
                    </div>

                    <!-- Missing elements (some aspects) -->
                    <div
                      v-if="
                        (
                          quickScanResult[
                            aspect as keyof SPARCQuickScanResponse
                          ] as SPARCAspectResult
                        ).missing_elements?.length ||
                        (
                          quickScanResult[
                            aspect as keyof SPARCQuickScanResponse
                          ] as SPARCAspectResult
                        ).missing_theme_elements?.length
                      "
                    >
                      <p class="text-sm font-semibold text-yellow-400 mb-2">Missing Elements</p>
                      <ul class="list-disc list-inside text-sm space-y-1">
                        <li
                          v-for="missing in (
                            quickScanResult[
                              aspect as keyof SPARCQuickScanResponse
                            ] as SPARCAspectResult
                          ).missing_elements ||
                          (
                            quickScanResult[
                              aspect as keyof SPARCQuickScanResponse
                            ] as SPARCAspectResult
                          ).missing_theme_elements ||
                          []"
                          :key="missing"
                        >
                          {{ missing }}
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="text-center text-neutral-400 py-12">
          <p class="text-lg">No quick scan results yet. Click "Quick Scan" to run evaluation.</p>
        </div>
      </div>

      <!-- Monolithic Results -->
      <div v-if="selectedTab === 'monolithic'" class="space-y-6">
        <div v-if="monolithicResult" class="space-y-6">
          <!-- Overall Assessment -->
          <div class="p-6 border border-neutral-800 rounded-lg">
            <h2 class="text-2xl font-bold mb-4">Overall Assessment</h2>
            <p class="text-lg">{{ monolithicResult.overall_assessment }}</p>
          </div>

          <!-- Readiness Verdict -->
          <div class="p-6 border border-neutral-800 rounded-lg">
            <h2 class="text-2xl font-bold mb-4">Readiness Verdict</h2>
            <p class="text-lg">{{ monolithicResult.readiness_verdict }}</p>
          </div>

          <!-- Aspects Evaluated -->
          <div class="p-6 border border-neutral-800 rounded-lg">
            <h2 class="text-2xl font-bold mb-4">Aspects Evaluated</h2>
            <div class="grid grid-cols-2 gap-4">
              <div
                v-for="aspect in monolithicResult.aspects_evaluated"
                :key="aspect.aspect_name"
                class="p-4 rounded-lg"
              >
                <h3 class="font-semibold mb-2">{{ aspect.aspect_name }}</h3>
                <p class="text-sm">{{ aspect.assessment }}</p>
              </div>
            </div>
          </div>

          <!-- Missing Aspects -->
          <div
            v-if="monolithicResult.missing_aspects.length > 0"
            class="p-6 border border-red-900 rounded-lg"
          >
            <h3 class="text-xl font-bold mb-4 text-red-500">Missing Aspects</h3>
            <ul class="list-disc list-inside space-y-2">
              <li v-for="aspect in monolithicResult.missing_aspects" :key="aspect">
                {{ aspect }}
              </li>
            </ul>
          </div>

          <!-- Suggestions -->
          <div class="p-6 border border-blue-900 rounded-lg">
            <h3 class="text-xl font-bold mb-4 text-blue-500">Suggestions</h3>
            <ul class="list-disc list-inside space-y-2">
              <li v-for="suggestion in monolithicResult.suggestions" :key="suggestion">
                {{ suggestion }}
              </li>
            </ul>
          </div>

          <!-- Additional Details -->
          <div
            v-if="monolithicResult.additional_details.length > 0"
            class="p-6 border border-neutral-800 rounded-lg"
          >
            <h3 class="text-xl font-bold mb-4">Additional Details</h3>
            <ul class="list-disc list-inside space-y-2">
              <li v-for="detail in monolithicResult.additional_details" :key="detail">
                {{ detail }}
              </li>
            </ul>
          </div>
        </div>

        <div v-else class="text-center text-neutral-400 py-12">
          <p class="text-lg">No monolithic results yet. Click "Monolithic" to run evaluation.</p>
        </div>
      </div>
    </div>

    <!-- Game Concept Sidebar -->
    <GameConceptSidebar>
      <h2 class="text-2xl font-semibold mt-6 mb-4">Additional Context</h2>
      <UTextarea
        v-model="context"
        placeholder="Add any additional context or constraints..."
        variant="outline"
        color="secondary"
        size="xl"
        :rows="8"
        :max-rows="0"
        autoresize
        class="w-full"
      />

      <div class="mt-6 p-4 rounded-lg">
        <p class="text-xs text-neutral-400">
          SPARC evaluates 10 aspects: Player Experience, Theme, Gameplay, Place, Unique Features,
          Story & Narrative, Goals/Challenges/Rewards, Art Direction, Purpose, and Opportunities &
          Risks.
        </p>
      </div>
    </GameConceptSidebar>
  </div>
</template>
