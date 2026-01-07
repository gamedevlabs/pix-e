<script setup lang="ts">
import type { DropdownMenuItem } from '@nuxt/ui'
import { useProjectHandler } from '~/composables/useProjectHandler'

defineProps<{
  collapsed?: boolean
}>()

// use the project's composable
const { projects, currentProject, switchProject, unselectProject } = useProjectHandler()

// selected team/item derived from the currentProject state
const selectedTeam = computed(() => {
  const p = currentProject.value ?? projects.value[0]
  if (!p) {
    // safe fallback to avoid spreading undefined into v-bind
    return {
      label: 'No project',
      avatar: {
        src: `https://ui-avatars.com/api/?name=Project&background=random`,
        alt: 'No project',
      },
    }
  }

  return {
    label: p.name,
    avatar: {
      // fallback avatar generator based on project name
      src: `https://ui-avatars.com/api/?name=${encodeURIComponent(p.name)}&background=random`,
      alt: p.name,
    },
  }
})

const items = computed<DropdownMenuItem[][]>(() => {
  return [
    projects.value.map((proj) => ({
      label: proj.name,
      avatar: {
        src: `https://ui-avatars.com/api/?name=${encodeURIComponent(proj.name)}&background=random`,
        alt: proj.name,
      },
      onSelect() {
        // switch project and navigate to its dashboard (don't prevent default so menu can close)
        void switchProject(proj.id)
      },
    })),
    [
      {
        label: 'New Project',
        icon: 'i-lucide-circle-plus',
      },
      {
        label: 'Manage projects',
        icon: 'i-lucide-cog',
        onSelect() {
          // unselect any project and go to landing/overview page
          unselectProject()
          void navigateTo('/')
        },
      },
    ],
  ]
})
</script>

<template>
  <UDropdownMenu
    :items="items"
    :content="{ align: 'center', collisionPadding: 12 }"
    :ui="{ content: collapsed ? 'w-40' : 'w-(--reka-dropdown-menu-trigger-width)' }"
  >
    <UButton
      v-bind="{
        ...selectedTeam,
        label: collapsed ? undefined : selectedTeam?.label,
        trailingIcon: collapsed ? undefined : 'i-lucide-chevrons-up-down',
      }"
      color="neutral"
      variant="ghost"
      block
      :square="collapsed"
      class="data-[state=open]:bg-elevated"
      :class="[!collapsed && 'py-2']"
      :ui="{
        trailingIcon: 'text-dimmed',
      }"
    />
  </UDropdownMenu>
</template>
