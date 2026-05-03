<script setup lang="ts">
import { mockRecentActivity } from '~/mock_data/mock_recent-activity'

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

const {
  pillarPreviewItems,
  pillarMoreLabel,
  chartPreviewItems,
  chartMoreLabel,
  expectationsPreviewItems,
  expectationsMoreLabel,
} = useDashboardModuleCards()
</script>

<template>
  <div class="max-w-screen-2xl mx-auto w-full px-2 py-8 space-y-10">
    <DashboardProjectHeader />

    <div class="grid grid-cols-1 xl:grid-cols-[260px_1fr_260px] gap-6 items-start">
      <!-- Left side panel -->
      <aside class="hidden xl:flex flex-col gap-4">
        <WorkflowCard orientation="vertical" />
        <HistoryCard :items="mockRecentActivity" title="Recent Activity" />
      </aside>

      <!-- Center: Modules -->
      <div class="space-y-5 min-w-0">
        <div class="flex items-center gap-3">
          <div class="h-6 w-1 rounded-full bg-primary" />
          <h2 class="text-xl font-bold text-gray-900 dark:text-gray-100">Modules</h2>
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
            empty-state-description="Define the core values that shape your game's identity and guide every design decision."
          />
          <DashboardModuleCard
            title="Player Experience"
            description="Build and explore player experience charts"
            icon="i-lucide-chart-network"
            to="/pxcharts"
            cta-label="Open"
            :preview-items="chartPreviewItems"
            :preview-more-label="chartMoreLabel"
            empty-state-description="Map how different aspects of your game contribute to the overall player experience."
          />
          <DashboardModuleCard
            title="Player Expectations"
            description="Benchmarks, sentiment, and alignment"
            icon="i-lucide-book-open"
            to="/player-expectations"
            cta-label="Open"
            :preview-items="expectationsPreviewItems"
            :preview-more-label="expectationsMoreLabel"
            empty-state-description="Track what players expect and see how well your design meets those expectations."
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
