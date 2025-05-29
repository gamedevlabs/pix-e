<script setup lang="ts">
definePageMeta({
  middleware: 'authentication',
})

const config = useRuntimeConfig()

const { basics, designIdea, llmFeedback, getLLMFeedback, validatePillar, updateDesignIdea } =
  await usePillars()

basics.fetchAll()

await useFetch<GameDesign>(`${config.public.apiBase}/llm/design/get_or_create/`, {
  method: 'GET',
  credentials: 'include',
  headers: useRequestHeaders(['cookie']),
}).then((data) => {
  designIdea.value = data.data.value?.description ?? ''
})
const selectedPillar = ref(-1)
async function handlePillarCreation() {
  const dto: PillarDTO = {
    pillar_id: -1,
    title: 'New Pillar',
    description: '',
  }
  const newPillar = await basics.createItem(dto)
  selectedPillar.value = newPillar?.pillar_id ?? -1
}

async function handlePillarSelect(toSelect: number) {
  if (selectedPillar.value != -1) {
    const pillar = basics.items.value.find((p) => p.pillar_id === selectedPillar.value)
    if (pillar) {
      await basics.updateItem(pillar.pillar_id, pillar)
    }
  }
  selectedPillar.value = toSelect
}
</script>

<template>
  <div>
    <!-- Game Design Idea Section -->
    <h2 class="text-2xl font-bold mb-4">Game Design Idea:</h2>
    <div class="flex items-stretch w-300 max-w-xxl">
      <UTextarea
        v-model="designIdea"
        placeholder="Enter your game design idea here..."
        variant="outline"
        color="secondary"
        size="xl"
        class="w-full"
        autoresize
        @focusout="updateDesignIdea"
      />
    </div>

    <!-- Pillar Display -->
    <h2 class="text-2xl font-bold mt-6 mb-4">Pillars:</h2>
    <div class="flex mt-6 gap-4 flex-wrap p-5">
      <PillarDisplay
        v-for="(pillar, index) in basics.items.value"
        :key="pillar.pillar_id"
        v-model:pillar="basics.items.value[index]"
        :selected-pillar="selectedPillar"
        @select="handlePillarSelect"
      />
      <div>
        <UButton
          icon="i-lucide-plus"
          variant="soft"
          color="secondary"
          size="lg"
          class="w-70 min-h-55 [&>*]:text-[50px] justify-center"
          @click="handlePillarCreation"
        />
      </div>
    </div>

    <!-- LLM Feedback -->
    <h2 class="text-2xl font-bold mt-6 mb-4">
      LLM Feedback
      <UButton
        icon="i-lucide-refresh-cw"
        label="Refresh"
        color="secondary"
        variant="soft"
        @click="getLLMFeedback"
      />
    </h2>

    <div class="flex gap-4 flex-wrap w-300">
      <div
        style="color: var(--ui-color-secondary-200)"
        class="p-4 rounded-lg w-fit whitespace-pre-line"
      >
        {{ llmFeedback }}
      </div>
    </div>
  </div>
</template>
