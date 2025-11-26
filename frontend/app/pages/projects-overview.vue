<script setup lang="ts">
const authentication = useAuthentication()
await authentication.checkAuthentication()

const toast = useToast()
const router = useRouter()

const username = computed(() => authentication.user.value?.username || 'User')

const handleCreateProject = () => {
  toast.add({
    title: 'Feature Not Available',
    description: 'This feature is not implemented yet.',
    color: 'warning',
  })
}

const handleOpenDemoProject = () => {
  router.push('/')
}
</script>

<template>
  <UContainer class="py-10 space-y-10">
    <!-- Hero Section -->
    <section class="text-center">
      <h1 class="text-4xl font-bold mb-4">
        Welcome back <span class="text-primary">{{ username }}</span> 🎉
      </h1>
      <p class="text-gray-500 dark:text-gray-400 mb-6">
        <span class="text-primary font-semibold">pix:e</span> enables you to design your project with research.
      </p>
    </section>

    <!-- Projects Overview Section -->
    <section>
      <h2 class="text-3xl font-bold mb-6">Projects Overview</h2>
      
      <!-- Project Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <!-- Demo Project Card -->
        <UCard 
          class="hover:shadow-lg transition cursor-pointer"
          @click="handleOpenDemoProject"
        >
          <template #header>
            <h2 class="font-semibold text-lg">Demo Project</h2>
          </template>
          <p>
            This is the standard project using the dev database. Please continue your work here.
          </p>
        </UCard>

        <!-- Create New Project Card -->
        <UCard 
          class="hover:shadow-lg transition cursor-pointer flex items-center justify-center min-h-[150px]"
          @click="handleCreateProject"
        >
          <div class="flex flex-col items-center justify-center py-8 text-gray-400 dark:text-gray-500">
            <UIcon name="i-heroicons-plus-circle" class="text-6xl mb-2" />
            <p class="text-sm font-medium">Create New Project</p>
          </div>
        </UCard>
      </div>
    </section>
  </UContainer>
</template>
