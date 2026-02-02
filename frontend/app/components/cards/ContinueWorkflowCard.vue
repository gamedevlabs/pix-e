<script setup lang="ts">
import { computed, onMounted } from 'vue'

// TODO: Connect to database - currently using mock data from ProjectApiEmulator
const projectWorkflow = useProjectWorkflow()
const { currentProjectId, projects } = useProjectHandler()
const authentication = useAuthentication()

const isLoggedIn = computed(() => authentication.isLoggedIn.value)

// Get the most recently updated project (first project when sorted by updated_at)
const mostRecentProject = computed(() => {
  if (!projects.value || projects.value.length === 0) return null
  return [...projects.value].sort((a, b) => {
    return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
  })[0]
})

// Use either the selected project or the most recent one
const activeProjectId = computed(
  () => currentProjectId.value || mostRecentProject.value?.id || null,
)

const hasWorkflow = computed(() => projectWorkflow.workflow.value !== null)

// Load workflow on mount if user is logged in and has a project
onMounted(async () => {
  if (isLoggedIn.value && activeProjectId.value) {
    await projectWorkflow.loadForProject(activeProjectId.value)
  }
})

const isEmpty = computed(() => !hasWorkflow.value || !activeProjectId.value)

const projectName = computed(() => {
  if (mostRecentProject.value) {
    return mostRecentProject.value.name
  }
  return 'No Project'
})

// Get the current active substep (or the first incomplete one)
const currentSubstep = computed(() => {
  const step = projectWorkflow.getCurrentStep.value
  if (!step || !step.substeps || step.substeps.length === 0) return null

  // Find the first active substep
  const activeSubstep = step.substeps.find((ss) => ss.status === 'active')
  if (activeSubstep) return activeSubstep

  // If no active substep, find the first incomplete one
  const incompleteSubstep = step.substeps.find((ss) => ss.status === 'pending')
  if (incompleteSubstep) return incompleteSubstep

  // Otherwise return the first substep
  return step.substeps[0] || null
})

// Get display name for current step/substep
const currentStepDisplayName = computed(() => {
  const substep = currentSubstep.value
  const step = projectWorkflow.getCurrentStep.value
  if (substep) {
    return substep.name
  }
  return step?.name || 'No active step'
})

const progressPercent = computed(() => {
  return projectWorkflow.getCurrentStepProgress.value || 0
})

const overallProgress = computed(() => {
  return projectWorkflow.getProgress.value || 0
})

const currentStepIndex = computed(() => {
  return (projectWorkflow.workflow.value?.currentStepIndex ?? 0) + 1
})

const totalSteps = computed(() => {
  return projectWorkflow.workflow.value?.steps.length ?? 0
})

function openProject() {
  // Navigate to the current active substep's route, or fall back to the step's route
  const substep = currentSubstep.value
  const step = projectWorkflow.getCurrentStep.value

  let targetRoute = null

  if (substep?.route) {
    targetRoute = substep.route
  } else if (step?.route) {
    targetRoute = step.route
  }

  if (targetRoute && activeProjectId.value) {
    // Include project ID in the route
    navigateTo(`${targetRoute}?id=${activeProjectId.value}`)
  } else if (activeProjectId.value) {
    navigateTo(`/dashboard?id=${activeProjectId.value}`)
  } else {
    navigateTo('/dashboard')
  }
}
</script>

<template>
  <DashboardCard
    title="Continue where you left off"
    icon="i-lucide-play-circle"
    :login-required="true"
  >
    <div v-if="!isEmpty" class="space-y-4">
      <!-- Project Info -->
      <div class="space-y-2">
        <div class="font-semibold text-base text-gray-900 dark:text-gray-100">
          {{ projectName }}
        </div>
        <div class="space-y-1">
          <div class="text-xs text-gray-500 dark:text-gray-400">Current task</div>
          <div class="font-medium text-sm text-gray-900 dark:text-gray-100">
            {{ currentStepDisplayName }}
          </div>
        </div>

        <!-- Progress Bar -->
        <div class="space-y-1">
          <div class="h-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              class="h-full bg-primary-500 transition-all duration-300 ease-out"
              :style="{ width: progressPercent + '%' }"
            />
          </div>
          <div class="text-xs text-gray-500 dark:text-gray-400">
            Step {{ currentStepIndex }} / {{ totalSteps }} · {{ overallProgress }}% overall
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex gap-2 pt-2">
        <UButton
          label="Continue"
          icon="i-lucide-arrow-right"
          color="primary"
          size="sm"
          @click="openProject"
        />
      </div>
    </div>

    <!-- Empty state when no workflow found -->
    <div v-else class="text-center py-6 space-y-3">
      <div class="text-sm text-gray-500 dark:text-gray-400">No active workflow found</div>
    </div>
  </DashboardCard>
</template>
