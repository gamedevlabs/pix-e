<script setup lang="ts">
const { designIdea, isSavingConcept, fetchGameConcept, saveGameConcept } = useGameConcept()

const showHistoryModal = ref(false)

defineExpose({
  fetchGameConcept,
})
</script>

<template>
  <div
    class="flex flex-col flex-shrink-0 basis-[20%] min-w-[270px] max-w-[420px] h-full border-l border-neutral-800 p-6"
  >
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-2xl font-semibold">Game Concept</h2>
      <div class="flex items-center gap-2">
        <UButton
          icon="i-heroicons-clock"
          label="History"
          color="secondary"
          variant="soft"
          size="sm"
          @click="showHistoryModal = true"
        />
        <UButton
          icon="i-heroicons-arrow-down-tray"
          label="Save"
          color="primary"
          size="sm"
          :loading="isSavingConcept"
          :disabled="!designIdea.trim()"
          @click="saveGameConcept"
        />
      </div>
    </div>
    <div class="game-concept-textarea-wrapper h-[35vh]">
      <UTextarea
        v-model="designIdea"
        placeholder="Enter your game design idea here..."
        variant="outline"
        color="secondary"
        size="xl"
        class="w-full h-full"
      />
    </div>

    <!-- Slot for additional content -->
    <slot />

    <!-- History Modal -->
    <GameConceptHistoryModal v-model="showHistoryModal" />
  </div>
</template>

<style scoped>
.game-concept-textarea-wrapper {
  display: flex;
  flex-direction: column;
}

.game-concept-textarea-wrapper :deep(> div) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.game-concept-textarea-wrapper :deep(textarea) {
  flex: 1;
  height: 100% !important;
  resize: none;
  overflow-y: auto;
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE and Edge */
}

.game-concept-textarea-wrapper :deep(textarea)::-webkit-scrollbar {
  display: none; /* Chrome, Safari, Opera */
}
</style>
