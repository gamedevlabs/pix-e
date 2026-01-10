<script setup lang="ts">
import type { AssetListAnalysis } from '~/utils/movie-script-evaluator'

const props = defineProps<{
  projectId: string
}>()

const { useAssets, useAnalyzeMovieScript } = useMovieScriptEvaluator()
const { items, fetchAll } = useAssets(props.projectId)
const { user } = useAuthentication()
const analysisResponse = ref<AssetListAnalysis | null>(null)
const result = ref<string[] | null>(null)
const showResults = ref(false)
const toast = useToast()

onMounted(() => {
  fetchAll()
})

function anaylzeMovieScript() {
  toast.add({
    title: 'Action Has Been Triggered',
    description: 'Whenever the result is ready, you can view it',
    color: 'info',
  })

  useAnalyzeMovieScript(props.projectId)
    .then((response) => {
      analysisResponse.value = response
      result.value = []

      for (const scene of response.scenes) {
        if (scene.can_use_assets && scene.assets_used.length > 0) {
          result.value?.push(`Scene ${scene.scene_id} can use the following assets:`)
          scene.assets_used.forEach((asset) => {
            result.value?.push(`${asset}`)
          })
        }
      }

      toast.add({
        title: 'Action Successful',
        description: 'The result has been created',
        color: 'success',
      })
    })
    .catch((_) =>
      toast.add({
        title: 'Action failed!',
        description: 'Please try it again later',
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
        <UploadScript :project-id="projectId" />
        <div class="mt-4 flex">
          <UButton type="button" label="Analyze Script" @click="anaylzeMovieScript" />
          <UButton
            v-if="result"
            class="ml-4"
            :label="showResults ? 'Close the result' : 'See the result'"
            @click="showResults = !showResults"
          />
        </div>

        <div v-if="showResults && result" class="mt-4">
          <h3 class="text-lg font-semibold mb-2">Analysis Result:</h3>
          <p v-if="result.length === 0">No assets can be used from the uploaded script.</p>
          <ul v-else>
            <li v-for="(line, index) in result" :key="index">{{ line }}</li>
          </ul>
          <div class="mt-4 flex">
            <UButton label="Save Results" />
          </div>
        </div>
      </div>
      <div class="mb-4">
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
