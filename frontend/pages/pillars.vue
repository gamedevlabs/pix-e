<script setup lang="ts">
definePageMeta({
  middleware: 'authentication',
})

const config = useRuntimeConfig()

const {
  pillars,
  designIdea,
  llmFeedback,
  initalPillarFetch,
  createPillar,
  updatePillar,
  deletePillar,
  getLLMFeedback,
  validatePillar,
  updateDesignIdea,
} = await usePillars()

const selectedPillar = ref(-1)

initalPillarFetch()

await useFetch<GameDesign>(`${config.public.apiBase}/llm/design/get_or_create/`, {
  method: 'GET',
  credentials: 'include',
  headers: useRequestHeaders(['cookie']),
}).then((data) => {
  designIdea.value = data.data.value?.description ?? ''
})

async function handlePillarCreation() {
  const newPillar = await createPillar()
  selectedPillar.value = newPillar.pillar_id
}

async function handlePillarSelect(toSelect: number) {
  if (selectedPillar.value != -1) {
    const pillar = pillars.value.find((p) => p.pillar_id === selectedPillar.value)
    if (pillar) {
      await updatePillar(pillar)
    }
  }
  selectedPillar.value = toSelect
}

async function handlePillarDelete(pillar: Pillar) {
  if (selectedPillar.value === pillar.pillar_id) {
    selectedPillar.value = -1
  }
  await deletePillar(pillar)
}
</script>

<template>
  <div class="p-4">
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
      <div v-for="pillar in pillars" :key="pillar.pillar_id" class="relative">
        <UCard class="w-70 min-h-55 flex flex-col justify-center-safe" variant="soft">
          <template #header>
            <div class="w-full h-12 flex items-center justify-between">
              <div class="flex-1">
                <template v-if="selectedPillar === pillar.pillar_id">
                  <UInput
                    v-model="pillar.title"
                    placeholder="Enter name..."
                    size="xl"
                    variant="subtle"
                  />
                </template>
                <template v-else>
                  <h3 class="text-lg font-semibold h-full flex items-center">
                    {{ pillar.title !== '' ? pillar.title : 'Title' }}
                  </h3>
                </template>
              </div>
            </div>
          </template>

          <div class="flex-1 w-full flex items-center left-0">
            <template v-if="selectedPillar === pillar.pillar_id">
              <UTextarea
                v-model="pillar.description"
                placeholder="Enter description here..."
                size="lg"
                variant="subtle"
                :rows="1"
                autoresize
                class="w-full"
              />
            </template>
            <template v-else>
              <p>{{ pillar.description !== '' ? pillar.description : 'Description' }}</p>
            </template>
          </div>

          <template #footer>
            <div class="flex items-center justify-between">
              <UButton
                color="neutral"
                variant="soft"
                @click="
                  selectedPillar === pillar.pillar_id
                    ? handlePillarSelect(-1)
                    : handlePillarSelect(pillar.pillar_id)
                "
              >
                {{ selectedPillar === pillar.pillar_id ? 'Save' : 'Edit' }}
              </UButton>
              <UButton
                v-if="selectedPillar !== pillar.pillar_id"
                color="secondary"
                variant="soft"
                label="Validate"
                @click="validatePillar(pillar)"
              />
            </div>
            <UCollapsible class="pt-4" :open="pillar.display_open" :disabled="!pillar.llm_feedback">
              <UButton
                color="neutral"
                variant="soft"
                class="w-full text-left"
                :label="pillar.llm_feedback ? 'LLM Feedback' : 'No LLM Feedback'"
                icon="i-lucide-chevron-down"
                @click="pillar.display_open = !pillar.display_open"
              />
              <template #content>
                {{ pillar.llm_feedback }}
              </template>
            </UCollapsible>
          </template>
        </UCard>

        <UButton
          aria-label="Delete"
          icon="i-lucide-trash-2"
          color="error"
          variant="ghost"
          class="absolute top-2 right-2 z-10"
          @click="handlePillarDelete(pillar)"
        />
      </div>
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
