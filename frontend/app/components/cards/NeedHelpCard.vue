<template>
  <UCard class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800">
    <template #header>
      <div class="flex items-center gap-2">
        <UIcon name="i-lucide-help-circle" class="text-gray-600 dark:text-gray-400" />
        <h3 class="font-semibold text-gray-900 dark:text-gray-100">Need Help?</h3>
      </div>
    </template>
    <div class="space-y-2">
      <UButton
        label="Wiki"
        icon="i-lucide-book-open"
        color="neutral"
        variant="soft"
        size="sm"
        block
      />
      <UButton
        label="Contact Us"
        icon="i-lucide-mail"
        color="neutral"
        variant="soft"
        size="sm"
        block
      />
    </div>
  </UCard>
</template>
