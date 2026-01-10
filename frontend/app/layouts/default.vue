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
      onSelect: async (e: Event | undefined) => {
        e?.preventDefault?.()
        await authentication.logout()
      },
    },
  ],
])

// PROJECT
const { currentProjectId, syncProjectFromUrl } = useProjectHandler()
syncProjectFromUrl()
const projectQuery = computed(() => (currentProjectId.value ? `?id=${currentProjectId.value}` : ''))

// Handles sidebar visibility
const showSidebar = computed(() => {
  const path = route.path || ''
  const name = route.name ? String(route.name) : ''
  const alwaysShowSidebar: string[] = ['dashboard', 'edit']
  const alwaysHideSidebar: string[] = ['login', '/movie-script-evaluator', 'create']

  // Hide the root/index page explicitly and when the route has no name
  if (!name || path === '/') {
    return false
  }

  // If the current route is explicitly hidden, return false
  if (alwaysHideSidebar.some((p) => p && (p === name || path === p || path.startsWith(p)))) {
    return false
  }

  // If the current route is explicitly shown, return true
  if (alwaysShowSidebar.some((p) => p && (p === name || path === p || path.startsWith(p)))) {
    return true
  }

  // Check rules
  const checks = {
    // A project is considered selected if either a currentProjectId exists OR an ?id= query param is present
    hasCurrentProject: !!currentProjectId.value || !!route.query?.id,
    userLoggedIn: authentication.isLoggedIn.value,
  }

  // Combined rules: requires both a selected project and a logged-in user
  return checks.hasCurrentProject && checks.userLoggedIn
})

const links = computed<NavigationMenuItem[][]>(() => [
  [
    {
      label: 'Dashboard',
      icon: 'i-lucide-house',
      to: `/dashboard${projectQuery.value}`,
    },
    {
      label: 'Charts',
      icon: 'i-lucide-network',
      defaultOpen: true,
      children: [
        { label: 'PxCharts', to: `/pxcharts${projectQuery.value}` },
        { label: 'PxNodes', to: `/pxnodes${projectQuery.value}` },
        { label: 'PxComponents', to: `/pxcomponents${projectQuery.value}` },
        { label: 'PxComponentsDefinitions', to: `/pxcomponentdefinitions${projectQuery.value}` },
      ],
    },
    {
      label: 'Player Expectations',
      icon: 'i-lucide-book-open',
      defaultOpen: true,
      children: [
        { label: 'Dashboard', to: `/player-expectations${projectQuery.value}` },
        { label: 'Sentiment Analysis', to: `/sentiments${projectQuery.value}` },
      ],
    },
    { label: 'Pillars', icon: 'i-lucide-landmark', to: `/pillars${projectQuery.value}` },
    { label: 'Movie Script Evaluator', icon: 'i-lucide-film', to: '/movie-script-evaluator' },
    { label: 'Settings', icon: 'i-lucide-settings', to: `/edit${projectQuery.value}` },
  ],
  [
    {
      label: 'Wiki',
      icon: 'i-lucide-book-text',
      to: 'https://github.com/gamedevlabs/pix-e/wiki',
      target: '_blank',
    },
    {
      label: 'Discord',
      icon: 'i-lucide-message-circle',
      to: 'https://discord.gg/7BhM3nTq',
      target: '_blank',
    },
  ],
])

const groups = computed(() => [
  {
    id: 'links',
    label: 'Go to',
    items: links.value.flat(),
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
      <div v-if="!showSidebar" class="h-full min-h-0 p-8 overflow-auto">
        <slot />
      </div>

      <!-- VISIBLE SIDEBAR -->
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
              <!-- Make the sidebar content a full-height column so mt-auto pushes footer to the bottom of the sidebar viewport. -->
              <div class="flex flex-col h-full relative">
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

                <!-- Bottom area: Wiki & Discord links. mt-auto ensures this area sits at the bottom of the sidebar -->
                <div class="mt-auto w-full flex flex-col items-start px-2">
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
