<template>
  <UCard class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800">
    <template #header>
      <div class="flex items-center gap-2">
        <UIcon name="i-lucide-lightbulb" class="text-gray-600 dark:text-gray-400" />
        <h3 class="font-semibold text-gray-900 dark:text-gray-100">Quick Tips</h3>
      </div>
    </template>
    <ul class="space-y-3 text-sm text-gray-700 dark:text-gray-300">
      <li class="flex gap-2">
        <UIcon name="i-lucide-check" class="text-success shrink-0 mt-0.5" />
        <span>Right-click projects for more options</span>
      </li>
      <li class="flex gap-2">
        <UIcon name="i-lucide-check" class="text-success shrink-0 mt-0.5" />
        <span>Create design pillars early in development</span>
      </li>
      <li class="flex gap-2">
        <UIcon name="i-lucide-check" class="text-success shrink-0 mt-0.5" />
        <span>Use PX Charts to map player experiences</span>
      </li>
    </ul>
  </UCard>
</template>
