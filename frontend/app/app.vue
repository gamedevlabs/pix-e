<script setup lang="ts">
import type { NavigationMenuItem } from '@nuxt/ui'

const authentication = useAuthentication()
await authentication.checkAuthentication()

const llmStore = useLLM()

const items = ref<NavigationMenuItem[]>([
  {
    label: 'Dashboard',
    icon: 'i-lucide-book-open',
    to: '/',
  },
  {
    label: 'Player Experience',
    icon: 'i-lucide-brain-cog',
    to: '/player-experience',
    children: [
      {
        label: 'Charts',
        icon: 'i-lucide-chart-network',
        to: '/pxcharts',
      },
      {
        label: 'Nodes',
        icon: 'i-lucide-hexagon',
        to: '/pxnodes',
      },
      {
        label: 'Components',
        icon: 'i-lucide-component',
        to: '/pxcomponents',
      },
      {
        label: 'Component Definitions',
        icon: 'i-lucide-library-big',
        to: '/pxcomponentdefinitions',
      },
    ],
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
  {
    label: 'Movie Script Evaluator',
    icon: 'i-lucide-film',
    to: '/movie-script-evaluator',
  },
])

const dropdownItems = ref([
  [
    {
      label: authentication.user.value?.username,
      icon: 'i-lucide-user',
      type: 'label',
    },
  ],
  [
    {
      label: 'Logout',
      icon: 'i-lucide-log-out',
      async onSelect() {
        await handleLogout()
      },
    },
  ],
])

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
      <UHeader class="px-0" :ui="{ container: 'sm:px-2 lg:px-4' }">
        <template #left>
          <UButton
            :icon="isSidebarCollapsed ? 'i-lucide-panel-right' : 'i-lucide-panel-left'"
            color="neutral"
            variant="ghost"
            aria-label="Toggle Sidebar"
            class="mr-2"
            @click="toggleSidebar"
          />
          <NuxtImg src="/favicon.png" alt="Logo" class="h-10 w-auto mr-2 object-contain" />
          <h1 class="text-xl font-bold">pix:e</h1>
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

      <!-- Main Content Area -->
      <UMain class="flex flex-1 overflow-hidden">
        <!-- Sidebar -->
        <UNavigationMenu
          tooltip
          popover
          :collapsed="isSidebarCollapsed"
          orientation="vertical"
          :items="items"
          class="border-r border-gray-200 dark:border-gray-800 overflow-y-auto flex flex-col items-stretch"
        />

        <!-- Page Content -->
        <UMain
          :class="{
            'p-10': !isSidebarCollapsed, // Add padding only when not collapsed
            'p-4': isSidebarCollapsed, // Smaller padding when collapsed
          }"
          class="flex-1 overflow-y-auto transition-all duration-300 ease-in-out"
        >
          <NuxtPage />
        </UMain>
      </UMain>
    </div>
  </UApp>
</template>

<style scoped>
.page-enter-active,
.page-leave-active {
  transition: all 0.2s;
}

.page-enter-from,
.page-leave-to {
  opacity: 0;
  filter: blur(1rem);
}
</style>
