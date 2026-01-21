<script setup lang="ts">
definePageMeta({
  middleware: 'authentication',
})

const route = useRoute()
const id = route.params.id as string
</script>

<template>
  <div class="p-8">
    <MovieScriptEvaluatorCanvas :project-id="id" />
  </div>
</template>
