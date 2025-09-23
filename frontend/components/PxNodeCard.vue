<script setup lang="ts">
import PxNodeCardPreview from '~/components/PxNodeCardPreview.vue'

const props = defineProps({
  node: {
    type: Object as PropType<PxNode>,
    required: true,
  },
  components: {
    type: Array as PropType<Array<PxComponent>>,
    default: null,
  },
  visualizationStyle: {
    type: String as PropType<'preview' | 'detailed'>,
    default: 'detailed',
  },
})

onMounted(() => {
  getComponents()
})

const {
  items: pxComponents,
  fetchAll: fetchPxComponents,
  loading: loadingPxComponents,
  error: errorPxComponents,
} = usePxComponents()

const emit = defineEmits<{
  (e: 'addForeignComponent', id: string): void
}>()

const associatedComponents = ref<Array<PxComponent> | undefined>(props.components)

async function getComponents() {
  if (associatedComponents.value || props.visualizationStyle === 'preview') {
    return
  }
  await fetchPxComponents()
  associatedComponents.value = pxComponents.value.filter(
    (component) => component.node === props.node.id,
  )
}

async function updateComponents(id: string) {
  if (id !== props.node.id) {
    emit('addForeignComponent', id)
    return
  }
  await fetchPxComponents()
  associatedComponents.value = pxComponents.value.filter(
    (component) => component.node === props.node.id,
  )
}

async function handleDeleteComponent(id: string) {
  const index = associatedComponents.value!.findIndex((component) => component.id === id)
  if (index > -1) {
    associatedComponents.value!.splice(index, 1)
  }
}
</script>

<template>
  <div v-if="errorPxComponents">Error loading Px Node {{ node.name }}</div>
  <PxNodeCardPreview v-else-if="visualizationStyle === 'preview'" :node="node" />
  <PxNodeCardDetailed
    v-else-if="associatedComponents && visualizationStyle === 'detailed'"
    :node="node"
    :components="associatedComponents"
    @delete-component="handleDeleteComponent"
    @add-component="updateComponents"
  />
  <div v-else-if="loadingPxComponents">Loading PxNode {{ node.name }}</div>
</template>

<style scoped></style>
