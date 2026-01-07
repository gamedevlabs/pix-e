<script setup lang="ts">
const { currentProjectTitle, isProjectSelected } = useProjectHandler()

definePageMeta({
  middleware: 'authentication',
})

// Redirect to home if no project is selected
onMounted(() => {
  if (!isProjectSelected.value) {
    navigateTo('/')
  }
})
</script>

<template>
  <div>
    <SimpleContentWrapper>
      <!-- Hero Section -->
      <section class="text-center">
        <h1 class="text-4xl font-bold mb-4">Welcome to {{ currentProjectTitle }} 🎉</h1>
        <p class="text-gray-500 dark:text-gray-400 mb-6">Design games with research.</p>
      </section>

      <!-- Cards Section -->
      <section class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <UCard class="hover:shadow-lg transition">
          <template #header>
            <h2 class="font-semibold text-lg">Formalized Player Experience</h2>
          </template>
          <p>
            You can design player experiences through a formalization (currently being implemented).
          </p>
        </UCard>
        <UCard class="hover:shadow-lg transition">
          <template #header>
            <h2 class="font-semibold text-lg">LLM supported Design Pillars</h2>
          </template>
          <p>
            The tool has design pillar functionality, that is validated and cross-checked by the
            help of LLMs to make sure your design stays consistent.
          </p>
        </UCard>
        <UCard class="hover:shadow-lg transition">
          <template #header>
            <h2 class="font-semibold text-lg">Moodboard Generation</h2>
          </template>
          <p>
            Through multimodal LLMs, you can design your moodboard directly in the app by describing
            and interaction with the tool.
          </p>
        </UCard>
        <UCard class="hover:shadow-lg transition">
          <template #header>
            <h2 class="font-semibold text-lg">Player Expectations Dashboard</h2>
          </template>
          <p>
            What do players expect when buying different genre games? What do they like or dislike?
            For these insights and more, visit the Player Expectations module.
          </p>
        </UCard>
        <UCard class="hover:shadow-lg transition">
          <template #header>
            <h2 class="font-semibold text-lg">Unified Agentic AI Interface</h2>
          </template>
          <p>
            All pix:e AI features are powered by a unified agentic interface. The agentic approach
            ensures top-tier results through tool usage and improved context awareness.
          </p>
        </UCard>
        <UCard class="hover:shadow-lg transition">
          <template #header>
            <h2 class="font-semibold text-lg">Movie Script Evaluator for Virtual Production</h2>
          </template>
          <p>
            This tool is to evaluate movie scripts through LLMs based on the assets available in the
            game engine for virtual production purposes.
          </p>
        </UCard>
      </section>
    </SimpleContentWrapper>
  </div>
</template>

<style scoped></style>
