<script setup lang="ts">
import type { NavigationMenuItem } from '@nuxt/ui'

const items = ref<NavigationMenuItem[]>([
  {
    label: 'Dashboard',
    icon: 'i-lucide-book-open',
    to: '/',
  },
  {
    label: 'PxNodes',
    icon: 'i-lucide-hexagon',
    to: '/pxnodes',
  },
  {
    label: 'PxComponents',
    icon: 'i-lucide-component',
    to: '/pxcomponents',
  },
  {
    label: 'PxComponentsDefinitions',
    icon: 'i-lucide-library-big',
    to: '/pxcomponentdefinitions',
  },
  {
    label: 'PxCharts',
    icon: 'i-lucide-chart-network',
    to: '/pxcharts',
  },
  {
    label: 'Player Expectations',
    icon: 'i-lucide-book-open',
    to: '/player-expectations',
    children: [
      {
        label: 'Dashboard',
        icon: 'i-lucide-book-open',
        to: '/player-expectations',
      },
      {
        label: 'Sentiment Analysis',
        icon: 'i-lucide-library-big',
        to: '/sentiments',
      },
    ],
  },
  {
    label: 'Pillars',
    icon: 'i-lucide-landmark',
    to: '/pillars',
  },
  /*{
    label: 'GitHub',
    icon: 'i-simple-icons-github',
    badge: '3.8k',
    to: 'https://github.com/nuxt/ui',
    target: '_blank',
  },
  {
    label: 'Help',
    icon: 'i-lucide-circle-help',
    disabled: true,
  },*/
])
const authentication = useAuthentication()
authentication.checkAuthentication()

const llmstore = useLLM()

async function handleLogout() {
  await authentication.logout()
}

const isSidebarCollapsed = ref(false)

function toggleSidebar() {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
}
</script>

<template>
  <UApp>
    <div class="min-h-screen flex flex-col">
      <!-- Topbar -->
      <header
        class="h-16 border-b border-gray-200 dark:border-gray-800 px-6 flex items-center justify-between"
      >
        <div class="flex items-center">
          <UButton
            :icon="isSidebarCollapsed ? 'i-lucide-panel-right' : 'i-lucide-panel-left'"
            color="gray"
            variant="ghost"
            aria-label="Toggle Sidebar"
            class="mr-3"
            @click="toggleSidebar"
          />
          <NuxtImg src="/favicon.png" alt="Logo" class="h-10 w-auto mr-2 object-contain" />
          <h1 class="text-xl font-bold">pix:e</h1>
        </div>
        <div class="flex items-center gap-3">
          <!-- Put user info, settings, logout etc. here -->
          <USelect
            v-model="llmstore.active_llm"
            :items="llmstore.llm_models"
            value-key="value"
            :icon="llmstore.llm_icon"
            class="w-48"
          />
          <ColorModeSwitch />
          <UButton
            v-if="!authentication.isLoggedIn.value"
            label="Login"
            color="primary"
            variant="subtle"
            @click="useRouter().push('login')"
          />
          <div v-else class="flex items-center gap-2">
            <p>Hello {{ authentication.user.value?.username }}</p>
            <UButton label="Logout" color="error" variant="subtle" @click="handleLogout" />
          </div>
          <UAvatar src="https://i.pravatar.cc/40" alt="User" />
        </div>
      </header>

      <!-- Main Content Area -->
      <div class="flex flex-1 overflow-hidden">
        <!-- Sidebar -->
        <aside
          :class="{
            'w-16': isSidebarCollapsed,
            'w-64': !isSidebarCollapsed,
            'p-4': !isSidebarCollapsed, // Add padding only when not collapsed
            'px-2': isSidebarCollapsed, // Smaller horizontal padding when collapsed
            'overflow-hidden': isSidebarCollapsed, // Hide overflow when collapsed
          }"
          class="border-r border-gray-200 dark:border-gray-800 overflow-y-auto flex flex-col items-stretch transition-all duration-300 ease-in-out"
        >
          <UNavigationMenu
            orientation="vertical"
            :items="items"
            :class="{ hidden: isSidebarCollapsed }"
          />
          <div v-if="isSidebarCollapsed" class="flex flex-col items-center mt-4 space-y-2">
            <UButton
              v-for="item in items"
              :key="item.to"
              :icon="item.icon"
              :to="item.to"
              variant="ghost"
              color="gray"
              class="w-full justify-center"
              :aria-label="item.label"
            />
          </div>
        </aside>

        <!-- Page Content -->
        <main
          :class="{
            'p-10': !isSidebarCollapsed, // Add padding only when not collapsed
            'p-4': isSidebarCollapsed, // Smaller padding when collapsed
          }"
          class="flex-1 overflow-y-auto transition-all duration-300 ease-in-out"
        >
          <NuxtPage />
        </main>
      </div>
    </div>
  </UApp>
</template>

<style scoped>
.page-enter-active,
.page-leave-active {
  transition: all 0.4s;
}

.page-enter-from,
.page-leave-to {
  opacity: 0;
  filter: blur(1rem);
}
</style>
