<script setup lang="ts">
interface Props {
  total: number
  recent: number
}

defineProps<Props>()
</script>

<template>
  <UCard class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800">
    <template #header>
      <div class="flex items-center gap-2">
        <UIcon name="i-lucide-bar-chart-3" class="text-gray-600 dark:text-gray-400" />
        <h3 class="font-semibold text-gray-900 dark:text-gray-100">Quick Stats</h3>
      </div>
    </template>
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <span class="text-sm text-gray-600 dark:text-gray-400">Total Projects</span>
        <UBadge color="primary" variant="subtle" size="lg">{{ total }}</UBadge>
      </div>
      <div class="flex items-center justify-between">
        <span class="text-sm text-gray-600 dark:text-gray-400">Active This Week</span>
        <UBadge color="success" variant="subtle" size="lg">{{ recent }}</UBadge>
      </div>
    </div>
  </UCard>
</template>
