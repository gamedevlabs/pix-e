<script setup lang="ts">
defineProps<{
  visible: boolean
  saving?: boolean
}>()

defineEmits<{
  (e: 'save' | 'discard'): void
}>()
</script>

<template>
  <Transition name="slide-up">
    <div v-if="visible" class="sticky bottom-4 z-10">
      <UCard
        class="border border-primary/30 bg-white/90 dark:bg-gray-900/90 backdrop-blur shadow-lg"
        :ui="{ body: 'px-5 py-3' }"
      >
        <div class="flex items-center justify-between gap-4">
          <div class="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
            <UIcon name="i-lucide-circle-dot" class="size-3.5 text-primary animate-pulse" />
            You have unsaved changes
          </div>
          <div class="flex gap-2">
            <UButton
              label="Discard"
              color="neutral"
              variant="ghost"
              size="sm"
              :disabled="saving"
              @click="$emit('discard')"
            />
            <UButton
              label="Save Changes"
              icon="i-lucide-save"
              color="primary"
              size="sm"
              :loading="saving"
              @click="$emit('save')"
            />
          </div>
        </div>
      </UCard>
    </div>
  </Transition>
</template>

<style scoped>
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.2s ease;
}
.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(0.5rem);
}
</style>
