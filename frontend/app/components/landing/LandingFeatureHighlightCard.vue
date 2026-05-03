<script setup lang="ts">
defineProps<{
  icon: string
  title: string
  description: string
  iconBgClass?: string
  iconColorClass?: string
}>()
</script>

<template>
  <UCard
    class="border border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-900"
    :ui="{ body: 'p-4' }"
  >
    <div class="flex items-start gap-3">
      <div class="rounded-lg p-2 shrink-0 mt-0.5" :class="iconBgClass ?? 'bg-primary/10'">
        <UIcon :name="icon" class="size-4" :class="iconColorClass ?? 'text-primary'" />
      </div>
      <div class="space-y-0.5 min-w-0">
        <p class="font-semibold text-sm text-gray-900 dark:text-gray-100">{{ title }}</p>
        <p class="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
          {{ description }}
        </p>
      </div>
    </div>
  </UCard>
</template>
