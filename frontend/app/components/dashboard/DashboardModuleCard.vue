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
    class="group transition-all"
    :class="[
      props.disabled
        ? 'opacity-60'
        : 'hover:shadow-lg hover:-translate-y-0.5 hover:border-primary cursor-pointer',
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
              <p class="text-base font-semibold text-gray-900 dark:text-gray-100 truncate">
                {{ props.title }}
              </p>
              <p v-if="props.description" class="text-sm text-gray-600 dark:text-gray-400">
                {{ props.description }}
              </p>
            </div>
          </div>

          <UBadge
            v-if="props.badgeLabel"
            color="primary"
            variant="subtle"
            size="xs"
            class="shrink-0"
          >
            {{ props.badgeLabel }}
          </UBadge>
        </div>

        <!-- Preview / insight area (optional) -->
        <div v-if="props.previewItems?.length" class="space-y-1">
          <div
            v-for="(item, idx) in props.previewItems"
            :key="idx"
            class="flex items-center gap-2 rounded-md bg-gray-50 dark:bg-gray-800/60 px-2 py-1"
          >
            <UIcon
              v-if="item.icon"
              :name="item.icon"
              class="size-4 text-gray-400 dark:text-gray-500 shrink-0"
            />
            <p class="text-sm text-gray-700 dark:text-gray-200 truncate">
              {{ item.text }}
            </p>
          </div>

          <p v-if="props.previewMoreLabel" class="text-xs text-gray-500 dark:text-gray-400 px-1">
            {{ props.previewMoreLabel }}
          </p>
        </div>

        <!-- Backwards-compatible insightItems grid (if still used anywhere) -->
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

        <div class="flex items-center justify-end">
          <UButton
            :label="props.ctaLabel"
            color="primary"
            variant="soft"
            size="sm"
            trailing-icon="i-lucide-arrow-right"
          />
        </div>
      </div>
    </NuxtLink>

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

          <UBadge
            v-if="props.badgeLabel"
            color="primary"
            variant="subtle"
            size="xs"
            class="shrink-0"
          >
            {{ props.badgeLabel }}
          </UBadge>
        </div>

        <!-- Preview / insight area (optional) -->
        <div v-if="props.previewItems?.length" class="space-y-1">
          <div
            v-for="(item, idx) in props.previewItems"
            :key="idx"
            class="flex items-center gap-2 rounded-md bg-gray-50 dark:bg-gray-800/60 px-2 py-1"
          >
            <UIcon
              v-if="item.icon"
              :name="item.icon"
              class="size-4 text-gray-400 dark:text-gray-500 shrink-0"
            />
            <p class="text-sm text-gray-700 dark:text-gray-200 truncate">
              {{ item.text }}
            </p>
          </div>

          <p v-if="props.previewMoreLabel" class="text-xs text-gray-500 dark:text-gray-400 px-1">
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

        <div class="flex items-center justify-end">
          <UButton
            :label="props.ctaLabel"
            color="primary"
            variant="soft"
            size="sm"
            trailing-icon="i-lucide-arrow-right"
            disabled
          />
        </div>
      </div>
    </div>
  </UCard>
</template>
