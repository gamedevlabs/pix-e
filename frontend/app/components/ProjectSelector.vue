<script setup lang="ts">
import type { DropdownMenuItem } from '@nuxt/ui'

defineProps<{
  collapsed?: boolean
}>()

const projects = ref([
  {
    label: 'Project One',
    avatar: {
      src: 'https://github.com/nuxt.png',
      alt: 'Project One',
    },
  },
  {
    label: 'Project 2',
    avatar: {
      src: 'https://github.com/nuxt-hub.png',
      alt: 'Project 2',
    },
  },
  {
    label: 'Demo Project',
    avatar: {
      src: 'https://github.com/nuxtlabs.png',
      alt: 'Demo Project',
    },
  },
])
const selectedTeam = ref(projects.value[0])

const items = computed<DropdownMenuItem[][]>(() => {
  return [
    projects.value.map((team) => ({
      ...team,
      onSelect() {
        selectedTeam.value = team
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
