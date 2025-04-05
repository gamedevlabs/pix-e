<script setup lang="ts">
const toast = useToast()

function showToast() {
  toast.add({
    title: 'Success',
    description: 'Your action was completed successfully.',
    color: 'success',
  })
}

const colorMode = useColorMode()

function switchColorMode() {
  colorMode.preference = colorMode.value === 'dark' ? 'light' : 'dark'
}
</script>

<template>
  <UContainer class="py-10 space-y-10">
    <!-- Nav Bar -->
    <header
      class="flex items-center justify-between py-4 border-b border-gray-200 dark:border-gray-800"
    >
      <div class="text-xl font-bold">Nuxt UI Demo</div>
      <div class="flex items-center gap-4">
        <UButton color="secondary" variant="ghost" to="/">Home</UButton>
        <UButton color="secondary" variant="ghost" to="/about">About</UButton>
        <UButton
          color="neutral"
          variant="ghost"
          icon="{colorMode.value === 'dark' ? 'i-heroicons-sun' : 'i-heroicons-moon'}"
          @click="switchColorMode"
        />
      </div>
    </header>

    <!-- Hero Section -->
    <section class="text-center">
      <h1 class="text-4xl font-bold mb-4">Welcome to Nuxt UI 🎉</h1>
      <p class="text-gray-500 dark:text-gray-400 mb-6">
        Clean, composable, and styled out of the box with Nuxt UI.
      </p>
      <UButton size="lg" color="primary" @click="showToast">Get Started</UButton>
    </section>

    <!-- Cards Section -->
    <section class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      <UCard v-for="n in 3" :key="n" class="hover:shadow-lg transition">
        <template #header>
          <h2 class="font-semibold text-lg">Card Title {{ n }}</h2>
        </template>
        <p>This is some content inside card {{ n }}. You can use this section for anything.</p>
        <template #footer>
          <UButton color="neutral" variant="soft">Read more</UButton>
        </template>
      </UCard>
    </section>

    <!-- Footer -->
    <footer
      class="border-t pt-6 border-gray-200 dark:border-gray-800 text-center text-sm text-gray-500 dark:text-gray-400"
    >
      © 2025 Nuxt UI Example. Built with ❤️
    </footer>
  </UContainer>
</template>

<style scoped></style>
