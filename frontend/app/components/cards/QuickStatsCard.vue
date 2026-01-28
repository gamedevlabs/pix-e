<script setup lang="ts">
interface Props {
  total: number
  recent: number
}

defineProps<Props>()
</script>

<template>
  <DashboardCard title="Quick Stats" icon="i-lucide-bar-chart-3">
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
  </DashboardCard>
</template>
