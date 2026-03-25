<script setup lang="ts">
import { computed } from 'vue'
import type { ProjectTargetPlatform } from '~/utils/project.d'
import { platformConfigs } from '~/utils/platformConfig'

const model = defineModel<ProjectTargetPlatform[]>({ required: true })

const props = withDefaults(
  defineProps<{
    disabled?: boolean
    label?: string
    required?: boolean
    error?: string
    hint?: string
  }>(),
  {
    label: 'Target Platforms',
    required: false,
    error: '',
    hint: '',
  },
)

type PlatformItem = { value: ProjectTargetPlatform; label: string; icon: string }

function coerceArray(v: unknown): ProjectTargetPlatform[] {
  if (!v) return []
  if (Array.isArray(v)) return v as ProjectTargetPlatform[]
  return [v as ProjectTargetPlatform]
}

function toggle(value: ProjectTargetPlatform) {
  if (props.disabled) return
  const next = new Set(coerceArray(model.value))
  if (next.has(value)) next.delete(value)
  else next.add(value)
  model.value = Array.from(next)
}

const items = computed<PlatformItem[]>(() => platformConfigs)
</script>

<template>
  <UFormField :label="props.label" :required="props.required" :error="props.error">
    <UCheckboxGroup
      v-model="model"
      variant="table"
      indicator="hidden"
      :items="items"
      :disabled="props.disabled"
      class="w-full"
    >
      <template #label="{ item }">
        <!-- UCheckboxGroup slot typing is generic; in our case items always match PlatformItem. -->
        <!-- Make it obvious the whole row is clickable -->
        <button
          type="button"
          class="w-full flex items-center gap-2 text-left cursor-pointer"
          :class="props.disabled ? 'cursor-not-allowed opacity-60' : 'hover:text-primary'"
          @click.stop.prevent="toggle((item as unknown as PlatformItem).value)"
        >
          <UIcon :name="(item as unknown as PlatformItem).icon" class="w-5 h-5 shrink-0" />
          <span class="flex-1">{{ (item as unknown as PlatformItem).label }}</span>
          <UIcon
            v-if="model.includes((item as unknown as PlatformItem).value)"
            name="i-lucide-check"
            class="w-4 h-4 text-primary"
          />
        </button>
      </template>
    </UCheckboxGroup>

    <template v-if="props.hint" #hint>
      <p class="text-xs text-gray-500 mt-2">{{ props.hint }}</p>
    </template>
  </UFormField>
</template>
