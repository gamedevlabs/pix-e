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
  <div>
    <SimpleContentWrapper>
      <template #header>Px Components</template>

      <PxCardSection>
        <div v-for="component in pxComponents" :key="component.id">
          <PxComponentCard
            visualization-style="detailed"
            :component="component"
            @delete="handleDelete"
          />
        </div>
      </PxCardSection>
    </SimpleContentWrapper>
  </div>
</template>
