<script setup lang="ts">
// ============================================================================
// PAGE CONFIG - Edit these settings for this module
// ============================================================================
definePageMeta({
  middleware: ['authentication', 'project-context'],
  pageConfig: {
    type: 'project-required',
    showSidebar: true,
    title: 'Dashboard',
    icon: 'i-lucide-house',
  },
})
// ============================================================================

const { currentProject, currentProjectId } = useProjectHandler()

// Fetch real data from modules
const { items: pillars, fetchAll: fetchPillars } = usePillars()
const { items: pxCharts, fetchAll: fetchPxCharts } = usePxCharts()

onMounted(() => {
  fetchPillars()
  fetchPxCharts()
})

// Helper function to generate initials from project name
const getProjectInitials = (name: string) => {
  if (!name) return 'P'
  const parts = name.split(/\s+/).filter(Boolean)
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[1][0]).toUpperCase()
}

// Example workflow data - will be replaced with real data later
const workflowSteps = computed(() => {
  // Track completion status
  const hasProject = !!currentProject.value
  const hasCharts = pxCharts.value.length > 0
  const hasExpectations = false // TODO: Add real check when player expectations data is available
  const hasPillars = pillars.value.length > 0

  return [
    {
      title: 'Create Project',
      description: 'Set up your game project',
      icon: hasProject ? 'i-lucide-check-circle' : 'i-lucide-folder-plus',
    },
    {
      title: 'Create first PX Chart',
      description: 'Build your experience model',
      icon: hasCharts ? 'i-lucide-check-circle' : 'i-lucide-network',
    },
    {
      title: 'Analyze Player Expectations',
      description: 'Define player expectations',
      icon: hasExpectations ? 'i-lucide-check-circle' : 'i-lucide-users',
    },
    {
      title: 'Create Pillars',
      description: 'Define design pillars',
      icon: hasPillars ? 'i-lucide-check-circle' : 'i-lucide-landmark',
    },
    {
      title: 'Continue Development',
      description: 'Build and refine your game',
      icon: 'i-lucide-rocket',
    },
  ]
})

const currentWorkflowStep = ref(1) // Currently on Research step

// Navigate to specific module with project context
const navigateToModule = (route: string) => {
  const projectQuery = currentProjectId.value ? `?id=${currentProjectId.value}` : ''
  navigateTo(`${route}${projectQuery}`)
}
</script>

<template>
  <UPage>
    <UPageBody>
      <UPageGrid :ui="{ root: 'grid-cols-1 lg:grid-cols-[2fr,2fr,1fr] gap-6' }">
        <!-- Project Information (Spans 2 columns, No Card Border) -->
        <div class="col-span-2">
          <!-- Settings Button - Top Right -->
          <div class="flex justify-end mb-4">
            <UButton
              icon="i-lucide-settings"
              size="sm"
              color="gray"
              variant="ghost"
              label="Settings"
              @click="navigateToModule('/edit')"
            />
          </div>

          <!-- Two Column Layout: Title/Icon Left, Info Right -->
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Left Column: Project Name and Icon -->
            <div class="flex items-center gap-4">
              <!-- Project Icon or Initials -->
              <div v-if="currentProject?.icon" class="text-6xl">
                {{ currentProject.icon }}
              </div>
              <UAvatar
                v-else
                :text="getProjectInitials(currentProject?.name || 'Project')"
                :alt="currentProject?.name || 'Project'"
                size="3xl"
                class="text-2xl font-bold"
              />
              <div>
                <h1 class="text-4xl font-bold mb-1">{{ currentProject?.name || 'Project' }}</h1>
                <p class="text-gray-500 dark:text-gray-400">Design games with research.</p>
              </div>
            </div>

            <!-- Right Column: Project Information -->
            <div class="bg-gray-50 dark:bg-gray-900/20 rounded-lg p-4">
              <div class="flex items-center gap-2 mb-3">
                <UIcon name="i-lucide-info" class="text-gray-500 dark:text-gray-400" />
                <h3 class="text-base font-medium text-gray-600 dark:text-gray-300">
                  Project Information
                </h3>
              </div>

              <div class="grid grid-cols-2 gap-3">
                <div>
                  <p class="text-xs text-gray-500 dark:text-gray-400">Target Platform</p>
                  <p class="text-sm font-medium">PC, Console</p>
                </div>
                <div>
                  <p class="text-xs text-gray-500 dark:text-gray-400">Genres</p>
                  <div class="flex gap-1 flex-wrap mt-1">
                    <UBadge size="xs" color="primary" variant="subtle">Action RPG</UBadge>
                    <UBadge size="xs" color="primary" variant="subtle">Open World</UBadge>
                  </div>
                </div>
                <div>
                  <p class="text-xs text-gray-500 dark:text-gray-400">Last Updated</p>
                  <p class="text-sm font-medium">Today, 2:30 PM</p>
                </div>
                <div>
                  <p class="text-xs text-gray-500 dark:text-gray-400">Status</p>
                  <UBadge size="xs" color="success" variant="subtle">Active</UBadge>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- AI Insights Card (Spans 1 column, 1 row) -->
        <UCard class="hover:shadow-lg transition-shadow">
          <template #header>
            <div class="flex items-center gap-2">
              <UIcon name="i-lucide-sparkles" class="text-primary" />
              <h3 class="text-lg font-semibold">AI Insights & Suggestions</h3>
            </div>
          </template>

          <div class="space-y-3">
            <div
              class="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800"
            >
              <div class="flex gap-2 items-start">
                <UIcon name="i-lucide-info" class="text-blue-600 mt-0.5 flex-shrink-0" />
                <div>
                  <p class="text-sm font-medium">Missing PX Nodes</p>
                  <p class="text-xs text-gray-600 dark:text-gray-400 mt-1">
                    You have combat expectations defined but no associated PX nodes yet.
                  </p>
                </div>
              </div>
            </div>

            <div
              class="p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800"
            >
              <div class="flex gap-2 items-start">
                <UIcon
                  name="i-lucide-alert-triangle"
                  class="text-yellow-600 mt-0.5 flex-shrink-0"
                />
                <div>
                  <p class="text-sm font-medium">Pacing Diagram Gap</p>
                  <p class="text-xs text-gray-600 dark:text-gray-400 mt-1">
                    Your pacing diagram lacks content around mid-game; consider adding events.
                  </p>
                </div>
              </div>
            </div>

            <div
              class="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800"
            >
              <div class="flex gap-2 items-start">
                <UIcon name="i-lucide-check-circle" class="text-green-600 mt-0.5 flex-shrink-0" />
                <div>
                  <p class="text-sm font-medium">Good Alignment</p>
                  <p class="text-xs text-gray-600 dark:text-gray-400 mt-1">
                    Your design pillars align well with player expectations.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </UCard>

        <!-- PX Charts Overview -->
        <UCard
          class="hover:shadow-lg transition-shadow cursor-pointer hover:border-primary"
          @click="navigateToModule('/pxcharts')"
        >
          <template #header>
            <div class="flex items-center gap-2">
              <UIcon name="i-lucide-chart-network" class="text-primary" />
              <h3 class="text-lg font-semibold">PX Charts</h3>
            </div>
          </template>

          <div class="space-y-3">
            <div
              v-if="pxCharts.length === 0"
              class="text-center py-8 text-gray-500 dark:text-gray-400"
            >
              <UIcon name="i-lucide-chart-network" class="mx-auto mb-2 text-4xl" />
              <p class="text-sm">No charts created yet</p>
              <p class="text-xs mt-1">Click to create your first PX chart</p>
            </div>
            <div v-else class="space-y-2">
              <div
                class="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800 rounded"
              >
                <span class="text-sm font-medium">Total Charts</span>
                <UBadge color="primary" variant="subtle">{{ pxCharts.length }}</UBadge>
              </div>
              <div class="space-y-1">
                <div
                  v-for="chart in pxCharts.slice(0, 4)"
                  :key="chart.id"
                  class="text-sm p-2 hover:bg-gray-50 dark:hover:bg-gray-800 rounded"
                >
                  <p class="font-medium truncate">{{ chart.name }}</p>
                  <p class="text-xs text-gray-500 dark:text-gray-400 truncate">
                    {{ chart.description || 'No description' }}
                  </p>
                </div>
              </div>
              <div v-if="pxCharts.length > 4" class="text-center pt-1">
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  +{{ pxCharts.length - 4 }} more chart{{ pxCharts.length - 4 > 1 ? 's' : '' }}
                </p>
              </div>
            </div>
          </div>
        </UCard>

        <!-- Player Expectations Card -->
        <UCard
          class="hover:shadow-lg transition-shadow cursor-pointer hover:border-primary"
          @click="navigateToModule('/player-expectations')"
        >
          <template #header>
            <div class="flex items-center gap-2">
              <UIcon name="i-lucide-users" class="text-primary" />
              <h3 class="text-lg font-semibold">Player Expectations</h3>
            </div>
          </template>

          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <span class="text-sm">Genre Benchmarks</span>
              <UBadge color="success" variant="subtle">
                <UIcon name="i-lucide-check" class="mr-1" />
                Defined
              </UBadge>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm">Combat Expectations</span>
              <UBadge color="success" variant="subtle">
                <UIcon name="i-lucide-check" class="mr-1" />
                Defined
              </UBadge>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm">Narrative Expectations</span>
              <UBadge color="warning" variant="subtle">
                <UIcon name="i-lucide-alert-circle" class="mr-1" />
                In Progress
              </UBadge>
            </div>
            <div class="mt-4 p-3 bg-gray-100 dark:bg-gray-800 rounded-lg">
              <p class="text-xs text-gray-600 dark:text-gray-400">Alignment Score</p>
              <p class="text-2xl font-bold text-primary">87%</p>
            </div>
          </div>
        </UCard>

        <!-- Workflow Progress - Vertical (Spans 1 column, 2 rows) -->
        <UCard
          class="row-span-2 hover:shadow-lg transition-shadow cursor-pointer hover:border-primary"
          @click="navigateToModule('/dashboard')"
        >
          <template #header>
            <div class="flex items-center gap-2">
              <UIcon name="i-lucide-workflow" class="text-primary" />
              <h3 class="text-lg font-semibold">Workflow Progress</h3>
            </div>
          </template>

          <UStepper
            v-model="currentWorkflowStep"
            :items="workflowSteps"
            orientation="vertical"
            color="primary"
            size="md"
            class="w-full"
          />
        </UCard>

        <!-- Design Pillars Card -->
        <UCard
          class="hover:shadow-lg transition-shadow cursor-pointer hover:border-primary"
          @click="navigateToModule('/pillars')"
        >
          <template #header>
            <div class="flex items-center gap-2">
              <UIcon name="i-lucide-layers" class="text-primary" />
              <h3 class="text-lg font-semibold">Design Pillars</h3>
            </div>
          </template>

          <div class="space-y-2">
            <div
              v-if="pillars.length === 0"
              class="text-center py-4 text-gray-500 dark:text-gray-400"
            >
              <p class="text-sm">No pillars defined yet</p>
              <p class="text-xs mt-1">Click to create your first pillar</p>
            </div>
            <div
              v-for="pillar in pillars.slice(0, 3)"
              :key="pillar.id"
              class="p-3 bg-primary-50 dark:bg-primary-900/20 rounded-lg"
            >
              <p class="font-semibold text-sm">{{ pillar.name }}</p>
              <p class="text-xs text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
                {{ pillar.description || 'No description' }}
              </p>
            </div>
            <div v-if="pillars.length > 3" class="text-center pt-2">
              <p class="text-xs text-gray-500 dark:text-gray-400">
                +{{ pillars.length - 3 }} more pillar{{ pillars.length - 3 > 1 ? 's' : '' }}
              </p>
            </div>
          </div>
        </UCard>

        <!-- Recent Activity Card -->
        <UCard class="hover:shadow-lg transition-shadow">
          <template #header>
            <div class="flex items-center gap-2">
              <UIcon name="i-lucide-clock" class="text-primary" />
              <h3 class="text-lg font-semibold">Recent Activity</h3>
            </div>
          </template>

          <div class="space-y-2">
            <div class="flex gap-2 items-center text-sm">
              <UIcon name="i-lucide-edit" class="text-primary flex-shrink-0" />
              <div class="flex-1 min-w-0">
                <p class="font-medium truncate">Updated PX Node</p>
                <p class="text-xs text-gray-500 dark:text-gray-400">10 min ago</p>
              </div>
            </div>
            <div class="flex gap-2 items-center text-sm">
              <UIcon name="i-lucide-plus" class="text-success flex-shrink-0" />
              <div class="flex-1 min-w-0">
                <p class="font-medium truncate">Added Design Pillar</p>
                <p class="text-xs text-gray-500 dark:text-gray-400">2 hours ago</p>
              </div>
            </div>
            <div class="flex gap-2 items-center text-sm">
              <UIcon name="i-lucide-trash" class="text-error flex-shrink-0" />
              <div class="flex-1 min-w-0">
                <p class="font-medium truncate">Removed expectation</p>
                <p class="text-xs text-gray-500 dark:text-gray-400">Yesterday</p>
              </div>
            </div>
          </div>
        </UCard>

        <!-- Workflow Progress - Horizontal (Spans 2 columns) -->
        <UCard
          class="col-span-2 hover:shadow-lg transition-shadow cursor-pointer hover:border-primary"
          @click="navigateToModule('/dashboard')"
        >
          <template #header>
            <div class="flex items-center gap-2">
              <UIcon name="i-lucide-workflow" class="text-primary" />
              <h3 class="text-lg font-semibold">Workflow Progress</h3>
            </div>
          </template>

          <UStepper
            v-model="currentWorkflowStep"
            :items="workflowSteps"
            orientation="horizontal"
            color="primary"
            size="md"
            class="w-full"
          />
        </UCard>
      </UPageGrid>

      <div>
        <SimpleContentWrapper>
          <!-- Cards Section -->
          <section class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            <UCard class="hover:shadow-lg transition">
              <template #header>
                <h2 class="font-semibold text-lg">Formalized Player Experience</h2>
              </template>
              <p>
                You can design player experiences through a formalization (currently being
                implemented).
              </p>
            </UCard>
            <UCard class="hover:shadow-lg transition">
              <template #header>
                <h2 class="font-semibold text-lg">LLM supported Design Pillars</h2>
              </template>
              <p>
                The tool has design pillar functionality, that is validated and cross-checked by the
                help of LLMs to make sure your design stays consistent.
              </p>
            </UCard>
            <UCard class="hover:shadow-lg transition">
              <template #header>
                <h2 class="font-semibold text-lg">Moodboard Generation</h2>
              </template>
              <p>
                Through multimodal LLMs, you can design your moodboard directly in the app by
                describing and interaction with the tool.
              </p>
            </UCard>
            <UCard class="hover:shadow-lg transition">
              <template #header>
                <h2 class="font-semibold text-lg">Player Expectations Dashboard</h2>
              </template>
              <p>
                What do players expect when buying different genre games? What do they like or
                dislike? For these insights and more, visit the Player Expectations module.
              </p>
            </UCard>
            <UCard class="hover:shadow-lg transition">
              <template #header>
                <h2 class="font-semibold text-lg">Unified Agentic AI Interface</h2>
              </template>
              <p>
                All pix:e AI features are powered by a unified agentic interface. The agentic
                approach ensures top-tier results through tool usage and improved context awareness.
              </p>
            </UCard>
            <UCard class="hover:shadow-lg transition">
              <template #header>
                <h2 class="font-semibold text-lg">Movie Script Evaluator for Virtual Production</h2>
              </template>
              <p>
                This tool is to evaluate movie scripts through LLMs based on the assets available in
                the game engine for virtual production purposes.
              </p>
            </UCard>
          </section>
        </SimpleContentWrapper>
      </div>
    </UPageBody>
  </UPage>
</template>

<style scoped></style>
