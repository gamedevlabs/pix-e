<script setup lang="ts">
import type { Project } from '~/utils/project.d'

defineProps<{
  project: Project
}>()
</script>

<template>
  <UCard
    class="border border-gray-200 dark:border-gray-700 bg-gray-50/60 dark:bg-gray-900/60"
    :ui="{ body: 'p-0' }"
  >
    <template #header>
      <div class="flex items-center gap-3">
        <div class="h-5 w-1 rounded-full bg-gray-300 dark:bg-gray-600" />
        <h2 class="text-base font-bold text-gray-900 dark:text-gray-100">Metadata</h2>
      </div>
    </template>

    <div class="px-5 pb-4 space-y-3">
      <div class="flex items-center justify-between gap-2">
        <div class="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400 shrink-0">
          <UIcon name="i-lucide-hash" class="size-3.5" />
          <span>ID</span>
        </div>
        <span class="text-xs font-mono text-gray-400 dark:text-gray-500 truncate select-all">
          {{ project.id }}
        </span>
      </div>
      <USeparator />
      <div class="flex items-center justify-between gap-2">
        <div class="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400 shrink-0">
          <UIcon name="i-lucide-calendar-plus" class="size-3.5" />
          <span>Created</span>
        </div>
        <span class="text-xs text-gray-400 dark:text-gray-500">
          {{ project.created_at ? new Date(project.created_at).toLocaleDateString() : 'N/A' }}
        </span>
      </div>
      <USeparator />
      <div class="flex items-center justify-between gap-2">
        <div class="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400 shrink-0">
          <UIcon name="i-lucide-calendar-clock" class="size-3.5" />
          <span>Updated</span>
        </div>
        <span class="text-xs text-gray-400 dark:text-gray-500">
          {{ project.updated_at ? new Date(project.updated_at).toLocaleDateString() : 'N/A' }}
        </span>
      </div>
    </div>
  </UCard>
</template>
