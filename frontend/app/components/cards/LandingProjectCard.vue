<script setup lang="ts">
import type { DropdownMenuItem } from '@nuxt/ui'

interface Props {
  id: string
  label: string
  description?: string
  icon?: string
  initials?: string
  updatedAt?: string
  isCreateCard?: boolean
  menuItems?: DropdownMenuItem[][]
}

const props = withDefaults(defineProps<Props>(), {
  description: undefined,
  icon: undefined,
  initials: undefined,
  updatedAt: undefined,
  isCreateCard: false,
  menuItems: () => [],
})

const emit = defineEmits<{
  (e: 'click', event: MouseEvent): void
}>()

const formatRelativeTime = (dateString: string): string => {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`
  if (diffDays < 365) return `${Math.floor(diffDays / 30)}mo ago`
  return `${Math.floor(diffDays / 365)}y ago`
}
</script>

<template>
  <!-- Create New Project Card -->
  <UCard
    v-if="props.isCreateCard"
    class="group h-full min-h-45 flex flex-col items-center justify-center border border-dashed border-gray-300 dark:border-gray-700 hover:border-primary-500 hover:bg-primary-50/50 dark:hover:bg-primary-950/10 transition-all duration-200 cursor-pointer shadow-sm rounded-xl"
    role="button"
    tabindex="0"
    :ui="{ body: 'flex-1 flex flex-col items-center justify-center p-6 gap-2' }"
    @click="emit('click', $event)"
    @keydown.enter="emit('click', $event as unknown as MouseEvent)"
  >
    <div
      class="rounded-full bg-gray-100 dark:bg-gray-800 group-hover:bg-primary-100 dark:group-hover:bg-primary-900/30 p-4 transition-colors duration-200"
    >
      <UIcon name="i-lucide-plus" class="size-6 text-gray-400 group-hover:text-primary-600 dark:text-gray-500 dark:group-hover:text-primary-400" />
    </div>
    <p class="text-sm font-medium text-gray-500 group-hover:text-primary-600 dark:text-gray-400 dark:group-hover:text-primary-400 transition-colors">Create Project</p>
  </UCard>

  <!-- Regular Project Card -->
  <UContextMenu v-else :items="props.menuItems" class="h-full">
    <UCard
      class="group h-full flex flex-col min-h-45 border border-gray-200 dark:border-gray-800 hover:border-primary-300 dark:hover:border-primary-700/50 bg-white dark:bg-gray-900 hover:shadow-md hover:-translate-y-1 transition-all duration-200 cursor-pointer rounded-xl overflow-hidden"
      :ui="{
        root: 'h-full flex flex-col',
        body: 'flex-1 p-5 flex flex-col gap-4',
        header: '',     // No header slot
        footer: ''      // No footer slot
      }"
      role="button"
      tabindex="0"
      @click="emit('click', $event)"
      @keydown.enter="emit('click', $event as unknown as MouseEvent)"
    >
      <!-- Top Section: Icon + Title + Menu -->
      <div class="flex items-start justify-between gap-3">
        <div class="flex items-center gap-3 min-w-0">
          <UAvatar
            v-if="props.icon"
            :src="props.icon"
            :alt="props.label"
            size="md"
            class="ring-1 ring-gray-200 dark:ring-gray-700 shrink-0"
          />
          <UAvatar
            v-else
            :alt="props.label"
            size="md"
            :text="props.initials || 'PR'"
            class="shrink-0 text-primary-700 bg-primary-100 dark:text-primary-200 dark:bg-primary-900/30 font-semibold ring-1 ring-primary-200 dark:ring-primary-900"
          />
          
          <h3 class="font-semibold text-base text-gray-900 dark:text-white truncate">
            {{ props.label }}
          </h3>
        </div>

        <!-- 3-dot dropdown (only visible on hover/focus to keep it clean) -->
        <div class="shrink-0 -mr-2 -mt-2">
           <UDropdownMenu :items="props.menuItems" class="project-menu-button">
            <UButton
              icon="i-lucide-more-vertical"
              color="neutral"
              variant="ghost"
              size="xs"
              class="opacity-0 group-hover:opacity-100 focus:opacity-100 transition-opacity text-gray-500"
              @click.stop
            />
          </UDropdownMenu>
        </div>
      </div>

      <!-- Description body -->
      <div class="flex-1">
        <p
          v-if="props.description"
          class="text-sm text-gray-500 dark:text-gray-400 line-clamp-2 leading-relaxed"
        >
          {{ props.description }}
        </p>
        <p v-else class="text-sm text-gray-400 dark:text-gray-600 italic">
          No description
        </p>
      </div>

      <!-- Bottom Meta -->
      <div class="flex items-center justify-between pt-2 border-t border-gray-100 dark:border-gray-800/50 mt-auto">
        <div class="flex items-center gap-1.5 text-xs text-gray-400 dark:text-gray-500">
          <UIcon name="i-lucide-clock" class="size-3" />
          <span>{{ props.updatedAt ? formatRelativeTime(props.updatedAt) : '—' }}</span>
        </div>

        <div class="flex items-center gap-1 text-xs font-medium text-primary-600 dark:text-primary-400 opacity-0 group-hover:opacity-100 transition-all duration-200 transform translate-x-1 group-hover:translate-x-0">
          <span>Open</span>
          <UIcon name="i-lucide-arrow-right" class="size-3" />
        </div>
      </div>
    </UCard>
  </UContextMenu>
</template>
