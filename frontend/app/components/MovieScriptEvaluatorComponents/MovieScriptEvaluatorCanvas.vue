<script setup lang="ts">
import SingleFileUpload from '~/components/MovieScriptEvaluatorComponents/SingleFileUpload.vue'

const props = defineProps<{
  projectId: string
}>()

const { useAssets, useUploadFile } = useMovieScriptEvaluator()
const { items, fetchAll } = useAssets(props.projectId)
const { user } = useAuthentication()
const toast = useToast()

onMounted(() => {
  fetchAll()
})

function uploadFile(file: File) {
  useUploadFile(props.projectId, file)
    .then((_) =>
      toast.add({
        title: 'File Upload Successful',
        description: 'File has been uploaded successfully',
        color: 'success',
      }),
    )
    .catch((_) =>
      toast.add({
        title: 'File Upload Failed',
        description: 'File couldnt be uploaded, server error',
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
        <h2 class="text-xl font-semibold mb-2">Uploaded Movie Script</h2>
        <SingleFileUpload
          :max-file-size="2 * 1024 * 1024"
          :accepted-file-types="['application/pdf', 'text/plain']"
          @upload-file="uploadFile"
        />
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
