<script setup lang="ts">
import type { NavigationMenuItem } from '@nuxt/ui'
import OnboardingTrigger from '~/components/onboarding/OnboardingTrigger.vue'

defineProps<{
  links: NavigationMenuItem[][]
}>()

const openNavValue = defineModel<string | undefined>('openNavValue')

// Sidebar collapse state — local to this component.
const open = ref(false)
const sidebarCollapsed = ref(false)

async function handleToggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

defineShortcuts({
  s: () => {
    handleToggleSidebar()
  },
})
</script>

<template>
  <UDashboardSidebar
    id="selected_project"
    v-model:open="open"
    v-model:collapsed="sidebarCollapsed"
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
        <!--
        <USeparator
          :label="collapsed ? undefined : 'Standalone Tools'"
          class="my-3"
          :ui="{ label: 'text-xs text-gray-400 dark:text-gray-500 px-2' }"
        />
        -->

        <!-- Standalone tools -->
        <UNavigationMenu
          :collapsed="collapsed"
          :items="links[1]"
          orientation="vertical"
          tooltip
          popover
        />

        <!-- Footer: onboarding trigger + hide sidebar + external links -->
        <div class="mt-auto w-full flex flex-col items-start">
          <!--
          <OnboardingTrigger mode="sidebar" :collapsed="collapsed" />
          -->

          <div v-if="!collapsed" class="mt-auto w-full min-w-0 flex flex-col items-start">
            <UTooltip text="Hide sidebar (S)">
              <UButton
                :block="true"
                style="justify-content: left"
                color="neutral"
                variant="outline"
                size="md"
                icon="heroicons:chevron-double-left-16-solid"
                @click="handleToggleSidebar()"
              >
                <span class="truncate"> Hide Sidebar </span>
              </UButton>
            </UTooltip>
          </div>
          <div v-else class="mt-auto w-full flex flex-col items-start text-truncate">
            <UTooltip text="Show sidebar (S)">
              <UButton
                :block="true"
                :square="true"
                color="neutral"
                variant="outline"
                size="lg"
                icon="heroicons:chevron-double-right-16-solid"
                @click="handleToggleSidebar()"
              />
            </UTooltip>
          </div>

          <USeparator class="my-3" />

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
