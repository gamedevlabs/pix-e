<script setup lang="ts">
import { mockRecentActivity } from '~/mock_data/mock_recent-activity'

interface HistoryItem {
  title: string
  timestamp: string
  icon: string
  type?: 'edit' | 'create' | 'delete'
}

interface Props {
  items?: HistoryItem[]
  title?: string
  showMockBadge?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  title: 'Recent Activity',
  items: () => mockRecentActivity as unknown as HistoryItem[],
  showMockBadge: true,
})

const { title, items, showMockBadge } = toRefs(props)

const typeConfig = (type?: string) => {
  const map: Record<string, { icon: string; iconBg: string; line: string }> = {
    create: {
      icon: 'text-success-600 dark:text-success-400',
      iconBg: 'bg-success-50 dark:bg-success-900/30 ring-1 ring-success-200 dark:ring-success-800',
      line: 'bg-success-200 dark:bg-success-800',
    },
    edit: {
      icon: 'text-primary-600 dark:text-primary-400',
      iconBg: 'bg-primary-50 dark:bg-primary-900/30 ring-1 ring-primary-200 dark:ring-primary-800',
      line: 'bg-primary-200 dark:bg-primary-800',
    },
    delete: {
      icon: 'text-error-600 dark:text-error-400',
      iconBg: 'bg-error-50 dark:bg-error-900/30 ring-1 ring-error-200 dark:ring-error-800',
      line: 'bg-error-200 dark:bg-error-800',
    },
  }
  return (
    map[type as string] ?? {
      icon: 'text-gray-500 dark:text-gray-400',
      iconBg: 'bg-gray-100 dark:bg-gray-800 ring-1 ring-gray-200 dark:ring-gray-700',
      line: 'bg-gray-200 dark:bg-gray-700',
    }
  )
}
</script>

<template>
  <DashboardCard :title="title" icon="i-lucide-clock">
    <template #actions>
      <MockDataBadge v-if="showMockBadge" />
    </template>

    <div class="flex flex-col gap-0">
      <div v-for="(item, index) in items" :key="index" class="relative flex items-stretch gap-4">
        <!-- Left: icon + vertical line -->
        <div class="flex flex-col items-center shrink-0">
          <!-- Icon node -->
          <div
            class="z-10 size-7 rounded-lg flex items-center justify-center shrink-0"
            :class="typeConfig(item.type).iconBg"
          >
            <UIcon :name="item.icon" class="size-3.5" :class="typeConfig(item.type).icon" />
          </div>
          <!-- Connector line (hidden on last item) -->
          <div
            v-if="index < items.length - 1"
            class="w-px flex-1 mt-1"
            :class="typeConfig(item.type).line"
          />
        </div>

        <!-- Right: content -->
        <div class="pb-5 min-w-0 flex-1" :class="{ 'pb-0': index === items.length - 1 }">
          <p class="text-sm font-medium text-gray-900 dark:text-gray-100 leading-snug">
            {{ item.title }}
          </p>
          <p class="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
            {{ item.timestamp }}
          </p>
        </div>
      </div>
    </div>
  </DashboardCard>
</template>
