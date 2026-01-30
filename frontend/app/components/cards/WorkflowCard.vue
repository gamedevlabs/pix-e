<script setup lang="ts">
import { onMounted, computed } from '#imports'
import type { WorkflowStep } from '~/composables/useProjectWorkflow'
import { useProjectWorkflow } from '~/composables/useProjectWorkflow'
import type { StepperItem } from '@nuxt/ui'

interface Props {
  projectId?: string
  orientation?: 'horizontal' | 'vertical'
}

const props = withDefaults(defineProps<Props>(), {
  projectId: 'pixe',
  orientation: 'vertical',
})

const { loading, loadForProject, getSteps, getCurrentStep } = useProjectWorkflow()

const router = useRouter()

onMounted(async () => {
  await loadForProject(props.projectId)
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
  }
}
</script>

<template>
  <DashboardCard title="Workflow" icon="i-lucide-list-checks">
    <template #actions>
      <UButton
        v-if="current?.route"
        color="primary"
        size="sm"
        trailing-icon="i-lucide-arrow-right"
        @click="navigateToCurrentStep"
      >
        Continue
      </UButton>
    </template>

    <div class="space-y-4">
      <!-- Stepper -->
      <UStepper
        v-if="!loading && stepperItems.length > 0"
        :model-value="activeStepValue"
        :items="stepperItems"
        color="primary"
        :orientation="orientation"
        size="sm"
        class="w-full"
        :ui="{
          trigger:
            'group-data-[state=active]:bg-elevated group-data-[state=active]:border-2 group-data-[state=active]:border-primary-500 dark:group-data-[state=active]:border-primary-400 group-data-[state=active]:text-default',
          item: orientation === 'vertical' ? 'w-full' : undefined,
          wrapper: orientation === 'vertical' ? 'flex-1' : undefined,
        }"
        @update:model-value="handleStepClick"
      >
        <template v-for="(step, index) in steps" :key="step.id" #[`${step.id}-icon`]>
          <UIcon v-if="step.status === 'complete'" name="i-lucide-check" class="size-5" />
          <span v-else class="text-sm font-medium">{{ index + 1 }}</span>
        </template>
      </UStepper>

      <!-- Loading state -->
      <div v-else-if="loading" class="flex items-center justify-center py-8">
        <UIcon name="i-lucide-loader-2" class="animate-spin text-primary-500" />
      </div>
    </div>
  </DashboardCard>
</template>
