<script setup lang="ts">
interface PreviewItem {
  text: string
  icon?: string
}

interface InsightItem {
  label: string
  value?: string | number
  icon?: string
}

interface Props {
  title: string
  description?: string
  icon: string
  to: string
  ctaLabel?: string
  badgeLabel?: string
  disabled?: boolean
  insightItems?: InsightItem[]
  previewItems?: PreviewItem[]
  previewMoreLabel?: string
}

const props = withDefaults(defineProps<Props>(), {
  description: undefined,
  ctaLabel: 'Open',
  badgeLabel: undefined,
  disabled: false,
  insightItems: undefined,
  previewItems: undefined,
  previewMoreLabel: undefined,
})
</script>

<template>
  <UCard
    class="group transition-all border-l-[3px] border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900"
    :class="[
      props.disabled
        ? 'opacity-60 border-l-gray-300 dark:border-l-gray-600'
        : 'border-l-primary/60 hover:border-l-primary hover:border-gray-400 dark:hover:border-gray-500 hover:shadow-xl hover:-translate-y-1 cursor-pointer',
    ]"
  >
    <NuxtLink
      v-if="!props.disabled"
      :to="{ path: props.to }"
      class="block"
      :aria-label="`${props.title}: ${props.ctaLabel}`"
    >
      <div class="space-y-4">
        <div class="flex items-start justify-between gap-3">
          <div class="flex items-start gap-3 min-w-0">
            <div
              class="mt-0.5 rounded-md p-2 bg-primary-50 dark:bg-primary-950/30 text-primary shrink-0"
            >
              <UIcon :name="props.icon" class="size-5" />
            </div>
            <div class="min-w-0">
              <p class="text-base font-bold text-gray-900 dark:text-gray-100 truncate">
                {{ props.title }}
              </p>
              <p v-if="props.description" class="text-sm text-gray-500 dark:text-gray-400">
                {{ props.description }}
              </p>
            </div>
          </div>

          <!-- Hover "Open →" label (replaces badge) -->
          <div
            class="flex items-center gap-1 text-xs font-medium text-primary opacity-0 group-hover:opacity-100 transition-opacity duration-150 shrink-0 mt-0.5"
          >
            <span>{{ props.ctaLabel }}</span>
            <UIcon
              name="i-lucide-arrow-right"
              class="size-3 group-hover:translate-x-0.5 transition-transform"
            />
          </div>
        </div>

        <!-- Preview items list -->
        <div v-if="props.previewItems?.length" class="space-y-1.5">
          <div
            v-for="(item, idx) in props.previewItems"
            :key="idx"
            class="flex items-center gap-2.5 rounded-md bg-gray-50 dark:bg-gray-800/60 px-3 py-2"
          >
            <UIcon
              v-if="item.icon"
              :name="item.icon"
              class="size-4 text-primary/70 dark:text-primary/60 shrink-0"
            />
            <p class="text-sm font-medium text-gray-800 dark:text-gray-100 truncate">
              {{ item.text }}
            </p>
          </div>

          <p
            v-if="props.previewMoreLabel"
            class="text-sm text-gray-500 dark:text-gray-400 px-1 pt-0.5"
          >
            {{ props.previewMoreLabel }}
          </p>
        </div>

        <!-- Backwards-compatible insightItems grid -->
        <div v-else-if="props.insightItems?.length" class="grid grid-cols-2 gap-2">
          <div
            v-for="(item, idx) in props.insightItems"
            :key="idx"
            class="flex items-center gap-2 rounded-md bg-gray-50 dark:bg-gray-800/60 px-2 py-1"
          >
            <UIcon
              v-if="item.icon"
              :name="item.icon"
              class="size-4 text-gray-400 dark:text-gray-500"
            />
            <div class="min-w-0">
              <p class="text-[11px] leading-4 text-gray-500 dark:text-gray-400 truncate">
                {{ item.label }}
              </p>
              <p class="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                {{ item.value ?? '—' }}
              </p>
            </div>
          </div>
        </div>
        <slot v-else name="insight" />
      </div>
    </NuxtLink>

    <!-- Disabled state -->
    <div v-else class="block" aria-disabled="true">
      <div class="space-y-4">
        <div class="flex items-start justify-between gap-3">
          <div class="flex items-start gap-3 min-w-0">
            <div
              class="mt-0.5 rounded-md p-2 bg-primary-50 dark:bg-primary-950/30 text-primary shrink-0"
            >
              <UIcon :name="props.icon" class="size-5" />
            </div>
            <div class="min-w-0">
              <p class="text-base font-semibold text-gray-900 dark:text-gray-100 truncate">
                {{ props.title }}
              </p>
              <p v-if="props.description" class="text-sm text-gray-600 dark:text-gray-400">
                {{ props.description }}
              </p>
            </div>
          </div>
        </div>

        <!-- Preview items list (disabled) -->
        <div v-if="props.previewItems?.length" class="space-y-1.5">
          <div
            v-for="(item, idx) in props.previewItems"
            :key="idx"
            class="flex items-center gap-2.5 rounded-md bg-gray-50 dark:bg-gray-800/60 px-3 py-2"
          >
            <UIcon
              v-if="item.icon"
              :name="item.icon"
              class="size-4 text-primary/70 dark:text-primary/60 shrink-0"
            />
            <p class="text-sm font-medium text-gray-800 dark:text-gray-100 truncate">
              {{ item.text }}
            </p>
          </div>
          <p
            v-if="props.previewMoreLabel"
            class="text-sm text-gray-500 dark:text-gray-400 px-1 pt-0.5"
          >
            {{ props.previewMoreLabel }}
          </p>
        </div>

        <div v-else-if="props.insightItems?.length" class="grid grid-cols-2 gap-2">
          <div
            v-for="(item, idx) in props.insightItems"
            :key="idx"
            class="flex items-center gap-2 rounded-md bg-gray-50 dark:bg-gray-800/60 px-2 py-1"
          >
            <UIcon
              v-if="item.icon"
              :name="item.icon"
              class="size-4 text-gray-400 dark:text-gray-500"
            />
            <div class="min-w-0">
              <p class="text-[11px] leading-4 text-gray-500 dark:text-gray-400 truncate">
                {{ item.label }}
              </p>
              <p class="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                {{ item.value ?? '—' }}
              </p>
            </div>
          </div>
        </div>
        <slot v-else name="insight" />
      </div>
    </div>
  </UCard>
</template>
