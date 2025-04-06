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
</script>

<template>
  <UApp>
    <div class="min-h-screen flex flex-col">
      <!-- Topbar -->
      <header
        class="h-16 border-b border-gray-200 dark:border-gray-800 px-6 flex items-center justify-between"
      >
        <h1 class="text-xl font-semibold">PIX:E</h1>
        <div>
          <!-- Put user info, settings, logout etc. here -->
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
          <div class="mt-auto flex justify-center">
            <ColorModeSwitch />
          </div>
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
