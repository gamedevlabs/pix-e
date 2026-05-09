<script setup lang="ts">
const open = defineModel<boolean>('open', { required: true })
const file = defineModel<File | null>('file', { required: true })
</script>

<template>
  <div
    v-if="open"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-25"
    @click="open = false"
  >
    <div
      class="bg-white dark:bg-gray-900 rounded-lg p-6 shadow-xl max-w-md w-full mx-4"
      @click.stop
    >
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold">Upload Project Icon</h3>
        <UButton
          icon="i-heroicons-x-mark"
          color="neutral"
          variant="ghost"
          size="xs"
          @click="open = false"
        />
      </div>

      <UFileUpload
        v-model="file"
        accept="image/*"
        icon="i-heroicons-photo"
        label="Drop your icon here"
        description="SVG, PNG, JPG or GIF (max. 2MB)"
        layout="grid"
        :interactive="false"
        class="w-full min-h-48"
      >
        <template #actions="{ open: openPicker }">
          <UButton
            label="Select image"
            icon="i-heroicons-arrow-up-tray"
            color="neutral"
            variant="outline"
            @click="openPicker()"
          />
        </template>
      </UFileUpload>
    </div>
  </div>
</template>
