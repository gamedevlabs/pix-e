<script setup lang="ts">
const authentication = useAuthentication()
await authentication.checkAuthentication()

const router = useRouter()
const { switchProject } = useCurrentProject()

const username = computed(() => authentication.user.value?.username || 'Guest')
const isLoggedIn = computed(() => authentication.isLoggedIn.value)

// Project cards - actual projects
const projectCards = ref([
  {
    id: 'demo-project',
    label: 'Demo Project',
    description: 'This is the standard project using the dev database. Please continue your work here.',
    icon: 'i-lucide-folder-open',
    requiresAuth: true,
    isCreateCard: false,
    action: async () => {
      await switchProject('demo')
    },
  },
  {
    id: 'create-project',
    label: 'Create New Project',
    requiresAuth: true,
    isCreateCard: true,
    action: async () => {
      const { createProject } = useCurrentProject()
      await createProject({ title: 'New Project' })
    },
  },
])

// Standalone modules - modules that don't require a project
const standaloneModules = ref([
  {
    id: 'movie-script',
    label: 'Movie Script Evaluator',
    description: 'Evaluate movie scripts through LLMs based on available assets for virtual production.',
    icon: 'i-lucide-film',
    requiresAuth: false,
    action: () => {
      router.push('/movie-script-evaluator')
    },
  },
])

const handleCardClick = (card: any) => {
  if (card.requiresAuth && !isLoggedIn.value) {
    router.push('/login')
  } else {
    card.action()
  }
}
</script>

<template>
  <UContainer class="py-10 space-y-10">
    <!-- Hero Section -->
    <section class="text-center">
      <h1 class="text-4xl font-bold mb-4">
        Welcome <span v-if="isLoggedIn" class="text-primary">{{ username }}</span> 🎉
      </h1>
      <p class="text-gray-500 dark:text-gray-400 mb-6">
        <span class="text-primary font-semibold">pix:e</span> enables you to design games with research.
      </p>
    </section>

    <!-- Projects Section -->
    <section>
      <h2 class="text-3xl font-bold mb-6">Projects</h2>
      
      <!-- Project Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="project in projectCards"
          :key="project.id"
          class="relative"
        >
          <!-- Login Overlay for auth-required projects -->
          <div
            v-if="project.requiresAuth && !isLoggedIn"
            class="absolute inset-0 bg-black/60 dark:bg-black/70 backdrop-blur-sm z-10 rounded-lg flex items-center justify-center"
          >
            <UButton
              label="Login"
              icon="i-lucide-log-in"
              color="primary"
              size="lg"
              @click="router.push('/login')"
            />
          </div>

          <!-- Create New Project Card (centered icon style) -->
          <UCard 
            v-if="project.isCreateCard"
            class="hover:shadow-lg transition cursor-pointer h-full flex items-center justify-center min-h-[200px]"
            :class="{ 'opacity-75': project.requiresAuth && !isLoggedIn }"
            @click="handleCardClick(project)"
          >
            <div class="flex flex-col items-center justify-center py-8 text-gray-400 dark:text-gray-500">
              <UIcon name="i-heroicons-plus-circle" class="text-6xl mb-2" />
              <p class="text-sm font-medium">New Project</p>
            </div>
          </UCard>

          <!-- Regular Project Card -->
          <UCard 
            v-else
            class="hover:shadow-lg transition cursor-pointer h-full"
            :class="{ 'opacity-75': project.requiresAuth && !isLoggedIn }"
            @click="handleCardClick(project)"
          >
            <template #header>
              <div class="flex items-center gap-3">
                <UIcon :name="project.icon" class="text-2xl" />
                <h2 class="font-semibold text-lg">{{ project.label }}</h2>
              </div>
            </template>
            <p class="text-sm text-gray-600 dark:text-gray-400">
              {{ project.description }}
            </p>
          </UCard>
        </div>
      </div>
    </section>

    <!-- Standalone Modules Section -->
    <section class="mt-16">
      <h2 class="text-2xl font-bold mb-6">Standalone Modules</h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="module in standaloneModules"
          :key="module.id"
          class="relative"
        >
          <!-- Module Card -->
          <UCard 
            class="hover:shadow-lg transition cursor-pointer h-full"
            @click="handleCardClick(module)"
          >
            <template #header>
              <div class="flex items-center gap-3">
                <UIcon :name="module.icon" class="text-2xl" />
                <h2 class="font-semibold text-lg">{{ module.label }}</h2>
              </div>
            </template>
            <p class="text-sm text-gray-600 dark:text-gray-400">
              {{ module.description }}
            </p>
          </UCard>
        </div>
      </div>
    </section>
  </UContainer>
</template>

<style scoped></style>
