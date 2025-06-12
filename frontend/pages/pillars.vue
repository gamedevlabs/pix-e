<script setup lang="ts">
definePageMeta({
  middleware: 'authentication',
})

const config = useRuntimeConfig()

const {
  items: pillars,
  fetchAll: pillarsFetchAll,
  createItem: createPillar,
  updateItem: updatePillar,
  deleteItem: deletePillar,
  designIdea,
  llmFeedback,
  getLLMFeedback,
  updateDesignIdea,
} = usePillars()

await pillarsFetchAll()

await useFetch<GameDesign>(`${config.public.apiBase}/llm/design/get_or_create/`, {
  method: 'GET',
  credentials: 'include',
  headers: useRequestHeaders(['cookie']),
}).then((data) => {
  designIdea.value = data.data.value?.description ?? ''
})

const selectedPillar = ref(-1)
const newItem = ref<NamedEntity | null>(null)

function addItem() {
  newItem.value = { name: '', description: '' }
}

async function createItem(newEntityDraft: Partial<NamedEntity>) {
  await createPillar(newEntityDraft)
  newItem.value = null
}

async function handleUpdate(id: number, namedEntityDraft: Partial<NamedEntity>) {
  await updatePillar(id, { ...namedEntityDraft })
  selectedPillar.value = -1
}
</script>

<template>
  <div>
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
      <SimpleCardSection use-add-button @add-clicked="addItem">
        <div v-for="pillar in pillars" :key="pillar.id">
          <PillarCard
            :pillar="pillar"
            :is-being-edited="selectedPillar === pillar.id"
            show-edit
            show-delete
            @edit="selectedPillar = selectedPillar === pillar.id ? -1 : pillar.id"
            @update="(namedEntityDraft) => handleUpdate(pillar.id, namedEntityDraft)"
            @delete="deletePillar(pillar.id)"
          />
        </div>
        <div v-if="newItem">
          <NamedEntityCard
            :named-entity="newItem"
            :is-being-edited="true"
            @edit="newItem = null"
            @update="createItem"
            @delete="newItem = null"
          />
        </div>
      </SimpleCardSection>
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
