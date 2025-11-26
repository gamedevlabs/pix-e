<script setup lang="ts">
import type { NavigationMenuItem } from '@nuxt/ui'
import { computed, ref } from 'vue'

const authentication = useAuthentication()
await authentication.checkAuthentication()

const llmStore = useLLM()

// Currently only MOCK DATA until backend is ready
const selectedProjectTitle = 'Demo Project'

// completely hide the sidebar, when on /projects-overview page
const route = useRoute()
const showSidebar = computed(() => route.path !== '/projects-overview')

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
        <div v-if="showSidebar" class="border-r border-gray-200 dark:border-gray-800 overflow-y-auto flex flex-col items-stretch" :class="{ 'w-12': isSidebarCollapsed, 'w-64': !isSidebarCollapsed }">
          <!-- Button that brings you to /projects-overview -->
          <div :class="isSidebarCollapsed ? 'px-0 py-2' : 'px-3 py-2'">
            <!-- Expanded: full-width buttons; Collapsed: tiny inline icon-link -->
            <div v-if="!isSidebarCollapsed">
              <NuxtLink to="/projects-overview" title="All Projects">
                <UButton
                  icon="i-lucide-arrow-left"
                  label="All Projects"
                  color="neutral"
                  variant="ghost"
                  class="w-full justify-start text-sm font-medium text-gray-800 dark:text-white"
                />
              </NuxtLink>
            </div>
            <div v-else class="flex justify-center">
              <!-- small inline link for /projects-overview -->
              <NuxtLink to="/projects-overview" class="inline-flex items-center justify-center h-8 w-8" title="All Projects" aria-label="All Projects">
                <UIcon name="i-lucide-arrow-left" class="text-base" />
              </NuxtLink>
            </div>
          </div>

          <!-- divider between back button and project buttons -->
          <div class="w-full" style="border-top:1px solid rgba(156,163,175,0.25)"></div>

           <!-- current selected project title -->
          <div :class="isSidebarCollapsed ? 'px-0 py-2' : 'px-4 py-2'">
            <div class="text-xs text-gray-500" v-if="!isSidebarCollapsed">Selected Project</div>
            <div v-if="isSidebarCollapsed" class="flex items-center justify-center">
              <div class="h-5 w-5 rounded-full bg-gray-300 dark:bg-gray-700 flex items-center justify-center">
                <span class="text-xs font-semibold text-gray-900 dark:text-white">{{ selectedProjectTitle.charAt(0) }}</span>
              </div>
            </div>
            <div v-else class="text-sm font-medium truncate">{{ selectedProjectTitle }}</div>
          </div>

           <!-- module Buttons -->
           <div class="flex-1 py-2" :class="{ 'px-2': !isSidebarCollapsed }">
             <div :class="{ 'flex justify-center': isSidebarCollapsed }">
               <UNavigationMenu
                 tooltip
                 popover
                 :collapsed="isSidebarCollapsed"
                 orientation="vertical"
                 :items="items"
                 class="h-full"
               />
             </div>
           </div>
         </div>

         <!-- Floating collapse/expand toggle (fixed bottom-left, aligned to sidebar width) -->
         <div v-if="showSidebar" style="left:12px;" class="fixed bottom-6 z-40">
           <UButton
             :icon="isSidebarCollapsed ? 'i-lucide-panel-right' : 'i-lucide-panel-left'"
             color="neutral"
             variant="ghost"
             aria-label="Toggle Sidebar"
             @click="toggleSidebar"
           />
         </div>

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
