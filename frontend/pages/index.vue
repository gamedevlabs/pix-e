<script setup lang="ts"></script>

<template>
  <UContainer class="py-10 space-y-10">    <!-- Hero Section -->
    <section class="text-center">
      <h1 class="text-4xl font-bold mb-4">Welcome to pix:e 🎉</h1>
      <p class="text-gray-500 dark:text-gray-400 mb-6">Design your game with research.</p>
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
        <!--
        <template #footer>
          <UButton color="neutral" variant="soft">Read more</UButton>
        </template>
        -->
      </UCard>
      <UCard class="hover:shadow-lg transition">
        <template #header>
          <h2 class="font-semibold text-lg">LLM supported Design Pillars</h2>
        </template>
        <p>
          The tool has design pillar functionality, that is validated and cross-checked by the help
          of LLMs to make sure your design stays consistent.
        </p>
        <!--
        <template #footer>
          <UButton color="neutral" variant="soft">Read more</UButton>
        </template>
        -->
      </UCard>
      <UCard class="hover:shadow-lg transition">
        <template #header>
          <h2 class="font-semibold text-lg">Moodboard Generation</h2>
        </template>
        <p>
          Through multimodal LLMs, you can design your moodboard directly in the app by describing
          and interaction with the tool.
        </p>
        <!--
        <template #footer>
          <UButton color="neutral" variant="soft">Read more</UButton>
        </template>
        -->
      </UCard>
    </section>
  </UContainer>
</template>

<style scoped></style>
