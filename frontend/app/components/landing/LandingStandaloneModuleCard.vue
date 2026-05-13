<script setup lang="ts">
defineProps<{
  icon: string
  label: string
  description: string
  to: string
  tagLabel?: string
}>()

const router = useRouter()
</script>

<template>
  <UCard
    class="group border border-primary-100 dark:border-primary-900/40 bg-white dark:bg-gray-900 hover:border-primary-300 dark:hover:border-primary-700 hover:shadow-md hover:-translate-y-1 transition-all duration-200 cursor-pointer flex flex-col h-full rounded-xl overflow-hidden"
    :ui="{ body: 'p-5 flex-1 flex flex-col gap-4', header: '', footer: '' }"
    role="button"
    tabindex="0"
    @click="router.push(to)"
    @keydown.enter="router.push(to)"
  >
    <div class="flex items-center gap-3 min-w-0">
      <div
        class="rounded-lg p-2 bg-primary-50 text-primary-600 dark:bg-primary-950/40 dark:text-primary-400 shrink-0"
      >
        <UIcon :name="icon" class="size-5" />
      </div>
      <div class="min-w-0">
        <h3 class="font-semibold text-base text-gray-900 dark:text-white truncate">{{ label }}</h3>
        <p
          class="text-[10px] font-medium text-primary-600 dark:text-primary-400 uppercase tracking-wider"
        >
          {{ tagLabel ?? 'Independent Module' }}
        </p>
      </div>
    </div>

    <p class="text-sm text-gray-500 dark:text-gray-400 leading-relaxed flex-1 line-clamp-2">
      {{ description }}
    </p>

    <div
      class="flex items-center justify-end pt-2 border-t border-gray-100 dark:border-gray-800/50 mt-auto"
    >
      <div
        class="flex items-center gap-1 text-xs font-medium text-primary-600 dark:text-primary-400 opacity-0 group-hover:opacity-100 transition-all duration-200 transform translate-x-1 group-hover:translate-x-0"
      >
        <span>Launch Tool</span>
        <UIcon name="i-lucide-arrow-right" class="size-3" />
      </div>
    </div>
  </UCard>
</template>
