<script setup lang="ts">
// ============================================================================
// PAGE CONFIG - Edit these settings for this module
// ============================================================================
// MOCK DATA FOR DASHBOARD CARDS
import { mockRecentActivity } from '~/mock_data/mock_recent-activity'
import { platformConfigs } from '~/utils/platformConfig'

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
const {
  aspectChartData,
  sentimentPieData,
  load: loadExpectations,
} = usePlayerExpectationCharts('http://localhost:8000/api')

onMounted(() => {
  fetchPillars()
  fetchPxCharts()
  loadExpectations()
})

// ── Preview helpers ──────────────────────────────────────────────────────────
const PREVIEW_MAX = 2

// Pillars
const pillarPreviewItems = computed(() =>
  pillars.value.slice(0, PREVIEW_MAX).map(p => ({ text: p.name, icon: 'i-lucide-layers' }))
)
const pillarMoreLabel = computed(() => {
  const rest = pillars.value.length - PREVIEW_MAX
  if (pillars.value.length === 0) return 'No pillars yet — add your first one'
  if (rest <= 0) return undefined
  return `+${rest} more ${rest === 1 ? 'pillar' : 'pillars'}`
})

// PX Charts
const chartPreviewItems = computed(() =>
  pxCharts.value.slice(0, PREVIEW_MAX).map(c => ({ text: c.name, icon: 'i-lucide-chart-network' }))
)
const chartMoreLabel = computed(() => {
  const rest = pxCharts.value.length - PREVIEW_MAX
  if (pxCharts.value.length === 0) return 'No charts yet — create your first one'
  if (rest <= 0) return undefined
  return `+${rest} more ${rest === 1 ? 'chart' : 'charts'}`
})

// Player Expectations — top aspects + sentiment summary
const expectationsPreviewItems = computed(() => {
  const items: { text: string; icon: string }[] = []

  // Top 2 most-mentioned aspects from aspectChartData
  const aspectData = aspectChartData.value as { labels: string[]; datasets: { data: number[] }[] } | null
  if (aspectData?.labels?.length) {
    const paired = aspectData.labels.map((label, i) => ({
      label,
      count: aspectData.datasets[0]?.data[i] ?? 0,
    }))
    paired
      .sort((a, b) => b.count - a.count)
      .slice(0, PREVIEW_MAX)
      .forEach(({ label, count }) => {
        items.push({ text: `${label} — ${count} mentions`, icon: 'i-lucide-tag' })
      })
  }

  // Dominant sentiment from sentimentPieData
  const pieData = sentimentPieData.value as { labels: string[]; datasets: { data: number[] }[] } | null
  if (pieData?.labels?.length) {
    const total = pieData.datasets[0]?.data.reduce((a, b) => a + b, 0) ?? 0
    if (total > 0) {
      const maxIdx = pieData.datasets[0]!.data.indexOf(Math.max(...pieData.datasets[0]!.data))
      const dominant = pieData.labels[maxIdx]
      const pct = Math.round((pieData.datasets[0]!.data[maxIdx]! / total) * 100)
      const icon =
        dominant === 'positive'
          ? 'i-lucide-smile'
          : dominant === 'negative'
            ? 'i-lucide-frown'
            : 'i-lucide-meh'
      items.push({ text: `${pct}% ${dominant} sentiment`, icon })
    }
  }

  return items
})

const expectationsMoreLabel = computed(() => {
  if (!expectationsPreviewItems.value.length) return 'No data loaded yet'
  return undefined
})
// ────────────────────────────────────────────────────────────────────────────

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

const mock_historyData = computed(() => mockRecentActivity)
</script>

<template>
  <div class="max-w-screen-2xl mx-auto w-full px-2 py-8 space-y-10">

    <!-- ─── Project Header ──────────────────────────────────────────────── -->
    <UCard
      class="border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900"
      :ui="{ body: 'px-3 py-2.5' }"
    >
      <div class="flex items-stretch gap-4 min-h-20">

        <!-- Left: avatar + name + description -->
        <div class="flex items-center gap-4 min-w-0 flex-1">
          <UAvatar
            v-if="!currentProject?.icon"
            :text="getProjectInitials(currentProject?.name || 'Project')"
            :alt="currentProject?.name || 'Project'"
            size="xl"
            class="shrink-0 text-primary bg-primary-100 dark:bg-primary-900/50 font-bold ring-2 ring-primary-200 dark:ring-primary-800"
          />
          <div v-else class="text-5xl leading-none shrink-0">{{ currentProject.icon }}</div>

          <div class="min-w-0">
            <h1 class="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-gray-100 truncate leading-tight">
              {{ currentProject?.name || 'Project' }}
            </h1>
            <p class="text-sm text-gray-500 dark:text-gray-400 truncate mt-0.5">
              {{ currentProject?.shortDescription || 'No description' }}
            </p>
          </div>
        </div>

        <!-- Right: settings top, badges bottom -->
        <div class="flex flex-col items-end justify-between shrink-0 gap-3">
          <UButton
            icon="i-lucide-settings"
            size="sm"
            color="neutral"
            variant="ghost"
            label="Settings"
            @click="navigateToModule('/edit')"
          />
          <div class="flex flex-col items-end gap-2">
            <!-- Platform icons -->
            <div v-if="currentProject?.targetPlatform?.length" class="flex items-center gap-2">
              <UTooltip
                v-for="platform in platformConfigs.filter(p => (currentProject?.targetPlatform as string[])?.includes(p.value))"
                :key="platform.value"
                :text="platform.label"
              >
                <UIcon :name="platform.icon" class="size-4 text-gray-500 dark:text-gray-400" />
              </UTooltip>
            </div>
            <!-- Genre badges -->
            <div v-if="currentProject?.genre" class="flex flex-wrap justify-end items-center gap-2">
              <UBadge
                v-for="g in currentProject.genre.split(',').map((s: string) => s.trim()).filter(Boolean)"
                :key="g"
                :label="g"
                size="sm"
                color="neutral"
                variant="outline"
                class="pointer-events-none"
              />
            </div>
          </div>
        </div>

      </div>
    </UCard>

    <!-- ─── 3-col layout (mirrors landing page) ───────────────────────── -->
    <div class="grid grid-cols-1 xl:grid-cols-[260px_1fr_260px] gap-6 items-start">

      <!-- Left side panel -->
      <aside class="hidden xl:flex flex-col gap-4">
        <WorkflowCard orientation="vertical" />
        <HistoryCard :items="mock_historyData" title="Recent Activity" />
      </aside>

      <!-- Center: Modules -->
      <div class="space-y-5 min-w-0">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="h-6 w-1 rounded-full bg-primary" />
            <h2 class="text-xl font-bold text-gray-900 dark:text-gray-100">Modules</h2>
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <DashboardModuleCard
            title="Design Pillars"
            description="Define your game's core foundations"
            icon="i-lucide-landmark"
            to="/pillars"
            cta-label="Manage"
            :preview-items="pillarPreviewItems"
            :preview-more-label="pillarMoreLabel"
          />
          <DashboardModuleCard
            title="Player Experience"
            description="Build and explore player experience charts"
            icon="i-lucide-chart-network"
            to="/pxcharts"
            cta-label="Open"
            :preview-items="chartPreviewItems"
            :preview-more-label="chartMoreLabel"
          />
          <DashboardModuleCard
            title="Player Expectations"
            description="Benchmarks, sentiment, and alignment"
            icon="i-lucide-book-open"
            to="/player-expectations"
            cta-label="Open"
            :preview-items="expectationsPreviewItems"
            :preview-more-label="expectationsMoreLabel"
          />
        </div>
      </div>

      <!-- Right side panel -->
      <aside class="hidden xl:flex flex-col gap-4">
        <AiInsightsCard />
      </aside>

    </div>
  </div>
</template>

<style scoped></style>
