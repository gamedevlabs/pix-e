<!-- components/ChartCard.vue -->
<template>
  <div class="bg-card-background p-6 rounded-lg shadow-lg border border-border">
    <h2 class="text-xl font-semibold mb-2 text-primary">{{ title }}</h2>
    <slot />
  </div>
</template>

<script setup>
defineProps({
  title: String,
})
</script>
