<script setup lang="ts">
definePageMeta({
  middleware: 'authentication',
})

const { items: pxComponents, fetchAll: fetchPxComponents } = usePxComponents()

onMounted(() => {
  fetchPxComponents()
})

function handleDelete(id: string) {
  const index = pxComponents.value.findIndex((component) => component.id === id)
  pxComponents.value.splice(index, 1)
}
</script>

<template>
  <div class="p-8">
    <h1 class="text-2xl font-bold mb-6">Px Components</h1>

    <!-- Cards Section -->
    <section class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
      <div v-for="component in pxComponents" :key="component.id">
        <PxComponentCard
          visualization-style="detailed"
          :component="component"
          @delete="handleDelete"
        />
      </div>
    </section>
  </div>
</template>
