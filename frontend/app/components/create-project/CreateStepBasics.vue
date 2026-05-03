<script setup lang="ts">
import { ref } from 'vue'

const name = defineModel<string>('name', { required: true })
const shortDescription = defineModel<string>('shortDescription', { required: true })

defineProps<{
  iconUrl?: string | null
  previewUrl?: string | null
  avatarText?: string
  submitting?: boolean
}>()

defineEmits<{
  (e: 'open-upload-modal'): void
}>()

const isAvatarHovered = ref(false)
</script>

<template>
  <div class="space-y-6">
    <div>
      <h2 class="text-xl font-semibold mb-4">Basic Information</h2>
      <p class="text-gray-600 dark:text-gray-400 mb-6">
        Let's start with the basics. What's the working title of your project?
      </p>
    </div>

    <div class="grid grid-cols-2 gap-6">
      <!-- Form inputs -->
      <div class="space-y-6">
        <UFormField label="Project Name" required>
          <UInput v-model="name" placeholder="My Awesome Game" size="lg" :disabled="submitting" />
        </UFormField>

        <UFormField label="Short Description" optional>
          <UTextarea
            v-model="shortDescription"
            placeholder="A brief description of your game project..."
            :rows="2"
            :disabled="submitting"
          />
        </UFormField>
      </div>

      <!-- Avatar with hover-to-upload -->
      <div class="flex flex-col items-center justify-center gap-4">
        <div
          class="relative cursor-pointer"
          @mouseenter="isAvatarHovered = true"
          @mouseleave="isAvatarHovered = false"
          @click="$emit('open-upload-modal')"
        >
          <UAvatar
            size="3xl"
            :src="previewUrl || iconUrl || undefined"
            :text="avatarText"
            class="transition-all duration-200"
            :class="{ 'brightness-75': isAvatarHovered }"
          />

          <div
            v-if="isAvatarHovered"
            class="absolute inset-0 flex items-center justify-center pointer-events-none"
          >
            <UIcon name="i-heroicons-arrow-up-tray" class="w-12 h-12 text-white" />
          </div>
        </div>

        <div class="flex flex-col items-center gap-1">
          <p class="text-sm font-medium text-gray-700 dark:text-gray-300">Project Icon</p>
          <p class="text-xs text-gray-500 text-center">You can upload your own icon</p>
        </div>
      </div>
    </div>
  </div>
</template>
