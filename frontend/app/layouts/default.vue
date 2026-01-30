<script setup lang="ts">
import type { NavigationMenuItem } from '@nuxt/ui'
import { computed, ref } from 'vue'
import type { PageConfig } from '~/types/page-config'

// ROUTING
const route = useRoute()
const router = useRouter()

const open = ref(false)

// AUTH
const authentication = useAuthentication()

// HEADER
const llmStore = useLLM()

// PROJECT
const { currentProjectId, syncProjectFromUrl } = useProjectHandler()
syncProjectFromUrl()
const projectQuery = computed(() => (currentProjectId.value ? `?id=${currentProjectId.value}` : ''))

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

// Handles sidebar visibility
const showSidebar = computed(() => {
  // Check if page has custom config
  const pageConfig = route.meta.pageConfig as PageConfig | undefined

  // If page explicitly sets showSidebar, use that
  if (pageConfig?.showSidebar !== undefined) {
    return pageConfig.showSidebar
  }

  // Otherwise, determine based on page type
  if (pageConfig?.type === 'public') {
    return false
  }

  if (pageConfig?.type === 'standalone') {
    return false
  }

  if (pageConfig?.type === 'project-required') {
    // For project-required pages, show sidebar if user is logged in and has a project
    const hasCurrentProject = !!currentProjectId.value || !!route.query?.id
    return authentication.isLoggedIn.value && hasCurrentProject
  }

  // Fallback to old logic for pages without config (backwards compatibility)
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

// Dynamically build navigation from page metadata
const links = computed<NavigationMenuItem[][]>(() => {
  const routes = router.getRoutes()

  // Filter routes that should appear in navigation
  const navRoutes = routes.filter((route) => {
    const pageConfig = route.meta.pageConfig as PageConfig | undefined
    return pageConfig?.showInNav !== false && pageConfig?.title && pageConfig?.icon
  })

  // Sort by navOrder
  const sortedRoutes = navRoutes.sort((a, b) => {
    const aConfig = a.meta.pageConfig as PageConfig
    const bConfig = b.meta.pageConfig as PageConfig
    return (aConfig.navOrder || 999) - (bConfig.navOrder || 999)
  })

  // Group routes by parent
  const routesByParent = new Map<string, typeof sortedRoutes>()
  const topLevelRoutes: typeof sortedRoutes = []

  sortedRoutes.forEach((route) => {
    const pageConfig = route.meta.pageConfig as PageConfig
    if (pageConfig.navParent) {
      const existing = routesByParent.get(pageConfig.navParent) || []
      routesByParent.set(pageConfig.navParent, [...existing, route])
    } else {
      topLevelRoutes.push(route)
    }
  })

  // Build navigation items
  const navItems: NavigationMenuItem[] = topLevelRoutes.map((route) => {
    const pageConfig = route.meta.pageConfig as PageConfig
    const routePath = route.path

    // Check if this route has children
    const childRoutes = routesByParent.get(routePath.replace(/^\//, ''))

    // Determine if route needs project query
    const needsProjectQuery = pageConfig.type === 'project-required'
    const to = needsProjectQuery ? `${routePath}${projectQuery.value}` : routePath

    const navItem: NavigationMenuItem = {
      label: pageConfig.title!,
      icon: pageConfig.icon!,
      to,
    }

    // Add children if they exist
    if (childRoutes && childRoutes.length > 0) {
      navItem.children = childRoutes.map((childRoute) => {
        const childConfig = childRoute.meta.pageConfig as PageConfig
        const childNeedsProjectQuery = childConfig.type === 'project-required'
        const childTo = childNeedsProjectQuery
          ? `${childRoute.path}${projectQuery.value}`
          : childRoute.path

        return {
          label: childConfig.title!,
          icon: childConfig.icon!,
          to: childTo,
        }
      })
    }

    return navItem
  })

  // External links section
  const externalLinks: NavigationMenuItem[] = [
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
  ]

  return [navItems, externalLinks]
})

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
              <UDashboardSearchButton
                :collapsed="collapsed"
                class="w-full bg-transparent ring-default"
              />
            </template>

            <template #default="{ collapsed }">
              <div class="flex flex-col h-full relative">
                <USeparator class="my-2" />
                <div class="bg-gray-100 dark:bg-gray-800/50 rounded-lg p-2 mx-2 mb-2">
                  <ProjectSelector :collapsed="collapsed" />
                </div>

                <UNavigationMenu
                  :collapsed="collapsed"
                  :items="links[0]"
                  orientation="vertical"
                  tooltip
                  popover
                />

                <div class="mt-auto w-full flex flex-col items-start px-2">
                  <!-- Workflow Slideover Component -->
                  <WorkflowSlideover :collapsed="collapsed" />

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
