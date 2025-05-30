<script setup lang="ts">
const props = defineProps<{
  node: PxNode
  components?: Array<PxComponent>
}>()

onMounted(() => {
  getComponents()
})

const { items: pxComponents, fetchAll: fetchPxComponents } = usePxComponents()

const associatedComponents = ref<Array<PxComponent>>([])

async function getComponents() {
  if (props.components) {
    associatedComponents.value = props.components
    return
  }
  await fetchPxComponents()
  associatedComponents.value = pxComponents.value.filter(
    (component) => component.node === props.node.id,
  )
}
</script>

<template>
  <PxNodeCardDetailed :node="node" :components="associatedComponents" />
</template>

<style scoped></style>
