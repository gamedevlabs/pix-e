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
    navGroup: 'main',
    navOrder: 1,
    showInNav: true,
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
  if (parts.length === 0) return 'P'
  if (parts.length === 1) return parts[0]!.slice(0, 2).toUpperCase()
  const first = parts[0]?.[0]
  const second = parts[1]?.[0]
  if (!first || !second) return parts[0]!.slice(0, 2).toUpperCase()
  return (first + second).toUpperCase()
}

// Navigate to specific module with project context
const navigateToModule = (route: string) => {
  const projectQuery = currentProjectId.value ? `?id=${currentProjectId.value}` : ''
  navigateTo(`${route}${projectQuery}`)
}

// MOCK DATA FOR DASHBOARD CARDS
const mock_historyData = computed(() => [
  {
    title: 'Set new Project Icon',
    timestamp: '10 min ago',
    icon: 'i-lucide-folder-open',
    type: 'edit' as const,
  },
  {
    title: 'Created New Pillar "testPillar1"',
    timestamp: '2 hours ago',
    icon: 'i-lucide-plus',
    type: 'create' as const,
  },
  {
    title: 'Adjusted PX Chart "Main Story Arc"',
    timestamp: 'Yesterday',
    icon: 'i-lucide-trash',
    type: 'delete' as const,
  },
])
</script>

<template>
  <UPage>
    <UPageBody>
      <div class="space-y-6">
        <!-- Project header (compact + aligned) -->
        <UCard class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800">
          <div class="p-1">
            <div class="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
              <div class="flex items-center gap-4 min-w-0">
                <UAvatar
                  v-if="!currentProject?.icon"
                  :text="getProjectInitials(currentProject?.name || 'Project')"
                  :alt="currentProject?.name || 'Project'"
                  size="xl"
                />
                <div v-else class="text-5xl leading-none">{{ currentProject.icon }}</div>

                <div class="min-w-0">
                  <h1
                    class="text-3xl lg:text-4xl font-bold text-gray-900 dark:text-gray-100 truncate"
                  >
                    {{ currentProject?.name || 'Project' }}
                  </h1>
                  <p class="text-base text-gray-600 dark:text-gray-400 truncate">
                    Design games with research.
                  </p>
                </div>
              </div>

              <!-- Right side: platform + genres on a grid + settings (top-right) + last edited (bottom-right) -->
              <div class="w-full lg:w-auto">
                <div class="grid grid-cols-1 sm:grid-cols-[minmax(0,1fr)_auto] gap-3 lg:gap-4">
                  <!-- Left column: platform + genres (grid-driven spacing/alignment) -->
                  <div class="grid gap-2">
                    <!-- Platform row (single item, still aligned to genre grid) -->
                    <div class="grid grid-cols-[max-content_1fr] items-center gap-2">
                      <UBadge color="primary" variant="subtle" size="sm" class="w-max">
                        <UIcon name="i-lucide-monitor" class="mr-1" />
                        PC, Console
                      </UBadge>
                    </div>

                    <!-- Genres row: uses CSS grid for consistent spacing; wraps automatically -->
                    <div class="grid grid-cols-[repeat(auto-fit,minmax(110px,max-content))] gap-2">
                      <UBadge color="primary" variant="subtle" size="sm" class="justify-center">
                        Action RPG
                      </UBadge>
                      <UBadge color="primary" variant="subtle" size="sm" class="justify-center">
                        Open World
                      </UBadge>
                      <!-- When real data is wired, render all genres here; grid will handle 1..N nicely -->
                    </div>
                  </div>

                  <!-- Right column: settings (top), status + last edited (bottom) -->
                  <div class="flex flex-col items-end justify-between gap-2">
                    <UButton
                      icon="i-lucide-settings"
                      size="sm"
                      color="neutral"
                      variant="ghost"
                      label="Settings"
                      @click="navigateToModule('/edit')"
                    />

                    <div
                      class="grid grid-cols-[max-content_max-content] items-center justify-end gap-2"
                    >
                      <UBadge color="success" variant="subtle" size="sm" class="w-max">
                        Active
                      </UBadge>
                      <UBadge color="neutral" variant="soft" size="sm" class="w-max">
                        <UIcon name="i-lucide-clock" class="mr-1" />
                        Today, 2:30 PM
                      </UBadge>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </UCard>

        <!-- Main dashboard layout -->
        <div class="grid grid-cols-1 2xl:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)] gap-6">
          <!-- Left: Modules -->
          <section class="space-y-3">
            <div class="flex items-center justify-between">
              <h2 class="text-sm font-semibold text-gray-900 dark:text-gray-100">Modules</h2>
              <UBadge color="neutral" variant="soft" size="xs">Open a module to continue</UBadge>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <DashboardModuleCard
                title="PX Charts"
                description="Build and explore PX charts"
                icon="i-lucide-chart-network"
                to="/pxcharts"
                cta-label="Open"
                :badge-label="pxCharts.length ? `${pxCharts.length} charts` : 'New'"
              />

              <DashboardModuleCard
                title="Player Expectations"
                description="Benchmarks, sentiment, and alignment"
                icon="i-lucide-users"
                to="/player-expectations"
                cta-label="Open"
                badge-label="87%"
              />

              <DashboardModuleCard
                title="Design Pillars"
                description="Define your game's foundations"
                icon="i-lucide-layers"
                to="/pillars"
                cta-label="Manage"
                :badge-label="pillars.length ? `${pillars.length}` : 'New'"
              />
            </div>

            <!-- Helpful overview content (kept, but visually quieter) -->
            <SimpleContentWrapper>
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
                    The tool has design pillar functionality, that is validated and cross-checked by
                    the help of LLMs to make sure your design stays consistent.
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
                    approach ensures top-tier results through tool usage and improved context
                    awareness.
                  </p>
                </UCard>
                <UCard class="hover:shadow-lg transition">
                  <template #header>
                    <h2 class="font-semibold text-lg">
                      Movie Script Evaluator for Virtual Production
                    </h2>
                  </template>
                  <p>
                    This tool is to evaluate movie scripts through LLMs based on the assets
                    available in the game engine for virtual production purposes.
                  </p>
                </UCard>
              </section>
            </SimpleContentWrapper>
          </section>

          <!-- Right: Information -->
          <aside class="space-y-4">
            <div class="flex items-center justify-between">
              <h2 class="text-sm font-semibold text-gray-900 dark:text-gray-100">Updates</h2>
              <UBadge color="neutral" variant="soft" size="xs">Info</UBadge>
            </div>

            <AiInsightsCard />
            <WorkflowCard orientation="vertical" />
            <HistoryCard :items="mock_historyData" title="Recent Activity" />
          </aside>
        </div>
      </div>
    </UPageBody>
  </UPage>
</template>

<style scoped></style>
