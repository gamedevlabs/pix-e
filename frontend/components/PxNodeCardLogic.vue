<script setup lang="ts">
const props = defineProps<{
  node: PxNode
  components?: Array<PxComponent>
}>()

onMounted(() => {
  getComponents()
})

const {
  items: pxComponents,
  fetchAll: fetchPxComponents,
  loading: loadingPxComponents,
  error: errorPxComponents,
} = usePxComponents()

const associatedComponents = ref<Array<PxComponent> | undefined>(props.components)

async function getComponents() {
  if (associatedComponents.value) {
    return
  }
  await fetchPxComponents()
  associatedComponents.value = pxComponents.value.filter(
    (component) => component.node === props.node.id,
  )
}
</script>

<template>
  <div v-if="errorPxComponents">Error loading Px Node {{ node.name }}</div>
  <PxNodeCardDetailed
    v-else-if="associatedComponents"
    :node="node"
    :components="associatedComponents"
  />
  <div v-else-if="loadingPxComponents">Loading PxNode {{ node.name }}</div>
</template>

<style scoped></style>
