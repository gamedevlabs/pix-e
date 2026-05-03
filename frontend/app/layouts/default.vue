<script setup lang="ts">
import AppHeader from '~/components/layout/AppHeader.vue'
import AppSidebar from '~/components/layout/AppSidebar.vue'
import type { WorkflowInstance } from '~/mock_data/mock_workflow'

const searchOpen = ref(false)

const { syncProjectFromUrl } = useProjectHandler()
syncProjectFromUrl()

const { showSidebar } = useSidebarVisibility()
const { links, openNavValue, groups } = useNavigationLinks()
useOnboardingProgress(searchOpen)

// Workflow title + progress for the sidebar's onboarding button.
const projectWorkflow = useProjectWorkflow()
const overallProgress = computed(() => projectWorkflow.getSelectedWorkflowProgress.value || 0)
const activeWorkflowTitle = computed(() => {
  const list = (projectWorkflow.workflows?.value || []) as WorkflowInstance[]
  const selectedId =
    projectWorkflow.viewedWorkflowId?.value ?? projectWorkflow.activeWorkflowId?.value
  const w = list.find((x) => x.id === selectedId)
  return w?.meta?.title || 'Onboarding Wizard'
})
</script>

<template>
  <div id="app" class="h-screen flex flex-col">
    <AppHeader />

    <main class="flex-1 min-h-0">
      <!-- No sidebar: page fills the main area -->
      <div v-if="!showSidebar" class="h-full min-h-0 p-8 overflow-auto">
        <slot />
      </div>

      <!-- With sidebar -->
      <div v-else class="h-full min-h-0 overflow-hidden">
        <UDashboardGroup class="h-full">
          <AppSidebar
            v-model:open-nav-value="openNavValue"
            :links="links"
            :workflow-title="activeWorkflowTitle"
            :workflow-progress="overallProgress"
          />

          <UDashboardSearch v-model:open="searchOpen" :groups="groups" />

          <div class="flex-1 min-h-0 overflow-hidden">
            <UDashboardPanel class="h-full relative">
              <div class="h-full min-h-0 overflow-auto p-6">
                <slot />
              </div>
            </UDashboardPanel>
          </div>
        </UDashboardGroup>
      </div>
    </main>

    <UFooter />
  </div>
</template>

<style>
html,
body,
#app {
  height: 100%;
  margin: 0;
}
</style>
