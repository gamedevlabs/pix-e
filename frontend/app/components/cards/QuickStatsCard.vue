<script setup lang="ts">
interface Props {
  total: number
  recent: number
}

defineProps<Props>()
</script>

<template>
  <DashboardCard title="Quick Stats" icon="i-lucide-bar-chart-3" :login-required="true">
    <div class="space-y-3">
      <div class="flex items-center justify-between gap-3">
        <div class="min-w-0">
          <p class="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
            Total Projects
          </p>
        </div>

        <UBadge color="primary" variant="subtle" size="lg" class="shrink-0">{{ total }}</UBadge>
      </div>

      <div class="h-px w-full bg-gray-200 dark:bg-gray-800" />

      <div class="flex items-center justify-between gap-3">
        <div class="min-w-0">
          <div class="flex items-center gap-2">
            <UIcon name="i-lucide-clock" class="size-4 text-gray-400 dark:text-gray-500" />
            <p class="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
              Active This Week
            </p>
          </div>
        </div>

        <UBadge color="success" variant="subtle" size="lg" class="shrink-0">{{ recent }}</UBadge>
      </div>
    </div>
  </DashboardCard>
</template>
