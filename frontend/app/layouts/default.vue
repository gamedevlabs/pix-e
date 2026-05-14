<script setup lang="ts">
import AppHeader from '~/components/layout/AppHeader.vue'
import AppSidebar from '~/components/layout/AppSidebar.vue'

const searchOpen = ref(false)

const { syncProjectFromUrl } = useProjectHandler()
syncProjectFromUrl()

const { showSidebar } = useSidebarVisibility()
const { links, openNavValue, groups } = useNavigationLinks()
useOnboardingProgress(searchOpen)
</script>

<template>
  <div id="app" class="h-screen flex flex-col">
    <AppHeader />

    <main class="flex-1 min-h-0">
      <!-- No sidebar: page fills the main area -->
      <!-- pt-16 leaves space for the sticky UHeader so the page isn't covered. -->
      <div v-if="!showSidebar" class="h-full min-h-0 px-8 pt-16 pb-8 overflow-auto">
        <slot />
      </div>

      <!-- With sidebar -->
      <div v-else class="h-full min-h-0 overflow-hidden">
        <UDashboardGroup class="h-full">
          <AppSidebar v-model:open-nav-value="openNavValue" :links="links" />

          <UDashboardSearch v-model:open="searchOpen" :groups="groups" />

          <div class="flex-1 min-h-0 overflow-hidden">
            <UDashboardPanel class="h-full relative">
              <!-- pt-16 leaves space for the sticky UHeader so the page isn't covered. -->
              <div class="h-full min-h-0 overflow-auto px-6 pt-16 pb-6">
                <slot />
              </div>
            </UDashboardPanel>
          </div>
        </UDashboardGroup>
      </div>
    </main>

    <UFooter />
    <SessionPasswordModal />
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
