<script setup lang="ts">
import type { MovieProject } from '~/utils/movie-script-evaluator';

    definePageMeta({
      middleware: 'authentication',
    })

    const { user } = useAuthentication()
    const {
      items: movieScriptProjects,
      fetchAll,
      createItem: createMovieScriptProject,
    } = useMovieScriptEvaluator();

    onMounted(() => {
      fetchAll()
    })

    const newItem = ref<MovieProject| null>(null);

    function addItem() {
      newItem.value = { name: '', description: '' };
    }

    async function createItem(newEntityDraft: Partial<MovieProject>) {
      await createMovieScriptProject(newEntityDraft);
      newItem.value = null;
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
          <UButton style="margin-top: 25%;">See Details</UButton>
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

 <style scoped>
  </style>