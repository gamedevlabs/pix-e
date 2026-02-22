<script setup lang="ts">
interface Props {
  total: number
  recent: number
}

defineProps<Props>()
</script>

<template>
  <DashboardCard title="Quick Stats" icon="i-lucide-bar-chart-3" :login-required="true">
    <div class="grid grid-cols-2 gap-2">
      <!-- Total Projects -->
      <div
        class="flex flex-col items-center justify-center gap-1 rounded-lg bg-primary-50 dark:bg-primary-950/30 py-3 px-2 text-center"
      >
        <span class="text-2xl font-bold text-primary leading-none">{{ total }}</span>
        <span class="text-[11px] text-gray-500 dark:text-gray-400 font-medium leading-tight"
          >Projects</span
        >
      </div>
      <!-- Active This Week -->
      <div
        class="flex flex-col items-center justify-center gap-1 rounded-lg bg-success-50 dark:bg-success-950/30 py-3 px-2 text-center"
      >
        <span class="text-2xl font-bold text-success-600 dark:text-success-400 leading-none">{{
          recent
        }}</span>
        <span class="text-[11px] text-gray-500 dark:text-gray-400 font-medium leading-tight"
          >This week</span
        >
      </div>
    </div>
  </DashboardCard>
</template>
