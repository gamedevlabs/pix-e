<script setup lang="ts">
definePageMeta({
  middleware: ['authentication', 'project-context'],
  pageConfig: {
    type: 'project-required',
    showSidebar: true,
    title: 'PxKeys',
    icon: 'i-lucide-component',
    navGroup: 'main',
    navParent: 'player-experience',
    navOrder: 3,
    showInNav: true,
  },
})

const { items: pxKeys, fetchAll: fetchPxKeys } = usePxKeys()

onMounted(() => {
  fetchPxKeys()
})

function handleDelete(id: string) {
  const index = pxKeys.value.findIndex((pxkey) => pxkey.id === id)
  pxKeys.value.splice(index, 1)
}
</script>

<template>
  <div>
    <SimpleContentWrapper>
      <template #header>Px Keys</template>

      <SimpleCardSection>
        <div v-for="pxkey in pxKeys" :key="pxkey.id">
          <PxKeyCard visualization-style="detailed" :pxkey="pxkey" @delete="handleDelete" />
        </div>
      </SimpleCardSection>
    </SimpleContentWrapper>
  </div>
</template>
