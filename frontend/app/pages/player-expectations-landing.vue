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
      <p class="text-gray-500 dark:text-gray-400 mb-4">
        A data driven analytics platform that transforms unstructured Steam reviews into actionable
        player expectation insights.
      </p>

      <p class="text-gray-500 dark:text-gray-400 mb-6">
        Powered by a multi agent LLM pipeline, reviews are segmented into quotes, mapped to a three
        dimensional expectation framework consisting of Game Features, Game Aesthetics
        (experiential), and Pain Points, and enriched with fine grained sentiment analysis including
        implicit and sarcastic expressions. Building on an earlier prototype marked as Legacy, the
        current system introduces deeper conceptual modeling, cross language comparison, and an
        enhanced interactive interface, converting large scale player discourse into insights for
        both game studios and indie developers.
      </p>
    </section>

    <!-- Cards Section -->
    <section class="grid grid-cols-1 sm:grid-cols-2 gap-6">
      <UCard class="hover:shadow-lg transition">
        <template #header>
          <h2 class="font-semibold text-lg">
            <NuxtLink to="/player-expectations-new/dashboard"> Dashboard </NuxtLink>
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
            <NuxtLink to="/player-expectations-new/dataset-explorer"> Dataset Explorer </NuxtLink>
          </h2>
        </template>
        <p>
          Inspect individual Steam reviews and validate verify the full analytical chain from
          extracted quote to assigned aspect code and sentiment label within each review.
        </p>
      </UCard>
      <UCard class="hover:shadow-lg transition">
        <template #header>
          <h2 class="font-semibold text-lg">
            <NuxtLink to="/player-expectations-new/prior-findings"> Prior Findings </NuxtLink>
          </h2>
        </template>
        <p>
          A curated catalog of selected findings from prior large scale game review research,
          presented as direct quotes and mapped to various tags.
        </p>
      </UCard>
      <UCard class="hover:shadow-lg transition">
        <template #header>
          <h2 class="font-semibold text-lg">
            <NuxtLink to="/player-expectations"> Dashboard (legacy) </NuxtLink>
          </h2>
        </template>
        <p>
          A static interface that provides a high level overview of extracted player expectations
          and aspect level sentiment across the complete legacy dataset.
        </p>
      </UCard>
      <UCard class="hover:shadow-lg transition">
        <template #header>
          <h2 class="font-semibold text-lg">
            <NuxtLink to="/sentiments"> Sentiment Analysis (legacy) </NuxtLink>
          </h2>
        </template>
        <p>
          Analyze sentiment patterns within the Legacy dataset through an interactive interface that
          visualizes sentiment distribution and dominant aspects across reviews.
        </p>
      </UCard>
    </section>
  </UContainer>
</template>

<style scoped></style>
