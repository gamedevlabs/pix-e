<script setup lang="ts">
// ============================================================================
// PAGE CONFIG - Edit these settings for this module
// ============================================================================
definePageMeta({
  middleware: ['authentication', 'project-context'],
  pageConfig: {
    type: 'project-required',
    showSidebar: true,
    title: 'Design Pillars',
    icon: 'i-lucide-landmark',
    navGroup: 'main',
    navOrder: 2,
    showInNav: true,
  },
})
// ============================================================================

const { currentProject } = useProjectHandler()

const {
  items: pillars,
  fetchAll: pillarsFetchAll,
  createItem: createPillar,
  updateItem: updatePillar,
  deleteItem: deletePillar,
  additionalFeature,
  featureFeedback,
  getContextInPillarsFeedback,
} = usePillars()

const { fetchGameConcept } = useGameConcept()

// Load workflow for the current project
const { toggleSubstep, loadForProject } = useProjectWorkflow()
if (currentProject.value?.id) {
  await loadForProject(currentProject.value.id)
}

await pillarsFetchAll()
await fetchGameConcept()

// pillars-1-1: "Open Design Pillars" — completes as soon as this page mounts
onMounted(() => {
  toggleSubstep('pillars-1', 'pillars-1-1')
})

const selectedPillar = ref(-1)
const newItem = ref<NamedEntity | null>(null)

function addItem() {
  newItem.value = { name: '', description: '' }
}

async function createItem(newEntityDraft: Partial<NamedEntity>) {
  const result = await createPillar(newEntityDraft)

  // pillars-1-2: "Create a new pillar" — completes on first successful save
  if (result) {
    await toggleSubstep('pillars-1', 'pillars-1-2')
  }

  newItem.value = null
}

async function handleUpdate(id: number, namedEntityDraft: Partial<NamedEntity>) {
  await updatePillar(id, { ...namedEntityDraft })
  selectedPillar.value = -1
}

async function dismissIssue(pillar: Pillar, index: number) {
  pillar.llm_feedback?.structuralIssues.splice(index, 1)
}

// pillars-2-1: "Generate LLM feedback for your first pillar" — completes when validate runs on any pillar
async function handleValidatePillar() {
  await toggleSubstep('pillars-2', 'pillars-2-1')
}

// pillars-2-2: "Fix a pillar issue with AI" — completes when the user closes the Fix with AI modal
async function handleFixWithAICompleted() {
  await toggleSubstep('pillars-2', 'pillars-2-2')
}

// pillars-3-1: "Write a new core idea, add additional features and then generate LLM feedback"
// completes when the user gets back the feedback response for the core design idea
async function handleGetContextInPillarsFeedback() {
  await getContextInPillarsFeedback()
  await toggleSubstep('pillars-3', 'pillars-3-1')
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
            @validate="handleValidatePillar"
            @fix-with-ai-completed="handleFixWithAICompleted"
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

      <!-- Pillar Evaluation Panel (supports both Monolithic and Agentic modes) -->
      <div class="-m-10 mt-10 border-t border-neutral-800 p-6">
        <PillarEvaluationPanel />
      </div>
    </div>

    <!-- Game Design Idea Section -->
    <GameConceptSidebar>
      <h2 class="text-2xl font-semibold mt-6 mb-4">Additional Feature:</h2>
      <UTextarea
        v-model="additionalFeature"
        placeholder="Describe an additional feature or mechanic..."
        variant="outline"
        color="secondary"
        size="xl"
        :rows="5"
        :max-rows="0"
        autoresize
        class="w-full"
      />

      <UButton
        icon="i-lucide-refresh-cw"
        label="Generate Feedback"
        color="secondary"
        variant="soft"
        loading-auto
        @click="handleGetContextInPillarsFeedback"
      />

      <h2 class="text-2xl font-semibold mt-6 mb-4">Feature Feedback:</h2>
      <p>{{ featureFeedback.rating }}</p>
      <p>
        {{ featureFeedback.feedback }}
      </p>
    </GameConceptSidebar>
  </div>
</template>
