<!-- components/ChartCard.vue -->
<template>
  <div class="bg-white shadow rounded-2xl p-4">
    <h2 class="text-xl font-semibold mb-2">{{ title }}</h2>
    <slot />
  </div>
</template>

<script setup>
defineProps({
  title: String
})
</script>
