<script setup lang="ts">
import LandingPublic from '~/components/landing/LandingPublic.vue'
import LandingAuthenticated from '~/components/landing/LandingAuthenticated.vue'

definePageMeta({
  pageConfig: {
    type: 'public',
    showSidebar: false,
    title: 'Projects',
  },
})

const authentication = useAuthentication()
await authentication.checkAuthentication()

const router = useRouter()
const route = useRoute()
const toast = useToast()

const isLoggedIn = computed(() => authentication.isLoggedIn.value)
const username = computed(() => authentication.user.value?.username || 'Guest')

// Surface error notifications coming from middleware redirects (e.g. project guard).
onMounted(() => {
  const error = route.query.error as string | undefined
  const projectId = route.query.projectId as string | undefined
  const message = route.query.message as string | undefined

  if (error === 'no-project') {
    toast.add({
      title: 'No Project Selected',
      description: message || 'Please select a project to use this module',
      color: 'warning',
      icon: 'i-lucide-alert-circle',
    })
    router.replace({ query: {} })
  } else if (error === 'project-not-found') {
    toast.add({
      title: 'Project Not Found',
      description: `Project "${projectId}" does not exist`,
      color: 'error',
      icon: 'i-lucide-alert-triangle',
    })
    router.replace({ query: {} })
  }
})
</script>

<template>
  <div class="max-w-screen-2xl mx-auto w-full px-6 lg:px-10 xl:px-14 py-10 space-y-14">
    <template v-if="isLoggedIn">
      <OnboardingSlideover />
      <LandingAuthenticated :username="username" />
    </template>

    <LandingPublic v-else />
  </div>
</template>
