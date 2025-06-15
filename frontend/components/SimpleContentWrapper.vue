<script setup lang="ts"></script>

<template>
  <div class="mb-8">
    <!-- Optional header slot -->
    <h1 v-if="$slots.header" class="text-2xl font-bold mb-4">
      <slot name="header" />
    </h1>

    <!-- Default main content -->
    <main>
      <slot />
    </main>
  </div>
</template>

<style scoped></style>
