<script setup lang="ts">
import { platformConfigs } from '~/utils/platformConfig'

const { currentProject, currentProjectId } = useProjectHandler()

// The icon may be a URL/data-URL (image) or a single emoji character — render differently for each.
const iconIsImage = computed(() => {
  const icon = currentProject.value?.icon
  if (!icon) return false
  return (
    icon.startsWith('data:') ||
    icon.startsWith('http://') ||
    icon.startsWith('https://') ||
    icon.startsWith('/')
  )
})

function getProjectInitials(name: string) {
  if (!name) return 'P'
  const parts = name.split(/\s+/).filter(Boolean)
  if (parts.length === 0) return 'P'
  if (parts.length === 1) return parts[0]!.slice(0, 2).toUpperCase()
  const first = parts[0]?.[0]
  const second = parts[1]?.[0]
  if (!first || !second) return parts[0]!.slice(0, 2).toUpperCase()
  return (first + second).toUpperCase()
}

function navigateToSettings() {
  const projectQuery = currentProjectId.value ? `?id=${currentProjectId.value}` : ''
  navigateTo(`/settings${projectQuery}`)
}
</script>

<template>
  <UCard
    class="border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900"
    :ui="{ body: 'px-3 py-2.5' }"
  >
    <div class="flex items-stretch gap-4 min-h-20">
      <!-- Left: avatar + name + description -->
      <div class="flex items-center gap-4 min-w-0 flex-1">
        <UAvatar
          v-if="iconIsImage"
          :src="currentProject!.icon!"
          :alt="currentProject?.name || 'Project'"
          size="xl"
          class="shrink-0 ring-2 ring-primary-200 dark:ring-primary-800"
        />
        <div v-else-if="currentProject?.icon" class="text-5xl leading-none shrink-0">
          {{ currentProject.icon }}
        </div>
        <UAvatar
          v-else
          :text="getProjectInitials(currentProject?.name || 'Project')"
          :alt="currentProject?.name || 'Project'"
          size="xl"
          class="shrink-0 text-primary bg-primary-100 dark:bg-primary-900/50 font-bold ring-2 ring-primary-200 dark:ring-primary-800"
        />

        <div class="min-w-0">
          <h1
            class="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-gray-100 truncate leading-tight"
          >
            {{ currentProject?.name || 'Project' }}
          </h1>
          <p class="text-sm text-gray-500 dark:text-gray-400 truncate mt-0.5">
            {{ currentProject?.description || 'No description' }}
          </p>
        </div>
      </div>

      <!-- Right: settings top, badges bottom -->
      <div class="flex flex-col items-end justify-between shrink-0 gap-3">
        <UButton
          icon="i-lucide-settings"
          size="sm"
          color="neutral"
          variant="ghost"
          label="Settings"
          @click="navigateToSettings"
        />
        <div class="flex flex-col items-end gap-2">
          <div v-if="currentProject?.target_platforms?.length" class="flex items-center gap-2">
            <UTooltip
              v-for="platform in platformConfigs.filter((p) =>
                (currentProject?.target_platforms as string[])?.includes(p.value),
              )"
              :key="platform.value"
              :text="platform.label"
            >
              <UIcon :name="platform.icon" class="size-4 text-gray-500 dark:text-gray-400" />
            </UTooltip>
          </div>
          <div v-if="currentProject?.genres" class="flex flex-wrap justify-end items-center gap-2">
            <UBadge
              v-for="g in currentProject.genres"
              :key="g"
              :label="g"
              size="sm"
              color="neutral"
              variant="outline"
              class="pointer-events-none"
            />
          </div>
        </div>
      </div>
    </div>
  </UCard>
</template>
