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
  /** When true, show a small badge indicating this card is backed by mock data. */
  showMockBadge?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  title: 'Recent Activity',
  items: () => mockRecentActivity as unknown as HistoryItem[],
  showMockBadge: true,
})

const { title, items } = toRefs(props)
const { showMockBadge } = toRefs(props)

const getTypeColor = (type?: string) => {
  const colors = {
    edit: 'text-primary',
    create: 'text-success',
    delete: 'text-error',
  }
  return colors[type as keyof typeof colors] || 'text-gray-600'
}
</script>

<template>
  <DashboardCard :title="title" icon="i-lucide-clock">
    <template #actions>
      <MockDataBadge v-if="showMockBadge" />
    </template>
    <div class="space-y-2">
      <div v-for="(item, index) in items" :key="index" class="flex gap-2 items-center text-sm">
        <UIcon :name="item.icon" :class="getTypeColor(item.type)" class="shrink-0" />
        <div class="flex-1 min-w-0">
          <p class="font-medium truncate text-gray-900 dark:text-gray-100">{{ item.title }}</p>
          <p class="text-xs text-gray-500 dark:text-gray-400">{{ item.timestamp }}</p>
        </div>
      </div>
    </div>
  </DashboardCard>
</template>
