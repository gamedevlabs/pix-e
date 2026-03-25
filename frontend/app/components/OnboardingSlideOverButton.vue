<script setup lang="ts">
import { computed } from 'vue'
import { useWorkflowSlideover } from '~/composables/useWorkflowSlideover'

interface Props {
  /** When true, render the compact icon-only variant (for collapsed sidebar). */
  collapsed?: boolean
  /** Title text shown on the left side of the button. */
  title?: string
  /** Progress percentage pill on the right. If omitted, no pill is shown. */
  progress?: number | null
  /** Show text inside the pill (defaults to progress% if progress provided, otherwise "Show"). */
  pillText?: string
}

const props = withDefaults(defineProps<Props>(), {
  collapsed: false,
  title: 'Onboarding Wizard',
  progress: null,
  pillText: 'Show',
})

const workflowSlideover = useWorkflowSlideover()

const pillLabel = computed(() => {
  if (props.progress === null || props.progress === undefined) return props.pillText
  return `${props.progress}%`
})
</script>

<template>
  <button
    v-if="!collapsed"
    class="w-full mb-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg p-3 flex items-center justify-between transition-colors group cursor-pointer"
    @click="workflowSlideover.toggle()"
  >
    <span class="flex items-center gap-2 min-w-0">
      <UIcon name="i-lucide-zap" class="w-5 h-5 shrink-0" />
      <span class="font-medium truncate">{{ title }}</span>
    </span>

    <span class="flex items-center gap-2 shrink-0">
      <span v-if="pillLabel" class="text-sm bg-white/20 px-2 py-0.5 rounded-full">
        {{ pillLabel }}
      </span>
      <UIcon
        name="i-lucide-chevron-right"
        class="w-4 h-4 group-hover:translate-x-0.5 transition-transform"
      />
    </span>
  </button>

  <UButton
    v-else
    icon="i-lucide-zap"
    color="primary"
    variant="solid"
    class="w-full justify-center mb-2"
    @click="workflowSlideover.toggle()"
  />
</template>
