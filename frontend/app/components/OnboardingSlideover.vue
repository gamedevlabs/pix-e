<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useWorkflowSlideover } from '~/composables/useWorkflowSlideover'
import type { WorkflowInstance } from '~/mock_data/mock_workflow'
import type { StepStatus } from '~/utils/workflow'

// State
const workflowSlideover = useWorkflowSlideover()
const slideoverOpen = workflowSlideover.isOpen
const openSteps = ref<Set<string>>(new Set())
const isPinned = ref(true)

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
  () => (projectWorkflow.workflows?.value || []) as WorkflowInstance[],
)
const activeWorkflowId = computed(() => projectWorkflow.activeWorkflowId?.value)

// The workflow currently being *viewed* in the panel (may differ from activeWorkflowId)
const viewedWorkflowId = computed(() => {
  // Expose viewedWorkflowId from the composable if set, otherwise fall back to activeWorkflowId
  // We read from the workflow itself since viewedWorkflowId is internal to the composable
  return projectWorkflow.workflow.value?.id ?? activeWorkflowId.value
})

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
const allWorkflowsDone = computed(() => projectWorkflow.allWorkflowsDone.value)

const activeWorkflowTitle = computed(() => {
  const id = viewedWorkflowId.value ?? activeWorkflowId.value
  const w = availableWorkflows.value.find((x) => x.id === id)
  return w?.meta?.title || 'Workflow'
})

const activeWorkflowDescription = computed(() => {
  const id = viewedWorkflowId.value ?? activeWorkflowId.value
  const w = availableWorkflows.value.find((x) => x.id === id)
  return w?.meta?.description ?? null
})

const activeWorkflowPhase = computed(() => {
  const w = availableWorkflows.value.find((x) => x.id === activeWorkflowId.value)
  const folder = w?.meta?.folder
  return folder ? displayPhaseName(folder) : null
})

const groupedWorkflows = computed(() => {
  const groups: Record<string, WorkflowInstance[]> = {}
  for (const w of availableWorkflows.value) {
    const folder = w.meta?.folder || 'Workflows'
    if (!groups[folder]) groups[folder] = []
    groups[folder].push(w)
  }
  // Desired display order for the phase picker.
  const phaseOrder = ['Onboarding', 'Design & Validation', 'Discover More'] as const

  const canonicalizePhase = (folder: string) => {
    const raw = displayPhaseName(folder).trim().toLowerCase()
    if (raw.includes('onboard')) return 'onboarding'
    if (raw.includes('discover')) return 'discover more'
    if (raw.includes('design') || raw.includes('validation')) return 'design & validation'
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

const getWorkflowStatus = (w: WorkflowInstance): StepStatus => {
  if (w.finished_at) return 'complete'
  if (w.id === activeWorkflowId.value) return 'active'
  const total = w.steps.flatMap((s) => s.substeps).length
  const completed = w.steps
    .flatMap((s) => s.substeps)
    .filter((ss) => ss.status === 'complete').length
  if (total > 0 && completed === total) return 'complete'
  return completed > 0 ? 'active' : 'pending'
}

// Preview a workflow without changing the active state
const viewWorkflow = async (id: string) => {
  await projectWorkflow.viewWorkflow(id)
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

// Width is fixed to match a reasonable sidebar size
</script>

<template>
  <USlideover
    v-model:open="slideoverOpen"
    side="right"
    :overlay="false"
    :modal="false"
    :dismissible="!isPinned"
    :close="false"
    :ui="{ content: 'max-w-xs xl:max-w-sm 2xl:max-w-sm' }"
    @update:open="(v) => (v ? workflowSlideover.open() : workflowSlideover.close())"
    @close="workflowSlideover.close()"
  >
    <template #header>
      <div class="w-full flex flex-col gap-1">
        <div class="flex items-center justify-between">
          <h3 class="font-semibold text-gray-900 dark:text-white">Onboarding Wizard</h3>
          <div class="flex items-center gap-1">
            <UButton
              :icon="isPinned ? 'i-lucide-pin' : 'i-lucide-pin-off'"
              :color="isPinned ? 'primary' : 'neutral'"
              :variant="isPinned ? 'soft' : 'ghost'"
              size="sm"
              @click="isPinned = !isPinned"
            />
            <UButton
              icon="i-lucide-x"
              color="neutral"
              variant="ghost"
              size="sm"
              @click="workflowSlideover.close()"
            />
          </div>
        </div>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          Pick a phase and continue your current step. Your progress is saved automatically.
        </p>
      </div>
    </template>
    <template #body>
      <!-- Use a vertical layout where the active workflow takes most space, and phases are at the bottom. -->
      <div class="flex flex-col h-full pb-6">
        <!-- MAIN: Active workflow (dominant) -->
        <div class="flex-1 min-h-0 overflow-auto pr-1">
          <!-- ALL DONE state -->
          <div
            v-if="allWorkflowsDone"
            class="flex flex-col items-center justify-center h-full text-center py-10 px-4"
          >
            <div
              class="w-20 h-20 rounded-full bg-green-500/10 flex items-center justify-center mb-5"
            >
              <UIcon name="i-lucide-party-popper" class="w-10 h-10 text-green-500" />
            </div>
            <h3 class="text-xl font-bold text-default mb-2">You're all done!</h3>
            <p class="text-sm text-muted leading-relaxed">
              Awesome work — you've completed every workflow. Keep exploring pix:e and make the most
              of your project.
            </p>
            <div class="mt-6 flex items-center gap-2 text-xs text-muted">
              <UIcon name="i-lucide-check-circle" class="w-4 h-4 text-green-500" />
              <span>All {{ availableWorkflows.length }} workflows complete</span>
            </div>
          </div>

          <!-- NORMAL workflow view -->
          <div v-else class="space-y-4">
            <div>
              <h3 class="text-lg font-semibold">{{ activeWorkflowTitle }}</h3>
              <p v-if="activeWorkflowDescription" class="text-sm text-muted mt-1">
                {{ activeWorkflowDescription }}
              </p>
            </div>

            <!-- Overall Progress -->
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
                        :variant="w.id === viewedWorkflowId ? 'soft' : 'ghost'"
                        size="sm"
                        block
                        class="justify-between"
                        @click="viewWorkflow(w.id)"
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
