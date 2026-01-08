<script setup lang="ts">
import { computed, watch } from 'vue'

const authentication = useAuthentication()
await authentication.checkAuthentication()

const route = useRoute()
const router = useRouter()

// Use the project handler composable
const { isProjectSelected } = useProjectHandler()

// Pages that don't require a project to be selected
const pagesWithoutProject = [
  '/movie-script-evaluator',
  '/player-expectations',
  '/sentiments',
  '/pillars',
  '/create',
]

// Check if current page requires a project
const requiresProject = computed(() => {
  return !pagesWithoutProject.some((path) => route.path.startsWith(path))
})

// Redirect to index if trying to access a project-required page without a project
watch(
  [() => route.path, isProjectSelected],
  () => {
    if (
      route.path !== '/' &&
      route.path !== '/login' &&
      requiresProject.value &&
      !isProjectSelected.value
    ) {
      router.push('/')

      // show a toast notification, that we switched back to index
      const toast = useToast()
      toast.add({
        title: 'No Project Selected',
        description: 'Please choose a project to access this page.',
        color: 'warning',
      })
    }
  },
  { immediate: true },
)
</script>

<template>
  <UApp>
    <NuxtLoadingIndicator />

    <UMain>
      <NuxtLayout>
        <NuxtPage />
      </NuxtLayout>
    </UMain>
  </UApp>
</template>

<style scoped>
.page-enter-active,
.page-leave-active {
  transition: all 0.2s;
}

.page-enter-from,
.page-leave-to {
  opacity: 0;
  filter: blur(1rem);
}
</style>
