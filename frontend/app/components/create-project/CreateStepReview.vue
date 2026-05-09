<script setup lang="ts">
import type { ProjectTargetPlatform } from '~/utils/project.d'
import { getPlatformConfig } from '~/utils/platformConfig'

defineProps<{
  name: string
  shortDescription: string
  genre: string[]
  targetPlatform: ProjectTargetPlatform[]
  iconUrl?: string | null
  previewUrl?: string | null
  avatarText?: string
}>()

defineEmits<{
  (e: 'edit-step', step: number): void
}>()
</script>

<template>
  <div class="space-y-6">
    <div>
      <h2 class="text-xl font-semibold mb-4">Review Your Project</h2>
      <p class="text-gray-600 dark:text-gray-400 mb-6">
        Almost done! Please review the information below before we create your project
      </p>
    </div>

    <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-6 space-y-6">
      <!-- Project Icon and Name -->
      <div class="flex items-center gap-4 pb-4 border-b border-gray-200 dark:border-gray-700">
        <div class="shrink-0">
          <div
            class="p-2 bg-white dark:bg-gray-900 rounded-full ring-2 ring-gray-200 dark:ring-gray-700"
          >
            <UAvatar size="xl" :src="previewUrl || iconUrl || undefined" :text="avatarText" />
          </div>
        </div>

        <div class="flex-1 group">
          <div class="flex items-center gap-2 mb-1">
            <label class="text-sm font-medium text-gray-500 dark:text-gray-400">
              Project Name
            </label>
            <UButton
              icon="i-heroicons-pencil"
              color="neutral"
              variant="ghost"
              size="sm"
              class="opacity-0 group-hover:opacity-100 transition-opacity"
              @click="$emit('edit-step', 1)"
            />
          </div>
          <p class="text-2xl font-bold">{{ name }}</p>
        </div>
      </div>

      <!-- Short Description -->
      <div class="group">
        <div class="flex items-center gap-2 mb-1">
          <label class="text-sm font-medium text-gray-500 dark:text-gray-400"> Description </label>
          <UButton
            icon="i-heroicons-pencil"
            color="neutral"
            variant="ghost"
            size="sm"
            class="opacity-0 group-hover:opacity-100 transition-opacity"
            @click="$emit('edit-step', 1)"
          />
        </div>
        <p v-if="shortDescription" class="text-gray-700 dark:text-gray-300">
          {{ shortDescription }}
        </p>
        <p v-else class="text-gray-400 dark:text-gray-500 italic">No description provided</p>
      </div>

      <div class="grid grid-cols-2 gap-6">
        <!-- Genre -->
        <div class="group">
          <div class="flex items-center gap-2 mb-2">
            <label class="text-sm font-medium text-gray-500 dark:text-gray-400">Genre</label>
            <UButton
              icon="i-heroicons-pencil"
              color="neutral"
              variant="ghost"
              size="sm"
              class="opacity-0 group-hover:opacity-100 transition-opacity"
              @click="$emit('edit-step', 2)"
            />
          </div>
          <div class="flex flex-wrap gap-2">
            <UBadge
              v-for="g in genre"
              :key="g"
              :label="g"
              color="neutral"
              variant="subtle"
              size="md"
            />
          </div>
        </div>

        <!-- Platforms -->
        <div class="group">
          <div class="flex items-center gap-2 mb-2">
            <label class="text-sm font-medium text-gray-500 dark:text-gray-400">Platforms</label>
            <UButton
              icon="i-heroicons-pencil"
              color="neutral"
              variant="ghost"
              size="sm"
              class="opacity-0 group-hover:opacity-100 transition-opacity"
              @click="$emit('edit-step', 2)"
            />
          </div>
          <div class="flex gap-3">
            <UIcon
              v-for="platform in targetPlatform"
              :key="platform"
              :name="getPlatformConfig(platform)?.icon || 'i-heroicons-square-3-stack-3d'"
              class="w-8 h-8 text-gray-700 dark:text-gray-300"
            />
          </div>
        </div>
      </div>
    </div>

    <UAlert
      icon="i-heroicons-information-circle"
      color="info"
      variant="soft"
      title="What happens next?"
      description="After creating your project, you'll be automatically redirected to the project dashboard where you can start building your game."
    />
  </div>
</template>
