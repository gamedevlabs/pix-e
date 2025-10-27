<script setup lang="ts">
definePageMeta({
  middleware: 'authentication',
});

</script>

<template>
    <div class="p-8">
    <h1 class="text-2xl font-bold mb-6">Movie Script Evaluator</h1>

    <div class="movie-script-evaluator-container mb-8" style="display:flex; flex-direction: row;">
        <div class="mb-4">
            <h2 class="text-xl font-semibold mb-2">Uploaded Movie Script</h2>
        </div>
        <div class="mb-4">
            <h3>List of the Existing Assets</h3>
            <AssetsList :assets="[{
                name: 'Sample Movie Script',
                className: 'application/pdf',
                path: '1.5 MB'
            },
            {
                name: 'Sample Movie Script 2',
                class_name: 'application/pdf',
                path: '1.5 MB'
            }]" />
        </div>
    </div>

    <!-- Add your movie script evaluator components and logic here -->
     
    </div>
</template>

<style scoped>
.mb-4 {
  width: 50%;
}
</style>