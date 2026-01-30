<script setup lang="ts">
interface Insight {
  type: 'info' | 'warning' | 'success'
  title: string
  message: string
}

interface Props {
  insights?: Insight[]
}

// TODO: Connect mock data to real backend (ai-insights)
const _props = withDefaults(defineProps<Props>(), {
  insights: () => [
    {
      type: 'info',
      title: 'Missing PX Nodes',
      message: 'You have combat expectations defined but no associated PX nodes yet.',
    },
    {
      type: 'warning',
      title: 'Pacing Diagram Gap',
      message: 'Your pacing diagram lacks content around mid-game; consider adding events.',
    },
    {
      type: 'success',
      title: 'Good Alignment',
      message: 'Your design pillars align well with player expectations.',
    },
  ],
})

const getInsightConfig = (type: Insight['type']) => {
  const configs = {
    info: {
      bgClass: 'bg-blue-50 dark:bg-blue-900/20',
      borderClass: 'border-blue-200 dark:border-blue-800',
      iconClass: 'text-blue-600',
      icon: 'i-lucide-info',
    },
    warning: {
      bgClass: 'bg-yellow-50 dark:bg-yellow-900/20',
      borderClass: 'border-yellow-200 dark:border-yellow-800',
      iconClass: 'text-yellow-600',
      icon: 'i-lucide-alert-triangle',
    },
    success: {
      bgClass: 'bg-green-50 dark:bg-green-900/20',
      borderClass: 'border-green-200 dark:border-green-800',
      iconClass: 'text-green-600',
      icon: 'i-lucide-check-circle',
    },
  }
  return configs[type]
}
</script>

<template>
  <DashboardCard title="AI Insights & Suggestions" icon="i-lucide-sparkles">
    <div class="space-y-3">
      <div
        v-for="(insight, index) in insights"
        :key="index"
        class="p-3 rounded-lg border"
        :class="[
          getInsightConfig(insight.type).bgClass,
          getInsightConfig(insight.type).borderClass,
        ]"
      >
        <div class="flex gap-2 items-start">
          <UIcon
            :name="getInsightConfig(insight.type).icon"
            :class="getInsightConfig(insight.type).iconClass"
            class="mt-0.5 shrink-0"
          />
          <div>
            <p class="text-sm font-medium">{{ insight.title }}</p>
            <p class="text-xs text-gray-600 dark:text-gray-400 mt-1">
              {{ insight.message }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </DashboardCard>
</template>
