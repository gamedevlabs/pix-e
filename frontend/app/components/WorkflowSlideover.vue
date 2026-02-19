<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useWorkflowSlideover } from '~/composables/useWorkflowSlideover'
import type { MockWorkflow } from '~/mock_data/mock_workflow'
import type { StepStatus } from '~/utils/workflow'

// Props
interface Props {
  collapsed?: boolean
}

defineProps<Props>()

// State
const workflowSlideover = useWorkflowSlideover()
const slideoverOpen = workflowSlideover.isOpen
const openSteps = ref<Set<string>>(new Set())

// Phases picker should be less prominent; collapse by default.
const phasesOpen = ref(false)

// PROJECT
const { currentProjectId, projects } = useProjectHandler()
const authentication = useAuthentication()

// WORKFLOW
const projectWorkflow = useProjectWorkflow()

const hasProjects = computed(() => (projects.value?.length ?? 0) > 0)
const isLoggedIn = computed(() => authentication.isLoggedIn.value)

// Workflows + active selection (additive API)
const availableWorkflows = computed(
  () => (projectWorkflow.workflows?.value || []) as MockWorkflow[],
)
const activeWorkflowId = computed(() => projectWorkflow.activeWorkflowId?.value)

// Load workflows depending on context:
// - If user is logged in and has no projects: show onboarding (user-level)
// - If a project is selected: show project workflows
watch(
  [currentProjectId, hasProjects, isLoggedIn],
  async ([newProjectId, _hasAnyProjects, loggedIn]) => {
    if (!loggedIn) return

    // If no project is selected, show the standalone onboarding workflow.
    if (!newProjectId) {
      await projectWorkflow.loadForUser()
      return
    }

    // Otherwise, show project workflows.
    await projectWorkflow.loadForProject(newProjectId)
  },
  { immediate: true },
)

// Refresh workflow data
const refreshWorkflow = async () => {
  if (!isLoggedIn.value) return

  // If no project is selected, show the standalone onboarding workflow.
  if (!currentProjectId.value) {
    await projectWorkflow.loadForUser()
    return
  }

  await projectWorkflow.loadForProject(currentProjectId.value)
}

// Watch for when slideover opens and refresh data
watch(slideoverOpen, async (isOpen) => {
  if (isOpen) {
    await refreshWorkflow()
  }
})

// Watch for workflow changes and auto-refresh
watch(
  () => projectWorkflow.workflow.value,
  () => {
    // Force reactivity update by triggering computed recalculation
    if (slideoverOpen.value) {
      // Workflow state changed, computed properties will automatically update
    }
  },
  { deep: true },
)

// Computed
const currentStepIndex = computed(() => projectWorkflow.workflow.value?.currentStepIndex ?? 0)
const steps = computed(() => projectWorkflow.getSteps.value || [])
const overallProgress = computed(() => projectWorkflow.getProgress.value || 0)

const activeWorkflowTitle = computed(() => {
  const w = availableWorkflows.value.find((x) => x.id === activeWorkflowId.value)
  return w?.meta?.title || 'Workflow'
})

const activeWorkflowPhase = computed(() => {
  const w = availableWorkflows.value.find((x) => x.id === activeWorkflowId.value)
  const folder = w?.meta?.folder
  return folder ? displayPhaseName(folder) : null
})

const groupedWorkflows = computed(() => {
  const groups: Record<string, MockWorkflow[]> = {}
  for (const w of availableWorkflows.value) {
    const folder = w.meta?.folder || 'Workflows'
    if (!groups[folder]) groups[folder] = []
    groups[folder].push(w)
  }
  // Desired display order for the phase picker.
  const phaseOrder = ['Onboarding', 'Concept and Planning', 'Validation', 'Discover'] as const

  // Some phases are named differently in workflow meta (e.g. "Concept & Design").
  // Map these to the desired canonical phases so ordering stays correct.
  const canonicalizePhase = (folder: string) => {
    const raw = displayPhaseName(folder).trim().toLowerCase()

    if (raw.includes('onboard')) return 'onboarding'
    if (raw.includes('valid')) return 'validation'
    if (raw.includes('discover')) return 'discover'

    // Concept & Planning bucket (common variants)
    if (
      raw.includes('concept') ||
      raw.includes('plan') ||
      raw.includes('design') ||
      raw.includes('&')
    ) {
      return 'concept and planning'
    }

    return raw
  }

  const phaseIndex = (folder: string) => {
    const canonical = canonicalizePhase(folder)
    const idx = phaseOrder.findIndex((p) => p.toLowerCase() === canonical)
    return idx === -1 ? Number.POSITIVE_INFINITY : idx
  }

  return Object.entries(groups)
    .map(([folder, items]) => ({ folder, items }))
    .sort((a, b) => {
      const ai = phaseIndex(a.folder)
      const bi = phaseIndex(b.folder)
      if (ai !== bi) return ai - bi
      // Unknown phases (or ties) fall back to alpha by display name
      return displayPhaseName(a.folder).localeCompare(displayPhaseName(b.folder))
    })
})

const displayPhaseName = (folder: string) => folder.replace(/^\d+\s*-\s*/u, '')

const getWorkflowStatus = (w: MockWorkflow): StepStatus => {
  if (w.finished_at) return 'complete'
  if (w.id === activeWorkflowId.value) return 'active'
  const total = w.steps.flatMap((s) => s.substeps).length
  const completed = w.steps
    .flatMap((s) => s.substeps)
    .filter((ss) => ss.status === 'complete').length
  if (total > 0 && completed === total) return 'complete'
  return completed > 0 ? 'active' : 'pending'
}

const selectWorkflow = async (id: string) => {
  await projectWorkflow.selectWorkflow(id, currentProjectId.value)
  openSteps.value = new Set()
}

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
    workflowSlideover.close()
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
    title="Workflow Guide"
    description="Pick a phase and continue your current step. Your progress is saved automatically."
    @update:open="(v) => (v ? workflowSlideover.open() : workflowSlideover.close())"
    @close="workflowSlideover.close()"
  >
    <template #body>
      <!-- Use a vertical layout where the active workflow takes most space, and phases are at the bottom. -->
      <div class="flex flex-col h-full pb-6">
        <!-- MAIN: Active workflow (dominant) -->
        <div class="flex-1 min-h-0 overflow-auto pr-1">
          <div class="space-y-4">
            <h3 class="text-lg font-semibold">{{ activeWorkflowTitle }}</h3>

            <!-- Overall Progress (kept near top) -->
            <div class="space-y-2">
              <div class="flex items-center justify-between text-sm mb-2">
                <span class="font-medium">Overall Progress</span>
                <span class="font-semibold text-primary">{{ overallProgress }}%</span>
              </div>
              <UProgress :model-value="overallProgress" color="primary" size="sm" />
            </div>

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
                          substep.status !== 'complete' &&
                          handleNavigate(substep.route || item.route)
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

        <!-- BOTTOM: Phases / workflow picker (de-emphasized) -->
        <div v-if="availableWorkflows.length > 1" class="mt-4 pt-4 border-t border-default/20">
          <UCollapsible v-model:open="phasesOpen" class="flex flex-col gap-2">
            <UButton
              class="group bg-elevated/30 border border-default/20"
              color="neutral"
              variant="ghost"
              block
              :ui="{
                trailingIcon:
                  'group-data-[state=open]:rotate-180 transition-transform duration-200',
              }"
            >
              <template #leading>
                <UIcon name="i-lucide-layers" class="w-4 h-4 text-muted" />
              </template>

              <div class="flex-1 min-w-0 text-left">
                <div class="font-semibold text-sm text-default">Phases</div>
                <div v-if="activeWorkflowPhase" class="text-xs text-muted truncate">
                  Current: <span class="font-medium text-default">{{ activeWorkflowPhase }}</span>
                </div>
              </div>

              <template #trailing>
                <UIcon name="i-lucide-chevron-down" class="w-4 h-4 text-muted" />
              </template>
            </UButton>

            <template #content>
              <div class="bg-elevated/20 border border-default/10 rounded-lg p-3">
                <div class="space-y-3">
                  <div v-for="group in groupedWorkflows" :key="group.folder" class="space-y-1">
                    <div class="text-[11px] uppercase tracking-wide text-muted">
                      {{ displayPhaseName(group.folder) }}
                    </div>

                    <div class="grid grid-cols-1 gap-1">
                      <UButton
                        v-for="w in group.items"
                        :key="w.id"
                        color="neutral"
                        :variant="w.id === activeWorkflowId ? 'soft' : 'ghost'"
                        size="sm"
                        block
                        class="justify-between"
                        @click="selectWorkflow(w.id)"
                      >
                        <template #leading>
                          <UIcon
                            :name="getStatusIcon(getWorkflowStatus(w))"
                            :class="[getStatusColor(getWorkflowStatus(w)), 'w-4 h-4']"
                          />
                        </template>

                        <span class="truncate text-left flex-1">
                          {{ w.meta?.title || w.id }}
                        </span>

                        <template #trailing>
                          <span
                            v-if="w.id === activeWorkflowId"
                            class="text-[11px] text-primary font-semibold"
                          >
                            Active
                          </span>
                        </template>
                      </UButton>
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </UCollapsible>
        </div>
      </div>
    </template>
  </USlideover>
</template>
