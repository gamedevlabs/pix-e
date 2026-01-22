<script setup lang="ts">
interface Update {
  title: string
  description: string
  icon?: string
}

interface Props {
  updates?: Update[]
}

withDefaults(defineProps<Props>(), {
  updates: () => [
    {
      title: 'Dashboard Update',
      description: 'New visual improvements',
      icon: 'i-lucide-zap',
    },
    {
      title: 'Enhanced UI',
      description: 'Better user experience',
      icon: 'i-lucide-palette',
    },
  ],
})
</script>

<template>
  <UCard class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800">
    <template #header>
      <div class="flex items-center gap-2">
        <UIcon name="i-lucide-sparkles" class="text-gray-600 dark:text-gray-400" />
        <h3 class="font-semibold text-gray-900 dark:text-gray-100">What's New</h3>
      </div>
    </template>
    <div class="space-y-3 text-sm">
      <div v-for="(update, index) in updates" :key="index" class="flex gap-2">
        <UIcon :name="update.icon || 'i-lucide-circle-dot'" class="text-primary shrink-0 mt-0.5" />
        <div>
          <p class="font-medium text-gray-900 dark:text-gray-100">{{ update.title }}</p>
          <p class="text-xs text-gray-600 dark:text-gray-400">{{ update.description }}</p>
        </div>
      </div>
    </div>
  </UCard>
</template>
