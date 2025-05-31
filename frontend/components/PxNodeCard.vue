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

async function updateComponents() {
  await fetchPxComponents()
  console.log('hehe')
  associatedComponents.value = pxComponents.value.filter(
    (component) => component.node === props.node.id,
  )
  console.log(associatedComponents.value.length)
}

async function handleDeleteComponent(id: number) {
  const index = associatedComponents.value!.findIndex((component) => component.id === id)
  if (index > -1) {
    associatedComponents.value!.splice(index, 1)
  }
}
</script>

<template>
  <div v-if="errorPxComponents">Error loading Px Node {{ node.name }}</div>
  <PxNodeCardDetailed
    v-else-if="associatedComponents"
    :node="node"
    :components="associatedComponents"
    @delete-component="handleDeleteComponent"
    @add-component="updateComponents"
  />
  <div v-else-if="loadingPxComponents">Loading PxNode {{ node.name }}</div>
</template>

<style scoped></style>
