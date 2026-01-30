<script setup lang="ts">
import { ref, watch, computed } from 'vue'

// Props
interface Props {
  collapsed?: boolean
}

defineProps<Props>()

// State
const slideoverOpen = ref(false)
const openSteps = ref<Set<string>>(new Set())

// PROJECT
const { currentProjectId } = useProjectHandler()

// WORKFLOW
const projectWorkflow = useProjectWorkflow()

// Load workflow when project changes
watch(
  currentProjectId,
  async (newProjectId) => {
    if (newProjectId) {
      await projectWorkflow.loadForProject(newProjectId)
    }
  },
  { immediate: true },
)

// Computed
const currentStepIndex = computed(() => projectWorkflow.workflow.value?.currentStepIndex ?? 0)
const steps = computed(() => projectWorkflow.getSteps.value || [])
const overallProgress = computed(() => projectWorkflow.getProgress.value || 0)

// Get status icon for steps/substeps
const getStatusIcon = (status: string) => {
  switch (status) {
    case 'complete':
      return 'i-lucide-check-circle'
    case 'active':
      return 'i-lucide-circle-dot'
    default:
      return 'i-lucide-circle'
  }
}

// Get status color
const getStatusColor = (status: string) => {
  switch (status) {
    case 'complete':
      return 'text-green-500'
    case 'active':
      return 'text-blue-500'
    default:
      return 'text-gray-400'
  }
}

// Toggle step collapse
const toggleStep = (stepId: string) => {
  if (openSteps.value.has(stepId)) {
    openSteps.value.delete(stepId)
  } else {
    openSteps.value.add(stepId)
  }
}

// Check if step is open
const isStepOpen = (stepId: string) => {
  return openSteps.value.has(stepId)
}

// Initialize open steps (open active and current steps by default)
watch(
  steps,
  (newSteps) => {
    if (newSteps.length > 0) {
      newSteps.forEach((step, index) => {
        if (step.status === 'active' || index === currentStepIndex.value) {
          openSteps.value.add(step.id)
        }
      })
    }
  },
  { immediate: true },
)

// Handle navigation
const handleNavigate = (route: string) => {
  if (route) {
    navigateTo(route)
    slideoverOpen.value = false
  }
}
</script>

<template>
  <USlideover
    v-model:open="slideoverOpen"
    side="left"
    :overlay="false"
    :modal="false"
    :dismissible="false"
    :close="{ icon: 'i-lucide-arrow-left' }"
    title="Getting Started"
    description="Follow these instructions to set up your project."
  >
    <!-- Custom styled button matching screenshot -->
    <button
      v-if="!collapsed"
      class="w-full mb-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg p-3 flex items-center justify-between transition-colors group cursor-pointer"
      @click="slideoverOpen = true"
    >
      <div class="flex items-center gap-2">
        <UIcon name="i-lucide-zap" class="w-5 h-5" />
        <span class="font-medium">Getting Started</span>
      </div>
      <div class="flex items-center gap-2">
        <span class="text-sm bg-white/20 px-2 py-0.5 rounded-full"> {{ overallProgress }}% </span>
        <UIcon
          name="i-lucide-chevron-right"
          class="w-4 h-4 group-hover:translate-x-0.5 transition-transform"
        />
      </div>
    </button>

    <!-- Collapsed state button -->
    <UButton
      v-else
      icon="i-lucide-zap"
      color="primary"
      variant="solid"
      class="w-full justify-center mb-2"
    />

    <template #body>
      <div class="space-y-6 pb-6">
        <!-- Overall Progress -->
        <div class="space-y-2">
          <div class="flex items-center justify-between text-sm mb-2">
            <span class="font-medium">Overall Progress</span>
            <span class="font-semibold text-primary">{{ overallProgress }}%</span>
          </div>
          <UProgress :model-value="overallProgress" color="primary" size="sm" />
        </div>

        <UDivider />

        <!-- Workflow Steps -->
        <div class="space-y-4">
          <h3 class="text-lg font-semibold">Essentials</h3>

          <!-- Timeline with collapsible categories -->
          <UTimeline :items="steps" color="primary" size="md" class="w-full">
            <template #title="{ item }">
              <div
                class="flex items-center justify-between w-full cursor-pointer group"
                @click="toggleStep(item.id)"
              >
                <span class="font-medium group-hover:text-primary transition-colors">{{
                  item.name
                }}</span>
                <UIcon
                  v-if="item.substeps && item.substeps.length > 0"
                  :name="isStepOpen(item.id) ? 'i-lucide-chevron-up' : 'i-lucide-chevron-down'"
                  class="w-4 h-4 transition-transform text-muted group-hover:text-default"
                />
              </div>
            </template>

            <template #description="{ item }">
              <div>
                <!-- Step description - clickable to toggle -->
                <p
                  v-if="item.description"
                  class="text-sm text-muted cursor-pointer hover:text-default transition-colors"
                  @click="toggleStep(item.id)"
                >
                  {{ item.description }}
                </p>

                <!-- Substeps (collapsible) -->
                <Transition
                  enter-active-class="transition-all duration-150 ease-out"
                  enter-from-class="opacity-0 -translate-y-2"
                  enter-to-class="opacity-100 translate-y-0"
                  leave-active-class="transition-all duration-150 ease-in"
                  leave-from-class="opacity-100 translate-y-0"
                  leave-to-class="opacity-0 -translate-y-2"
                >
                  <div
                    v-if="isStepOpen(item.id) && item.substeps && item.substeps.length > 0"
                    class="space-y-1 mt-3"
                  >
                    <component
                      :is="substep.status === 'complete' ? 'div' : 'NuxtLink'"
                      v-for="substep in item.substeps"
                      :key="substep.id"
                      :to="
                        substep.status !== 'complete'
                          ? substep.route || item.route || '#'
                          : undefined
                      "
                      class="flex items-start gap-3 py-2 px-3 rounded-lg transition-colors no-underline"
                      :class="[
                        substep.status === 'complete'
                          ? 'opacity-75 cursor-default'
                          : 'hover:bg-elevated/50 cursor-pointer',
                      ]"
                      @click.prevent.stop="
                        substep.status !== 'complete' && handleNavigate(substep.route || item.route)
                      "
                    >
                      <UIcon
                        :name="getStatusIcon(substep.status)"
                        :class="[getStatusColor(substep.status), 'w-5 h-5 shrink-0 mt-0.5']"
                      />
                      <div class="flex-1 min-w-0">
                        <div
                          class="text-sm"
                          :class="substep.status === 'complete' ? 'line-through text-muted' : ''"
                        >
                          {{ substep.name }}
                        </div>
                        <div v-if="substep.description" class="text-xs text-muted mt-0.5">
                          {{ substep.description }}
                        </div>
                      </div>
                    </component>
                  </div>
                </Transition>
              </div>
            </template>

            <template #indicator="{ item }">
              <div
                class="relative flex items-center justify-center cursor-pointer"
                @click="toggleStep(item.id)"
              >
                <UIcon
                  :name="getStatusIcon(item.status)"
                  :class="[getStatusColor(item.status), 'w-5 h-5']"
                />
              </div>
            </template>
          </UTimeline>
        </div>
      </div>
    </template>
  </USlideover>
</template>
