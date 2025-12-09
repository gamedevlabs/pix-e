<script setup lang="ts">
import {useCurrentProject} from "~~/composables/useCurrentProject";

const route = useRoute()
const projectId = route.params.id as string

const { setCurrentProject } = useCurrentProject()

// Set the current project context when entering this page
onMounted(() => {
  setCurrentProject(projectId)
})
</script>

<template>
  <NuxtPage />
</template>
