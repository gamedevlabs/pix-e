<script setup lang="ts">
import type { DropdownMenuItem } from '@nuxt/ui'
import { useProjectHandler } from '~/composables/useProjectHandler'

const props = withDefaults(
  defineProps<{
    collapsed?: boolean
    /**
     * Visual variant.
     * - 'button': current UButton-based trigger.
     * - 'brand': compact row styled like Nuxt UI sidebar header.
     */
    variant?: 'button' | 'brand'
  }>(),
  {
    variant: 'button',
  },
)

// use the project's composable
const { projects, currentProject, switchProject, unselectProject } = useProjectHandler()

function getInitials(name: string) {
  const parts = name.split(/\s+/).filter(Boolean)
  const a = parts[0] || ''
  const b = parts[1] || ''
  const a0 = a[0] || ''
  const b0 = b[0] || ''
  if (!a) return 'P'
  if (!b) return a.slice(0, 2).toUpperCase()
  return (a0 + b0).toUpperCase()
}

// selected team/item derived from the currentProject state
const selectedTeam = computed(() => {
  const p = currentProject.value ?? projects.value[0]
  if (!p) {
    return {
      label: 'No project',
      avatar: {
        text: 'P',
        alt: 'No project',
      },
    }
  }

  return {
    label: p.name,
    avatar: {
      src: p.icon || undefined,
      text: p.icon ? undefined : getInitials(p.name),
      alt: p.name,
    },
  }
})

const items = computed<DropdownMenuItem[][]>(() => {
  return [
    projects.value.map((proj) => {
      const isSelected = currentProject.value?.id === proj.id
      return {
        label: proj.name,
        avatar: {
          src: proj.icon || undefined,
          text: proj.icon ? undefined : getInitials(proj.name),
          alt: proj.name,
        },
        trailingIcon: isSelected ? 'i-lucide-check' : undefined,
        class: isSelected ? 'bg-gray-100 dark:bg-gray-800' : undefined,
        onSelect() {
          void switchProject(proj.id)
        },
      }
    }),
    [
      {
        label: 'New Project',
        icon: 'i-lucide-circle-plus',
        onSelect() {
          void navigateTo('/create')
        },
      },
      {
        label: 'Manage projects',
        icon: 'i-lucide-cog',
        onSelect() {
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
    <!-- Default (existing) trigger -->
    <UButton
      v-if="props.variant === 'button'"
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

    <!-- Brand-row trigger (Nuxt UI sidebar header style) -->
    <UButton
      v-else
      :label="collapsed ? undefined : selectedTeam.label"
      color="neutral"
      variant="ghost"
      block
      :square="collapsed"
      class="justify-start data-[state=open]:bg-elevated"
      :trailing-icon="collapsed ? undefined : 'i-lucide-chevron-down'"
      :ui="{ trailingIcon: 'text-dimmed' }"
    >
      <template #leading>
        <UAvatar
          :src="selectedTeam.avatar?.src"
          :alt="selectedTeam.avatar?.alt"
          :text="selectedTeam.avatar?.text"
          size="xs"
          class="bg-primary/10"
        />
      </template>
    </UButton>
  </UDropdownMenu>
</template>
