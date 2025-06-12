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
</script>

<template>
  <UApp>
    <div class="min-h-screen flex flex-col">
      <!-- Topbar -->
      <header
        class="h-16 border-b border-gray-200 dark:border-gray-800 px-6 flex items-center justify-between"
      >
        <div class="flex items-center">
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
          class="w-64 border-r border-gray-200 dark:border-gray-800 p-4 overflow-y-auto flex flex-col items-stretch"
        >
          <UNavigationMenu orientation="vertical" :items="items" />
        </aside>

        <!-- Page Content -->
        <main class="flex-1 p-10 overflow-y-auto">
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
