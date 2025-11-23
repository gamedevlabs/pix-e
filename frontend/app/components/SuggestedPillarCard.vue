<script setup lang="ts">
defineProps<{
  suggestion: PillarDTO
  isAccepting?: boolean
}>()

const emit = defineEmits<{
  accept: [suggestion: PillarDTO]
  decline: [suggestion: PillarDTO]
}>()
</script>

<template>
  <UCard variant="subtle" class="border border-primary-500/30">
    <template #header>
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <UIcon name="i-heroicons-plus-circle" class="text-primary-500" />
          <span class="font-semibold">{{ suggestion.name }}</span>
        </div>
        <UBadge color="primary" variant="subtle" size="xs">Suggested</UBadge>
      </div>
    </template>

    <p class="text-sm text-gray-600 dark:text-gray-300">
      {{ suggestion.description }}
    </p>

    <template #footer>
      <div class="flex justify-end gap-2">
        <UButton
          color="neutral"
          variant="ghost"
          size="sm"
          icon="i-heroicons-x-mark"
          label="Decline"
          :disabled="isAccepting"
          @click="emit('decline', suggestion)"
        />
        <UButton
          color="primary"
          size="sm"
          icon="i-heroicons-check"
          label="Accept"
          :loading="isAccepting"
          @click="emit('accept', suggestion)"
        />
      </div>
    </template>
  </UCard>
</template>
