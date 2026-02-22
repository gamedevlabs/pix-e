<script setup lang="ts">
definePageMeta({
  middleware: ['authentication', 'project-context'],
  pageConfig: {
    type: 'project-required',
    showSidebar: true,
    title: 'Nodes',
    icon: 'i-lucide-hexagon',
    navGroup: 'main',
    navParent: 'player-experience',
    navOrder: 2,
    showInNav: true,
  },
})

const {
  items: pxNodes,
  fetchAll: fetchPxNodes,
  createItem: createPxNode,
  deleteItem: deletePxNode,
} = usePxNodes()

const { currentProject } = useProjectHandler()
const { toggleSubstep, loadForProject } = useProjectWorkflow()
if (currentProject.value?.id) {
  await loadForProject(currentProject.value.id)
}

onMounted(() => {
  fetchPxNodes()
})

const newItem = ref<NamedEntity | null>(null)

function addItem() {
  newItem.value = { name: '', description: '' }
}

async function createItem(newEntityDraft: Partial<NamedEntity>) {
  await createPxNode({ ...newEntityDraft })
  // px-2-2: "Create your first node"
  await toggleSubstep('px-2', 'px-2-2')
  newItem.value = null
}

// Not particularly efficient, but works for now.
// Problem is that I do not get the specified PxNodeCard to reload its components from here
async function handleForeignAddComponent() {
  pxNodes.value = []
  await fetchPxNodes()
}

async function handleAddComponent() {
  // px-2-3: "Add a component to your new node"
  await toggleSubstep('px-2', 'px-2-3')
}
</script>

<template>
  <div>
    <SimpleContentWrapper>
      <template #header>Px Nodes</template>

      <SimpleCardSection use-add-button @add-clicked="addItem">
        <div v-for="node in pxNodes" :key="node.id">
          <PxNodeCard
            :key="node.id"
            :node-id="node.id"
            :visualization-style="'detailed'"
            @delete="deletePxNode"
            @add-foreign-component="handleForeignAddComponent"
            @add-component="handleAddComponent"
          />
        </div>
        <div v-if="newItem">
          <NamedEntityCard
            :named-entity="newItem"
            :is-being-edited="true"
            @edit="newItem = null"
            @update="createItem"
            @delete="newItem = null"
          />
        </div>
      </SimpleCardSection>
    </SimpleContentWrapper>
  </div>
</template>
