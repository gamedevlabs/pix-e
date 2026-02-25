<script setup lang="ts">
// ============================================================================
// PAGE CONFIG - Edit these settings for this module
// ============================================================================
// ============================================================================
definePageMeta({
  middleware: ['authentication', 'project-context'],
  pageConfig: {
    type: 'project-required',
    showSidebar: true,
    title: 'Player Expectations',
    icon: 'i-lucide-users',
    navGroup: 'main',
    navOrder: 3,
    showInNav: true,
  },
})
</script>

<template>
  <UContainer class="py-10 space-y-10">
    <!-- Hero Section -->
    <section class="text-center">
      <h1 class="text-4xl font-bold mb-4">Welcome to the player expectation section of pix:e 🎉</h1>
      <p class="text-gray-500 dark:text-gray-400 mb-6">
        Research player expectations for your game. Two different approaches using two different
        datasets are available to explore: v1, and v2.
      </p>
    </section>

    <!-- Cards Section -->
    <section class="grid grid-cols-1 sm:grid-cols-2 gap-6">
      <UCard class="hover:shadow-lg transition">
        <template #header>
          <h2 class="font-semibold text-lg">
            <NuxtLink to="/player-expectations"> Dashboard (v1) </NuxtLink>
          </h2>
        </template>
        <p>Dashboard of Player Expections.</p>
      </UCard>
      <UCard class="hover:shadow-lg transition">
        <template #header>
          <h2 class="font-semibold text-lg">
            <NuxtLink to="/sentiments"> Sentiment Analysis (v1) </NuxtLink>
          </h2>
        </template>
        <p>Analyse extracted sentiment of the v1 dataset.</p>
      </UCard>
      <UCard class="hover:shadow-lg transition">
        <template #header>
          <h2 class="font-semibold text-lg">
            <NuxtLink to="/player-expectations-new/dashboard"> Dashboard (v2) </NuxtLink>
          </h2>
        </template>
        <p>
          Data-Driven insights into how player expectations differ across cultural contexts, genre
          conventions, and individual game titles.
        </p>
      </UCard>
      <UCard class="hover:shadow-lg transition">
        <template #header>
          <h2 class="font-semibold text-lg">
            <NuxtLink to="/player-expectations-new/dataset-explorer">
              Dataset Explorer (v2)
            </NuxtLink>
          </h2>
        </template>
        <p>
          Inspect individual Steam reviews and validate the extracted quote → aspect code →
          sentiment assignments within each review.
        </p>
      </UCard>
      <UCard class="hover:shadow-lg transition">
        <template #header>
          <h2 class="font-semibold text-lg">
            <NuxtLink to="/player-expectations-new/prior-findings"> Prior Findings (v2) </NuxtLink>
          </h2>
        </template>
        <p>
          Serves as a centralized catalog of selected findings (presented as direct quotes) from
          prior research on game review analysis
        </p>
      </UCard>
    </section>
  </UContainer>
</template>

<style scoped></style>
