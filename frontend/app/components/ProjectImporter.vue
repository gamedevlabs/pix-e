<script setup lang="ts">
const emit = defineEmits<{
  (e: 'filePicked', file: File): void
}>()

const { error } = usePixeToast()

const MAX_FILE_SIZE = 8 * 1024 * 1024

// Fires as soon as a file is chosen — the shared import flow (parse, match,
// diff-or-new) runs in the parent, so there's no separate Submit step.
function onSelect(file: File | File[] | null) {
  const picked = Array.isArray(file) ? file[0] : file
  if (!picked) return
  if (picked.type && picked.type !== 'application/json') {
    error('Please choose a JSON file.')
    return
  }
  if (picked.size > MAX_FILE_SIZE) {
    error('The file is too large. Please choose a file smaller than 8MB.')
    return
  }
  emit('filePicked', picked)
}
</script>

<template>
  <UFileUpload
    accept="application/json"
    :dropzone="true"
    icon="i-lucide-file-json"
    label="Drop your project export here"
    description="or click to browse · JSON file up to 8MB"
    class="w-full min-h-56"
    :ui="{
      base: 'border-2 border-dashed rounded-xl transition-colors hover:border-primary-400 data-[dragging=true]:border-primary-500 data-[dragging=true]:bg-primary-50/50 dark:data-[dragging=true]:bg-primary-950/20',
      avatar: 'bg-primary-100 text-primary-600 dark:bg-primary-900/40 dark:text-primary-300',
      label: 'font-semibold text-gray-800 dark:text-gray-100',
      description: 'text-gray-500 dark:text-gray-400',
    }"
    @update:model-value="onSelect"
  />
</template>
