<script setup lang="ts">
import type { MovieScript } from '~/utils/movie-script-evaluator'
import SingleFileUpload from './SingleFileUpload.vue'
import MovieScriptList from './MovieScriptList.vue'

const props = defineProps<{
  projectId: string
}>()

const { uploadMovieScript } = useMovieScriptEvaluator()
const {
  items,
  fetchAll: fetchScripts,
  deleteItem: deleteScript,
} = useMovieScriptEvaluator().useMovieScript(props.projectId)
const isUploadingMode = ref(false)
const isListingMode = ref(true)
const toast = useToast()

onMounted(() => {
  fetchScripts()
})

function uploadFile(file: File, fileName: string) {
  if (fileName.trim() === '') {
    fileName = file.name
  }

  const movieScript: MovieScript = {
    title: fileName,
    file: file,
  }

  uploadMovieScript(props.projectId, movieScript)
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
    .finally(() => {
      fetchScripts()
    })
}

function deleteScriptFile(fileId: number) {
  deleteScript(fileId).then(() => {
    fetchScripts()
  })
}
</script>

<template>
  <h2 class="text-xl font-semibold mb-2">Movie Scripts</h2>
  <div class="flex flex-col space-y-4 mb-6">
    <div>
      <UButton
        :label="isListingMode ? 'Close the list' : 'Open file list'"
        @click="isListingMode = !isListingMode"
      />

      <MovieScriptList v-if="isListingMode" :files="items" @delete="deleteScriptFile" />
    </div>
    <div>
      <UButton
        :label="isUploadingMode ? 'Close the file uploader' : 'Upload a New Script'"
        @click="isUploadingMode = !isUploadingMode"
      />
      <SingleFileUpload
        v-if="isUploadingMode"
        :max-file-size="2 * 1024 * 1024"
        :accepted-file-types="['application/pdf', 'text/plain']"
        @upload-file="uploadFile"
      />
    </div>
  </div>
</template>
