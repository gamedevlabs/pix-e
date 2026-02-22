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
    class="group min-h-52 flex flex-col items-center justify-center border-2 border-dashed border-gray-200 dark:border-gray-700 hover:border-primary dark:hover:border-primary bg-white dark:bg-gray-900 hover:bg-primary-50/50 dark:hover:bg-primary-950/20 transition-all duration-200 cursor-pointer shadow-sm"
    role="button"
    tabindex="0"
    :ui="{ body: 'flex-1 flex items-center justify-center p-8' }"
    @click="emit('click', $event)"
    @keydown.enter="emit('click', $event as unknown as MouseEvent)"
  >
    <div
      class="flex flex-col items-center gap-3 text-gray-400 dark:text-gray-500 group-hover:text-primary transition-colors duration-200"
    >
      <div
        class="rounded-full bg-gray-100 dark:bg-gray-800 group-hover:bg-primary-100 dark:group-hover:bg-primary-950/50 size-20 flex items-center justify-center transition-colors duration-200"
      >
        <UIcon name="i-lucide-plus" class="size-8" />
      </div>
      <p class="text-sm font-semibold tracking-wide">New Project</p>
    </div>
  </UCard>

  <!-- Regular Project Card -->
  <UContextMenu v-else :items="props.menuItems" class="h-full">
    <UCard
      class="group h-full flex flex-col min-h-52 border-l-[3px] border-l-primary/60 border border-gray-300 dark:border-gray-600 hover:border-l-primary hover:border-gray-400 dark:hover:border-gray-500 bg-white dark:bg-gray-900 hover:shadow-xl hover:-translate-y-1 transition-all duration-200 cursor-pointer"
      :ui="{
        root: 'h-full flex flex-col',
        header: 'px-5 py-4',
        body: 'flex-1 px-5 py-3',
        footer: 'px-5 py-3 border-t border-gray-200 dark:border-gray-700',
      }"
      role="button"
      tabindex="0"
      @click="emit('click', $event)"
      @keydown.enter="emit('click', $event as unknown as MouseEvent)"
    >
      <template #header>
        <div class="flex items-center justify-between gap-3">
          <!-- Avatar + name -->
          <div class="flex items-center gap-3.5 min-w-0">
            <UAvatar
              v-if="props.icon"
              :src="props.icon"
              :alt="props.label"
              size="lg"
              class="ring-2 ring-primary-200 dark:ring-primary-800 shrink-0"
            />
            <UAvatar
              v-else
              :alt="props.label"
              size="lg"
              :text="props.initials || 'PR'"
              class="shrink-0 text-primary bg-primary-100 dark:bg-primary-900/50 font-bold"
            />
            <h3 class="font-bold text-lg text-gray-900 dark:text-gray-50 truncate leading-tight">
              {{ props.label }}
            </h3>
          </div>

          <!-- 3-dot dropdown -->
          <UDropdownMenu :items="props.menuItems" class="project-menu-button shrink-0">
            <UButton
              icon="i-lucide-more-vertical"
              color="neutral"
              variant="ghost"
              size="xs"
              class="opacity-0 group-hover:opacity-100 focus:opacity-100 transition-opacity"
              @click.stop
            />
          </UDropdownMenu>
        </div>
      </template>

      <!-- Description body -->
      <p
        v-if="props.description"
        class="text-sm text-gray-600 dark:text-gray-400 line-clamp-3 leading-relaxed"
      >
        {{ props.description }}
      </p>
      <p v-else class="text-sm text-gray-400 dark:text-gray-600 italic">No description</p>

      <template #footer>
        <div class="flex items-center justify-between gap-2">
          <!-- Last edited timestamp -->
          <div class="flex items-center gap-1.5 text-[11px] text-gray-400 dark:text-gray-500 min-w-0">
            <UIcon name="i-lucide-clock" class="size-3 shrink-0" />
            <span class="truncate">{{ props.updatedAt ? formatRelativeTime(props.updatedAt) : '—' }}</span>
          </div>

          <!-- "Open →" fades in on hover -->
          <div
            class="flex items-center gap-1 text-xs font-medium text-primary opacity-0 group-hover:opacity-100 transition-opacity duration-150"
          >
            <span>Open</span>
            <UIcon name="i-lucide-arrow-right" class="size-3 group-hover:translate-x-0.5 transition-transform" />
          </div>
        </div>
      </template>
    </UCard>
  </UContextMenu>
</template>
