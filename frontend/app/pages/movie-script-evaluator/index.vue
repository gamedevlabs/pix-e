<script setup lang="ts">
// ============================================================================
// PAGE CONFIG - Edit these settings for this module
// ============================================================================
definePageMeta({
  middleware: ['authentication'],
  pageConfig: {
    type: 'standalone',
    showSidebar: false,
    title: 'Movie Script Evaluator',
    icon: 'i-lucide-film',
  },
})
// ============================================================================
import type { MovieProject } from '~/utils/movie-script-evaluator'

const { user } = useAuthentication()

// Im not sure, if its a good approach
const {
  items: movieScriptProjects,
  fetchAll,
  createItem: createMovieScriptProject,
} = useMovieScriptEvaluator()

onMounted(() => {
  fetchAll()
})

const newItem = ref<MovieProject | null>(null)

function addItem() {
  newItem.value = { id: -1, name: '', description: '' }
}

async function createItem(newEntityDraft: Partial<MovieProject>) {
  await createMovieScriptProject(newEntityDraft)
  newItem.value = null
}

async function navigateToDetails(projectId: number) {
  await navigateTo(`/movie-script-evaluator/${projectId}`)
}
</script>
<template>
  <div class="p-8">
    <h1 class="text-2xl font-bold mb-6">Movie Script Evaluator</h1>
    <p>Welcome, {{ user?.username }}!</p>
    <p>This is the Movie Script Evaluator home page.</p>
    <SimpleContentWrapper>
      <template #header>Projects</template>
      <SimpleCardSection use-add-button @add-clicked="addItem">
        <div v-for="project in movieScriptProjects" :key="project.id" class="mb-4">
          <NamedEntityCard
            :named-entity="project"
            :visualization-style="'detailed'"
            show-edit
            show-delete
          >
            <UButton style="margin-top: 25%" @click="navigateToDetails(project.id)"
              >See Details</UButton
            >
          </NamedEntityCard>
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
    </SimpleContentWrapper>
  </div>
</template>

<style scoped></style>
