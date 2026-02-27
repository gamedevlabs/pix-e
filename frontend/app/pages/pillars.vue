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

const _config = useRuntimeConfig()
const { currentProject } = useProjectHandler()

const {
  items: pillars,
  fetchAll: pillarsFetchAll,
  createItem: createPillar,
  updateItem: updatePillar,
  deleteItem: deletePillar,
  additionalFeature,
  designIdea,
  llmFeedback,
  featureFeedback,
  getPillarsInContextFeedback,
  updateDesignIdea,
  getPillarsCompleteness,
  getPillarsAdditions,
  getPillarContradictions,
  getContextInPillarsFeedback,
} = usePillars()

// Load workflow for the current project
const { toggleSubstep, loadForProject } = useProjectWorkflow()
if (currentProject.value?.id) {
  await loadForProject(currentProject.value.id)
}

await pillarsFetchAll()

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

async function handleGetPillarsInContextFeedback() {
  await getPillarsInContextFeedback()

  // Complete all three pillars-4 substeps when Refresh All is used
  await toggleSubstep('pillars-4', 'pillars-4-1')
  await toggleSubstep('pillars-4', 'pillars-4-2')
  await toggleSubstep('pillars-4', 'pillars-4-3')
}

async function handleGetPillarsCompleteness() {
  await getPillarsCompleteness()

  // pillars-4-1: "Coverage"
  await toggleSubstep('pillars-4', 'pillars-4-1')
}

async function handleGetPillarContradictions() {
  await getPillarContradictions()

  // pillars-4-2: "Contradictions"
  await toggleSubstep('pillars-4', 'pillars-4-2')
}

async function handleGetPillarsAdditions() {
  await getPillarsAdditions()

  // pillars-4-3: "Additions"
  await toggleSubstep('pillars-4', 'pillars-4-3')
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

      <!-- Overall LLM Feedback -->
      <div class="-m-10 mt-10 border-t border-neutral-800 p-6">
        <h2 class="text-2xl font-bold">
          LLM Feedback
          <UButton
            icon="i-lucide-refresh-cw"
            label="Refresh All"
            color="secondary"
            variant="soft"
            loading-auto
            @click="handleGetPillarsInContextFeedback"
          />
        </h2>

        <div class="w-full p-4 gap-4">
          <h2 class="text-2xl font-bold">
            Coverage:
            <UButton
              icon="i-lucide-refresh-cw"
              label="Refresh"
              color="secondary"
              variant="soft"
              loading-auto
              @click="handleGetPillarsCompleteness"
            />
          </h2>
          <!-- Coverage Feedback -->
          <div class="w-full p-4 gap-4">
            <div
              v-for="pillar in llmFeedback.coverage.pillarFeedback"
              :key="pillar.name"
              class="border-b mb-4 border-neutral-500 pb-4"
            >
              <h3 class="text-lg font-semibold">{{ pillar.name }}</h3>
              <p>{{ pillar.reasoning }}</p>
            </div>
          </div>
          <!-- Contradictions Feedback -->
          <h2 class="text-2xl font-bold">
            Contradictions:
            <UButton
              icon="i-lucide-refresh-cw"
              label="Refresh"
              color="secondary"
              variant="soft"
              loading-auto
              @click="handleGetPillarContradictions"
            />
          </h2>
          <div class="w-full p-4 gap-4">
            <div
              v-for="contradiction in llmFeedback.contradictions.contradictions"
              :key="contradiction.pillarOneId"
              class="border-b mb-4 border-neutral-500 pb-4"
            >
              <h3 class="text-lg font-semibold">
                {{ contradiction.pillarOneTitle + ' vs ' + contradiction.pillarTwoTitle }}
              </h3>
              <p>{{ contradiction.reason }}</p>
            </div>
          </div>

          <!-- Additions Feedback -->
          <h2 class="text-2xl font-bold">
            Additions:

            <UButton
              icon="i-lucide-refresh-cw"
              label="Refresh"
              color="secondary"
              variant="soft"
              loading-auto
              @click="handleGetPillarsAdditions"
            />
          </h2>
          <div class="w-full p-4 gap-4">
            <div
              v-for="pillar in llmFeedback.proposedAdditions.additions"
              :key="pillar.name"
              class="border-b mb-4 border-neutral-500 pb-4"
            >
              <h3 class="text-lg font-semibold">{{ pillar.name }}</h3>
              <p>{{ pillar.description }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Game Design Idea Section -->
    <div
      class="flex-shrink-0 basis-[20%] min-w-[270px] max-w-[420px] border-l border-neutral-800 p-6"
    >
      <h2 class="text-2xl font-semibold mb-4">Core Design Idea:</h2>
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
    </div>
  </div>
</template>
