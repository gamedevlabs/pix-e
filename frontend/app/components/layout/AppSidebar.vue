<script setup lang="ts">
import type { NavigationMenuItem } from '@nuxt/ui'
import OnboardingSlideOverButton from '~/components/OnboardingSlideOverButton.vue'

defineProps<{
  links: NavigationMenuItem[][]
  workflowTitle: string
  workflowProgress: number
}>()

const openNavValue = defineModel<string | undefined>('openNavValue')

// Sidebar collapse state — local to this component.
const open = ref(false)
</script>

<template>
  <UDashboardSidebar
    id="selected_project"
    v-model:open="open"
    collapsible
    resizable
    class="bg-elevated/25 relative"
    :ui="{ footer: 'lg:border-t lg:border-default' }"
  >
    <template #header="{ collapsed }">
      <!-- Minimal header to avoid overlap with body padding/scroll area -->
      <div class="w-full flex items-center">
        <UIcon
          v-if="collapsed"
          name="i-lucide-panels-left-bottom"
          class="size-5 text-primary mx-auto"
        />
      </div>
    </template>

    <template #default="{ collapsed }">
      <div class="flex flex-col h-full">
        <!-- Project picker + search button -->
        <div class="pt-2 flex flex-col gap-3">
          <ProjectSelector :collapsed="collapsed" variant="brand" />

          <UDashboardSearchButton
            :collapsed="collapsed"
            class="w-full bg-transparent ring-default"
          />
        </div>

        <!-- Main module navigation -->
        <UNavigationMenu
          v-model="openNavValue"
          :collapsed="collapsed"
          :items="links[0]"
          orientation="vertical"
          type="single"
          :collapsible="true"
          tooltip
          popover
          class="mt-3"
        />

        <USeparator
          :label="collapsed ? undefined : 'Standalone Tools'"
          class="my-3"
          :ui="{ label: 'text-xs text-gray-400 dark:text-gray-500 px-2' }"
        />

        <!-- Standalone tools -->
        <UNavigationMenu
          :collapsed="collapsed"
          :items="links[1]"
          orientation="vertical"
          tooltip
          popover
        />

        <!-- Footer: onboarding trigger + external links -->
        <div class="mt-auto w-full flex flex-col items-start">
          <OnboardingSlideOverButton
            :collapsed="collapsed"
            :title="workflowTitle"
            :progress="workflowProgress"
          />
          <OnboardingSlideover :collapsed="collapsed" />

          <UNavigationMenu
            :collapsed="collapsed"
            :items="links[2]"
            orientation="vertical"
            tooltip
            class="w-full"
          />
        </div>
      </div>
    </template>
  </UDashboardSidebar>
</template>
