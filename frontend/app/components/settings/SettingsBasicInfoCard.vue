<script setup lang="ts">
const name = defineModel<string>('name', { required: true })
const shortDescription = defineModel<string>('shortDescription', { required: true })
</script>

<template>
  <UCard
    class="border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900"
    :ui="{ body: 'p-0' }"
  >
    <template #header>
      <div class="flex items-center gap-3">
        <div class="h-5 w-1 rounded-full bg-primary" />
        <h2 class="text-base font-bold text-gray-900 dark:text-gray-100">Basic Information</h2>
      </div>
    </template>

    <div class="px-5 pb-5 space-y-5">
      <UFormField label="Project Name" required>
        <UInput
          v-model="name"
          placeholder="Enter project name"
          size="md"
          class="w-full"
          required
        />
      </UFormField>

      <UFormField label="Short Description">
        <UTextarea
          v-model="shortDescription"
          placeholder="Brief description of your project"
          :rows="3"
          size="md"
          class="w-full"
        />
      </UFormField>
    </div>
  </UCard>
</template>
