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
        text: 'P',
        alt: 'No project',
      },
    }
  }

  // Helper function to generate initials from project name
  const getInitials = (name: string) => {
    const parts = name.split(/\s+/).filter(Boolean)
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
    return (parts[0][0] + parts[1][0]).toUpperCase()
  }

  return {
    label: p.name,
    avatar: {
      // Use project icon if available, otherwise show initials
      src: p.icon || undefined,
      text: p.icon ? undefined : getInitials(p.name),
      alt: p.name,
    },
  }
})

const items = computed<DropdownMenuItem[][]>(() => {
  // Helper function to generate initials from project name
  const getInitials = (name: string) => {
    const parts = name.split(/\s+/).filter(Boolean)
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
    return (parts[0][0] + parts[1][0]).toUpperCase()
  }

  return [
    projects.value.map((proj) => ({
      label: proj.name,
      avatar: {
        // Use project icon if available, otherwise show initials
        src: proj.icon || undefined,
        text: proj.icon ? undefined : getInitials(proj.name),
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
        onSelect() {
          // Navigate to the create project page
          void navigateTo('/create')
        },
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
