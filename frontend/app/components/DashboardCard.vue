<script setup lang="ts">
interface Props {
  title: string
  icon: string
}

defineProps<Props>()
</script>

<template>
  <UCard class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800">
    <template #header>
      <div class="flex items-center gap-2">
        <UIcon :name="icon" class="text-gray-600 dark:text-gray-400" />
        <h3 class="font-semibold text-gray-900 dark:text-gray-100">{{ title }}</h3>
      </div>
    </template>

    <slot />
  </UCard>
</template>
