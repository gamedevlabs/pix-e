<script setup lang="ts">
import SettingsBasicInfoCard from '~/components/settings/SettingsBasicInfoCard.vue'
import SettingsProjectDetailsCard from '~/components/settings/SettingsProjectDetailsCard.vue'
import SettingsProjectIconCard from '~/components/settings/SettingsProjectIconCard.vue'
import SettingsMetadataCard from '~/components/settings/SettingsMetadataCard.vue'
import SettingsSaveBar from '~/components/settings/SettingsSaveBar.vue'

definePageMeta({
  middleware: 'authentication',
  pageConfig: {
    type: 'project-required',
    showSidebar: true,
    title: 'Settings',
    icon: 'i-lucide-settings',
    navGroup: 'main',
    navOrder: 6,
    showInNav: true,
  },
})

const {
  formData,
  originalProject,
  isLoading,
  isSaving,
  hasChanges,
  handleCancel,
  handleSubmit,
} = useProjectSettings()
</script>

<template>
  <div class="max-w-screen-2xl mx-auto w-full px-2 py-8 space-y-8">
    <div v-if="isLoading" class="flex items-center justify-center min-h-100">
      <UIcon name="i-lucide-loader-2" class="animate-spin size-8 text-primary" />
    </div>

    <template v-else>
      <h1 class="text-xl font-semibold text-gray-900 dark:text-gray-100 px-1">Settings</h1>

      <form class="space-y-6" @submit.prevent="handleSubmit">
        <div class="grid grid-cols-1 xl:grid-cols-[1fr_300px] gap-6 items-start">
          <div class="space-y-6">
            <SettingsBasicInfoCard
              v-model:name="formData.name"
              v-model:short-description="formData.shortDescription"
            />
            <SettingsProjectDetailsCard
              v-model:genre="formData.genre"
              v-model:target-platform="formData.targetPlatform"
            />
          </div>

          <div class="space-y-6">
            <SettingsProjectIconCard v-model:icon="formData.icon" :name="formData.name" />
            <SettingsMetadataCard v-if="originalProject" :project="originalProject" />
          </div>
        </div>

        <SettingsSaveBar
          :visible="hasChanges"
          :saving="isSaving"
          @save="handleSubmit"
          @discard="handleCancel"
        />
      </form>
    </template>
  </div>
</template>
