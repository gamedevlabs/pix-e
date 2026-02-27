<script setup lang="ts">
import { onMounted, computed, watch } from '#imports'
import type { WorkflowStep } from '~/utils/workflow'
import { useProjectWorkflow } from '~/composables/useProjectWorkflow'
import type { StepperItem } from '@nuxt/ui'
import { useWorkflowSlideover } from '~/composables/useWorkflowSlideover'

interface Props {
  orientation?: 'horizontal' | 'vertical'
}

const { orientation } = withDefaults(defineProps<Props>(), {
  orientation: 'vertical',
})

const { currentProjectId } = useProjectHandler()
const { loading, loadForProject, getSteps, getCurrentStep } = useProjectWorkflow()
const { open: openSlideover } = useWorkflowSlideover()

const router = useRouter()

// Load workflow for the current project. loadForProject is idempotent —
// it skips the DB call when the same project is already loaded in memory.
onMounted(async () => {
  if (currentProjectId.value) {
    await loadForProject(currentProjectId.value)
  }
})

// Also react if the project changes after mount
watch(currentProjectId, async (newId) => {
  if (newId) {
    await loadForProject(newId)
  }
})

const steps = computed(() => getSteps.value as WorkflowStep[])
const current = computed(() => getCurrentStep.value as WorkflowStep | null)

// Convert workflow steps to Stepper items
const stepperItems = computed<StepperItem[]>(() => {
  return steps.value.map((step, index) => ({
    title: step.name,
    description: step.description,
    value: step.id,
    disabled: step.status !== 'active', // Only active step is clickable
    icon: step.status === 'complete' ? 'i-lucide-check' : undefined,
    slot: step.status !== 'complete' ? (index + 1).toString() : undefined, // Show step number
  }))
})

// Current active step value for v-model
const activeStepValue = computed(() => current.value?.id || steps.value[0]?.id)

// Handle step click - only navigate if it's the active step
const handleStepClick = (value: string | number) => {
  const step = steps.value.find((s) => s.id === value)
  if (step && step.status === 'active' && step.route) {
    router.push(step.route)
  }
}

// Navigate to current step
const navigateToCurrentStep = () => {
  if (current.value?.route) {
    router.push(current.value.route)
    openSlideover()
  }
}
</script>

<template>
  <DashboardCard title="Workflow" icon="i-lucide-list-checks">
    <template #actions>
      <UButton
        v-if="!loading && current?.route"
        color="primary"
        size="sm"
        trailing-icon="i-lucide-arrow-right"
        @click="navigateToCurrentStep"
      >
        Continue
      </UButton>
    </template>

    <div class="space-y-4">
      <!-- Loading state (skeleton + spinner) -->
      <div v-if="loading" class="space-y-4">
        <div class="flex items-center justify-between">
          <div class="h-4 w-44 rounded bg-gray-200/70 dark:bg-gray-800/70 animate-pulse" />
          <div class="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
            <UIcon name="i-lucide-loader-2" class="animate-spin" />
            <span>Loading workflow…</span>
          </div>
        </div>

        <div class="space-y-3">
          <div class="h-10 rounded bg-gray-200/70 dark:bg-gray-800/70 animate-pulse" />
          <div class="h-10 rounded bg-gray-200/60 dark:bg-gray-800/60 animate-pulse" />
          <div class="h-10 rounded bg-gray-200/50 dark:bg-gray-800/50 animate-pulse" />
        </div>
      </div>

      <!-- Stepper -->
      <UStepper
        v-else-if="stepperItems.length > 0"
        :model-value="activeStepValue"
        :items="stepperItems"
        color="primary"
        :orientation="orientation"
        size="sm"
        class="w-full"
        :ui="{
          trigger: [
            'group-data-[state=active]:bg-elevated',
            'group-data-[state=active]:border-2',
            'group-data-[state=active]:border-primary-500',
            'dark:group-data-[state=active]:border-primary-400',
            'group-data-[state=active]:text-default',
          ].join(' '),
          item: orientation === 'vertical' ? 'w-full' : undefined,
          wrapper: orientation === 'vertical' ? 'flex-1 min-w-0' : undefined,
          header: orientation === 'vertical' ? 'w-full' : undefined,
          content: 'hidden',
        }"
        @update:model-value="handleStepClick"
      >
        <template v-for="(step, index) in steps" :key="step.id" #[`${step.id}-icon`]>
          <UIcon v-if="step.status === 'complete'" name="i-lucide-check" class="size-5" />
          <span v-else class="text-sm font-medium">{{ index + 1 }}</span>
        </template>
      </UStepper>

      <!-- Empty state (after loading) -->
      <div v-else class="py-6">
        <div class="flex items-start gap-3">
          <UIcon name="i-lucide-inbox" class="mt-0.5 text-gray-500 dark:text-gray-400" />
          <div>
            <p class="text-sm font-medium text-gray-900 dark:text-gray-100">No workflow yet</p>
            <p class="text-sm text-gray-600 dark:text-gray-400">
              Once a workflow is created for this project, it’ll show up here so you can continue
              where you left off.
            </p>
          </div>
        </div>
      </div>
    </div>
  </DashboardCard>
</template>
