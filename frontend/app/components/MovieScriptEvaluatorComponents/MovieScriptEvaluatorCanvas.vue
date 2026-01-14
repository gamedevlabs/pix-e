<script setup lang="ts">
import type {
  MovieScriptAnalysisResponse,
  ScriptSceneAnalysis,
} from '~/utils/movie-script-evaluator'
import AnalysisResult from './AnalysisResult.vue'

const props = defineProps<{
  projectId: string
}>()

const { useAssets, useAnalyzeMovieScript, useScriptSceneAssetAnalysis } = useMovieScriptEvaluator()
const { items, fetchAll } = useAssets(props.projectId)
const {
  items: analysisItems,
  createItem: createAnalysisItem,
  deleteItem: deleteAnalysisItem,
  updateItem: updateAnalysisItem,
  fetchAll: fetchAllAnalysisItems,
} = useScriptSceneAssetAnalysis(props.projectId)
const { user } = useAuthentication()
const analysisResponse = ref<MovieScriptAnalysisResponse | null>(null)
const showResults = ref(false)
const toast = useToast()
const selectedScriptId = ref<number | null>(null)

onMounted(() => {
  fetchAll()
  fetchAndFormatAnalysisResults()
})

function fetchAndFormatAnalysisResults() {
  fetchAllAnalysisItems().then((_) => {
    if (analysisItems.value.length > 0) {
      analysisResponse.value = {
        result: analysisItems.value,
      }
    }
  })
}

function selectScriptToAnalyze(scriptId: number) {
  selectedScriptId.value = scriptId
}

function saveAnalysisItems(item: ScriptSceneAnalysis[]) {
  Promise.all(
    item.map((i) => {
      i.project = props.projectId
      createAnalysisItem(i)
    }),
  ).then(() => {
    fetchAndFormatAnalysisResults()
  })
}

function anaylzeMovieScript() {
  toast.add({
    title: 'Action Has Been Triggered',
    description: 'Whenever the result is ready, you can view it',
    color: 'info',
  })

  useAnalyzeMovieScript(props.projectId, selectedScriptId.value!)
    .then((response) => {
      analysisResponse.value = response

      toast.add({
        title: 'Action Successful',
        description: 'The result has been created',
        color: 'success',
      })
    })
    .catch((error) =>
      toast.add({
        title: 'Action failed!',
        description:
          error.message || 'Server error occurred during analysis, please try again later',
        color: 'error',
      }),
    )
}
</script>

<template>
  <div class="p-8">
    <h1 class="text-2xl font-bold mb-6">Movie Script Evaluator</h1>
    <div class="mb-4">
      <p>Welcome, {{ user?.username }}!</p>
      <p>Your user id is {{ user?.id }}</p>
      <p>The project Id is {{ projectId }}</p>
    </div>

    <div class="movie-script-evaluator-container mb-8" style="display: flex; flex-direction: row">
      <div class="mb-4">
        <UploadScript :project-id="projectId" @select="selectScriptToAnalyze" />
        <div class="mt-4 flex">
          <UButton type="button" label="Analyze Script" @click="anaylzeMovieScript" />
          <UButton
            v-if="analysisResponse"
            class="ml-4"
            :label="showResults ? 'Close the analysis' : 'See the analysis'"
            @click="showResults = !showResults"
          />
        </div>

        <div v-if="showResults && analysisResponse" class="mt-4 mr-4">
          <h3 class="text-lg font-semibold mb-2">Analysis Result:</h3>
          <AnalysisResult
            :analysis-data="analysisResponse?.result"
            @save-all="saveAnalysisItems"
            @update="updateAnalysisItem"
            @delete="deleteAnalysisItem"
            @create="createAnalysisItem"
          />
        </div>
      </div>
      <div class="mb-4 ml-4">
        <h3>List of the Existing Assets</h3>
        <div style="max-height: 65vh; overflow-x: scroll; overflow-y: auto; white-space: nowrap">
          <div style="display: inline-block; vertical-align: top">
            <AssetsList :assets="items" />
          </div>
        </div>
      </div>
    </div>

    <!-- Add your movie script evaluator components and logic here -->
  </div>
</template>

<style scoped>
.mb-4 {
  width: 50%;
  max-height: 50%;
}
</style>
