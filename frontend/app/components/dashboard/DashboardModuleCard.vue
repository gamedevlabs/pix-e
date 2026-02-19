<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  title: string
  description?: string
  icon: string
  to: string
  ctaLabel?: string
  badgeLabel?: string
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  description: undefined,
  ctaLabel: 'Open',
  badgeLabel: undefined,
  disabled: false,
})

const linkTo = computed(() => (props.disabled ? '#' : props.to))
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
      :to="linkTo"
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
