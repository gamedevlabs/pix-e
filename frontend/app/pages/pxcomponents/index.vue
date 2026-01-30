<script setup lang="ts">
definePageMeta({
  middleware: ['authentication', 'project-context'],
  pageConfig: {
    type: 'project-required',
    showSidebar: true,
    title: 'Components',
    icon: 'i-lucide-component',
    navGroup: 'main',
    navParent: 'player-experience',
    navOrder: 3,
    showInNav: true,
  },
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

      <SimpleCardSection>
        <div v-for="component in pxComponents" :key="component.id">
          <PxComponentCard
            visualization-style="detailed"
            :component="component"
            @delete="handleDelete"
          />
        </div>
      </SimpleCardSection>
    </SimpleContentWrapper>
  </div>
</template>
