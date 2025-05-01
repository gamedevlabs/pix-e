<script setup lang="ts">
import type { NavigationMenuItem } from '@nuxt/ui'

const items = ref<NavigationMenuItem[]>([
  {
    label: 'Dashboard',
    icon: 'i-lucide-book-open',
    to: '/',
  },
  {
    label: 'About',
    icon: 'i-lucide-database',
    to: '/about',
  },
  {
    label: 'PXNodes',
    icon: 'i-lucide-database',
    to: '/pxnodes',
  },
  {
    label: 'Pillars',
    icon: 'i-lucide-database',
    to: '/pillars',
  },
  {
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
  },
])
useAnonCookie()
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
        <div class="flex items-center">
          <!-- Put user info, settings, logout etc. here -->
          <ColorModeSwitch class="mx-8" />
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
        <main class="flex-1 p-6 overflow-y-auto">
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
