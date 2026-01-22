<script setup lang="ts">
interface HistoryItem {
  title: string
  timestamp: string
  icon: string
  type?: 'edit' | 'create' | 'delete'
}

interface Props {
  items?: HistoryItem[]
  title?: string
}

const _props = withDefaults(defineProps<Props>(), {
  title: 'Recent Activity',
  items: () => [
    {
      title: 'Updated PX Node',
      timestamp: '10 min ago',
      icon: 'i-lucide-edit',
      type: 'edit',
    },
    {
      title: 'Added Design Pillar',
      timestamp: '2 hours ago',
      icon: 'i-lucide-plus',
      type: 'create',
    },
    {
      title: 'Removed expectation',
      timestamp: 'Yesterday',
      icon: 'i-lucide-trash',
      type: 'delete',
    },
  ],
})

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
  <UCard class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800">
    <template #header>
      <div class="flex items-center gap-2">
        <UIcon name="i-lucide-clock" class="text-gray-600 dark:text-gray-400" />
        <h3 class="font-semibold text-gray-900 dark:text-gray-100">{{ title }}</h3>
      </div>
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
  </UCard>
</template>
