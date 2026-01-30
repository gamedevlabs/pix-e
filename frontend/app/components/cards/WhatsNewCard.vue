<script setup lang="ts">
interface Update {
  title: string
  description: string
  icon?: string
}

interface Props {
  mockUpdates?: Update[]
}

// TODO: Connect mock data to real backend (whats-new)
const _mockUpdates = withDefaults(defineProps<Props>(), {
  mockUpdates: () => [
    {
      title: 'Project Layer',
      description: 'Manage different projects separately',
      icon: 'i-lucide-zap',
    },
    {
      title: 'Enhanced UX',
      description: 'Better user experience',
      icon: 'i-lucide-palette',
    },
  ],
})
</script>

<template>
  <DashboardCard title="What's New" icon="i-lucide-sparkles">
    <div class="space-y-3 text-sm">
      <div v-for="(update, index) in mockUpdates" :key="index" class="flex gap-2">
        <UIcon :name="update.icon || 'i-lucide-circle-dot'" class="text-primary shrink-0 mt-0.5" />
        <div>
          <p class="font-medium text-gray-900 dark:text-gray-100">{{ update.title }}</p>
          <p class="text-xs text-gray-600 dark:text-gray-400">{{ update.description }}</p>
        </div>
      </div>
    </div>
  </DashboardCard>
</template>
