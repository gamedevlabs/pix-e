<script setup lang="ts">
import type { NavigationMenuItem } from '@nuxt/ui'
import { computed, ref } from 'vue'

// ROUTING
const route = useRoute()

const open = ref(false)

// AUTH
const authentication = useAuthentication()

// HEADER
const llmStore = useLLM()

const dropdownItems = computed(() => [
  [
    {
      label: authentication.user.value?.username || 'User',
      icon: 'i-lucide-user',
      type: 'label',
    },
  ],
  [
    {
      label: 'Logout',
      icon: 'i-lucide-log-out',
      click: async () => {
        await authentication.logout()
      },
    },
  ],
])

// PROJECT
const { currentProjectId } = useCurrentProject()
const projectQuery = currentProjectId.value ? `?id=${currentProjectId.value}` : ''

// For dev testing: compute whether a project is selected from the URL.
// isProjectSelected should be false for the landing page (path == '/') and
// true for any other path like '/dashboard'. This replaces the boolean
// previously provided by useCurrentProject().
const isProjectSelected = computed(() => {
  const path = route?.path ?? ''
  return !(path === '/' || path === '')
})

const links = [
  [
    {
      label: 'Dashboard',
      icon: 'i-lucide-house',
      to: `/dashboard${projectQuery}`,
    },
    {
      label: 'Charts',
      icon: 'i-lucide-network',
      defaultOpen: true,
      children: [
        { label: 'PxCharts', to: `/pxcharts${projectQuery}` },
        { label: 'PxNodes', to: `/pxnodes${projectQuery}` },
        { label: 'PxComponents', to: `/pxcomponents${projectQuery}` },
        { label: 'PxComponentsDefinitions', to: `/pxcomponentdefinitions${projectQuery}` },
      ],
    },
    {
      label: 'Player Expectations',
      icon: 'i-lucide-book-open',
      defaultOpen: true,
      children: [
        { label: 'Dashboard', to: `/player-expectations${projectQuery}` },
        { label: 'Sentiment Analysis', to: `/sentiments${projectQuery}` },
      ],
    },
    { label: 'Pillars', icon: 'i-lucide-landmark', to: `/pillars${projectQuery}` },
    { label: 'Movie Script Evaluator', icon: 'i-lucide-film', to: '/movie-script-evaluator' },
  ],
  [
    {
      label: 'Wiki',
      icon: 'i-lucide-book-text',
      to: 'https://github.com/gamedevlabs/pix-e/wiki',
      target: '_blank',
    },
  ],
] satisfies NavigationMenuItem[][]

const groups = computed(() => [
  {
    id: 'links',
    label: 'Go to',
    items: links.flat(),
  },
])
</script>

<template>
  <!-- App root: full viewport height and column layout so header + content behave predictably -->
  <div id="app" class="h-screen flex flex-col">
    <UHeader class="px-0" :ui="{ container: 'sm:px-2 lg:px-4' }">
      <template #left>
        <NuxtLink to="/" class="flex items-center gap-2 no-underline" aria-label="Home">
          <NuxtImg src="/favicon.png" alt="Logo" class="h-10 w-auto object-contain" />
          <h1 class="text-xl font-bold">pix:e</h1>
        </NuxtLink>
      </template>

      <template #right>
        <UColorModeSwitch />

        <UButton
          v-if="!authentication.isLoggedIn.value"
          label="Login"
          color="primary"
          variant="subtle"
          @click="useRouter().push('login')"
        />
        <div v-else class="flex items-center gap-2">
          <!-- Put user info, settings, logout etc. here -->
          <USelect
            v-model="llmStore.active_llm"
            :items="llmStore.llm_models"
            value-key="value"
            :icon="llmStore.llm_icon"
            class="w-48"
          />
          <UDropdownMenu :items="dropdownItems">
            <!-- we need to wrap it in a div so the whole component is clickable -->
            <div>
              <UAvatar avatar="i-lucide-user" :alt="authentication.user.value?.username" />
            </div>
          </UDropdownMenu>
        </div>
      </template>
    </UHeader>

    <!-- Main content: take remaining height. Pages should not need to handle sizing --- it's done here -->
    <main class="flex-1 min-h-0">
      <!--  PROJECT OVERVIEW: make this area take remaining space and be scrollable -->
      <div v-if="!isProjectSelected" class="h-full min-h-0 p-8 overflow-auto">
        <slot />
      </div>

      <!--PROJECT SELECTED-->
      <div v-else class="h-full min-h-0 overflow-hidden">
        <UDashboardGroup class="h-full">
          <UDashboardSidebar
            id="selected_project"
            v-model:open="open"
            collapsible
            resizable
            class="bg-elevated/25 relative"
            :ui="{ footer: 'lg:border-t lg:border-default' }"
            style="margin-top: 52px"
          >
            <template #header="{ collapsed }">
              <ProjectSelector :collapsed="collapsed" />
            </template>

            <template #default="{ collapsed }">
              <!-- Make the sidebar content a full-height column so mt-auto pushes footer to the bottom of the sidebar viewport.
                   Add bottom padding so the footer (and the collapsed button) don't overlap or get clipped by the scrolling area. -->
              <div class="flex flex-col h-full relative pb-16">
                <UDashboardSearchButton
                  :collapsed="collapsed"
                  class="bg-transparent ring-default"
                />

                <UNavigationMenu
                  :collapsed="collapsed"
                  :items="links[0]"
                  orientation="vertical"
                  tooltip
                  popover
                />

                <!-- Bottom area: Wiki link. mt-auto ensures this area sits at the bottom of the sidebar -->
                <div class="mt-auto w-full flex flex-col items-start px-2 pb-6">
                  <UNavigationMenu
                    :collapsed="collapsed"
                    :items="links[1]"
                    orientation="vertical"
                    tooltip
                    class="w-full"
                  />
                </div>
              </div>
            </template>

            <template #footer="{ collapsed }">
              <!-- Footer in normal flow; include the collapsed-state button here so it's part of the sidebar and won't fall outside the sidebar viewport. -->
              <div>
                <UserMenu :collapsed="collapsed" />
              </div>
            </template>
          </UDashboardSidebar>

          <UDashboardSearch :groups="groups" />

          <!-- Panel wrapper: leave top margin to account for header; make this area fill vertical space and contain a scrollable slot -->
          <div class="flex-1 min-h-0 overflow-hidden" style="margin-top: 52px">
            <UDashboardPanel class="h-full relative">
              <!-- Full-height scrollable content for any page that renders inside the dashboard -->
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
