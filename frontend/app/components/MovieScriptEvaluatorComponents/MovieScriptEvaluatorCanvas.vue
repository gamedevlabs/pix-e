<script setup lang="ts">
import type {
  MovieScriptAnalysisResponse,
  ScriptSceneAnalysis,
} from '~/utils/movie-script-evaluator'
import AnalysisResult from './AnalysisResult.vue'

const props = defineProps<{
  projectId: string
}>()

const { useAssets, useAnalyzeMovieScript, useScriptSceneAssetAnalysis, useRequiredAssets } =
  useMovieScriptEvaluator()
const { items, fetchAll } = useAssets(props.projectId)
const {
  items: analysisItems,
  createAll: createAnalysisAllItems,
  fetchAll: fetchAllAnalysisItems,
  getRecommendations,
  evaluateMissingItems,
} = useScriptSceneAssetAnalysis(props.projectId)

const { items: requiredAssetsItems, fetchAll: fetchAllRequiredAssetsItems } = useRequiredAssets(
  props.projectId,
)

const { user } = useAuthentication()
const analysisResponse = ref<MovieScriptAnalysisResponse | null>(null)
const showResults = ref(false)
const showRecommendations = ref(false)
const toast = useToast()
const selectedScriptId = ref<number | null>(null)

onMounted(() => {
  fetchAll()
  fetchAllRequiredAssetsItems()
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

function triggerGetRecommendations() {
  toast.add({
    title: 'Action Has Been Triggered',
    description: 'Whenever the result is ready, you can view it. This may take a while.',
    color: 'info',
  })

  getRecommendations().then(() => {
    toast.add({
      title: 'Action Successful',
      description: 'Recommendations have been generated',
      color: 'success',
    })

    fetchAllRequiredAssetsItems()
    fetchAndFormatAnalysisResults()
  })
}

function selectScriptToAnalyze(scriptId: number) {
  selectedScriptId.value = scriptId
}

function saveAnalysisItems(item: ScriptSceneAnalysis[]) {
  const itemsTobeSent = item.map((i) => {
    i.project = props.projectId
    return i
  })

  createAnalysisAllItems(itemsTobeSent).then(() => {
    toast.add({
      title: 'Action Successful',
      description: 'All actions on items have been saved',
      color: 'success',
    })

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
      analysisResponse.value = {
        result: [...(analysisResponse.value?.result || []), ...response.result],
      }

      showResults.value = false

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

function triggerEvaluateMissingItems() {
  toast.add({
    title: 'Action Has Been Triggered',
    description: 'Whenever the result is ready, you can view it. This may take a while.',
    color: 'info',
  })
  evaluateMissingItems().then(() => {
    toast.add({
      title: 'Action Successful',
      description: 'Evaluation of missing items has been completed',
      color: 'success',
    })

    fetchAndFormatAnalysisResults()
  })
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
        <div class="mt-4 flex gap-2">
          <UButton type="button" label="Analyze Script" @click="anaylzeMovieScript" />
          <UButton
            v-if="analysisResponse"
            :label="showResults ? 'Close the analysis' : 'See the analysis'"
            @click="showResults = !showResults"
          />
          <UButton type="button" label="Get Recommendations" @click="triggerGetRecommendations" />
          <UButton
            type="button"
            :label="showRecommendations ? 'Close Recommendations' : 'Show Recommendations'"
            :color="showRecommendations ? 'warning' : 'success'"
            @click="showRecommendations = !showRecommendations"
          />
        </div>
        <div class="mt-2 flex gap-2">
          <UButton
            type="button"
            label="Evaluate Missing Items"
            @click="triggerEvaluateMissingItems"
          />
        </div>

        <div v-if="showResults && analysisResponse" class="mt-4 mr-4">
          <h3 class="text-lg font-semibold mb-2">Analysis Result:</h3>
          <AnalysisResult
            :analysis-data="analysisResponse?.result"
            @save-all="saveAnalysisItems"
            @load-items="fetchAndFormatAnalysisResults"
          />
        </div>

        <div v-if="showRecommendations" class="mt-4 mr-4">
          <h3 class="text-lg font-semibold mb-2">Recommended Assets:</h3>
          <RequiredAssetsResult :required-assets="requiredAssetsItems" />
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
