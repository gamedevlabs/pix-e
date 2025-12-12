<script setup lang="ts">
import type { FormSubmitEvent } from '@nuxt/ui'
import SingleFileUpload from '~/components/MovieScriptEvaluatorComponents/SingleFileUpload.vue'

const props = defineProps<{
  projectId: string
}>()

const { items,fetchAll } = useMovieScriptEvaluatorAssets(props.projectId);
const { user } = useAuthentication()

onMounted(() => {
  fetchAll();
})

const state = reactive<Partial<any>>({
  movieScriptFile: null,
})

async function onSubmit(event: FormSubmitEvent<any>) {
  console.log(event.data)
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
          @submit="onSubmit"
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
