<script setup lang="ts">
const toast = useToast()

function showToast() {
  toast.add({
    title: 'Success',
    description: 'Your action was completed successfully.',
    color: 'success',
  })
}

showToast()
</script>

<template>
  <section>
    <p>This page will be displayed at the /about route.</p>
  </section>
</template>

<style scoped></style>
