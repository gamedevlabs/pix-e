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
  pillarCompleteness,
  getPillarCompleteness,
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

async function dismissIssue(pillar: Pillar, index: number) {
  pillar.llm_feedback?.structuralIssues.splice(index, 1)
}
</script>

<template>
  <div class="flex -m-10">
    <div class="flex-1 min-w-0 p-10">
      <!-- Pillar Display -->
      <h2 class="text-2xl font-bold mb-4">Pillars:</h2>
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
            @dismiss="dismissIssue(pillar, $event)"
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

      <!-- Overall LLM Feedback -->
      <div class="-m-10 mt-10 border-t border-neutral-800 p-6">
        <h2 class="text-2xl font-bold">
          LLM Feedback
          <UButton
            icon="i-lucide-refresh-cw"
            label="Refresh"
            color="secondary"
            variant="soft"
            loading-auto
            @click="getPillarCompleteness"
          />
        </h2>

        <div class="w-full p-4 gap-4">
          <!-- Direct Feedback -->
          <div v-for="pillar in pillarCompleteness.ideaIssues" :key="pillar.name">
            <h3 class="text-lg font-semibold">{{ pillar.name + " " + pillar.pillarId}}</h3>
            <p>{{ pillar.description }}</p>
          </div>
        </div>
        <h2 class="text-2xl font-bold">Additions:</h2>
        <!-- Additional Feedback -->
        <div class="w-full p-4 gap-4">
          <div v-for="pillar in pillarCompleteness.proposedAdditions" :key="pillar.name">
            <h3 class="text-lg font-semibold">{{ pillar.name + " " + pillar.pillarId}}</h3>
            <p>{{ pillar.description }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Game Design Idea Section -->
    <div
      class="flex-shrink-0 basis-[20%] min-w-[270px] max-w-[420px] border-l border-neutral-800 p-6"
    >
      <h2 class="text-2xl font-semibold mb-4">Game Design Idea:</h2>
      <UTextarea
        v-model="designIdea"
        placeholder="Enter your game design idea here..."
        variant="outline"
        color="secondary"
        size="xl"
        :rows="25"
        :max-rows="0"
        autoresize
        class="w-full"
        @focusout="updateDesignIdea"
      />
    </div>
  </div>
</template>
