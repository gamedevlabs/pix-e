<script setup lang="ts">
const icon = defineModel<string | null>('icon', { required: true })

defineProps<{
  name: string
}>()

const isIconHovered = ref(false)

function removeIcon() {
  icon.value = null
}

function handleIconChange(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (e) => {
    icon.value = e.target?.result as string
  }
  reader.readAsDataURL(file)
}
</script>

<template>
  <UCard
    class="border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900"
    :ui="{ body: 'p-0' }"
  >
    <template #header>
      <div class="flex items-center gap-3">
        <div class="h-5 w-1 rounded-full bg-primary" />
        <h2 class="text-base font-bold text-gray-900 dark:text-gray-100">Project Icon</h2>
      </div>
    </template>

    <div class="px-5 pb-5 flex flex-col items-center gap-4">
      <div
        class="relative"
        @mouseenter="isIconHovered = true"
        @mouseleave="isIconHovered = false"
      >
        <UAvatar
          v-if="icon"
          :src="icon"
          :alt="name"
          size="2xl"
          class="ring-2 ring-primary-200 dark:ring-primary-800"
        />
        <UAvatar
          v-else
          :alt="name"
          size="2xl"
          :text="name.substring(0, 2).toUpperCase()"
          class="ring-2 ring-primary-200 dark:ring-primary-800 text-primary bg-primary-100 dark:bg-primary-900/50 font-bold"
        />
        <div
          v-if="icon && isIconHovered"
          class="absolute inset-0 flex items-center justify-center bg-black/50 rounded-full cursor-pointer"
          @click="removeIcon"
        >
          <UIcon name="i-lucide-trash-2" class="text-white size-5" />
        </div>
      </div>

      <div class="flex gap-2">
        <label class="cursor-pointer">
          <UButton
            label="Upload"
            icon="i-lucide-upload"
            color="neutral"
            variant="outline"
            size="sm"
            as="span"
          />
          <input type="file" accept="image/*" class="hidden" @change="handleIconChange" />
        </label>
        <UButton
          v-if="icon"
          label="Remove"
          icon="i-lucide-trash-2"
          color="error"
          variant="soft"
          size="sm"
          @click="removeIcon"
        />
      </div>

      <p class="text-xs text-gray-400 dark:text-gray-500 text-center">
        PNG, JPG or GIF — displayed as your project avatar
      </p>
    </div>
  </UCard>
</template>
