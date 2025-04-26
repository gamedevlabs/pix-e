<script setup lang="ts">
const {
  componentDefs,
  nodes,
  createComponentDef,
  createNode,
  attachComponentToNode,
  getAttachedComponents,
  getComponentValue,
} = usePXGraph()

const newNodeName = ref('')
const newNodeDesc = ref('')
const newComponentName = ref('')
const newComponentType = ref<'number' | 'string' | 'boolean'>('number')

function addNode() {
  createNode(newNodeName.value, newNodeDesc.value)
  newNodeName.value = ''
  newNodeDesc.value = ''
}

function addComponent() {
  createComponentDef(newComponentName.value, newComponentType.value)
  newComponentName.value = ''
  newComponentType.value = 'number'
}
const boi = 'boi'
console.log(boi)

function attachToFirstNode(compId: string, value: unknown) {
  if (nodes.value.length > 0) {
    attachComponentToNode(nodes.value[0].id, compId, value)
  }
}
</script>

<template>
  <div>
    <h2>New PXNode</h2>
    <input v-model="newNodeName" placeholder="Name" />
    <input v-model="newNodeDesc" placeholder="Description" />
    <UButton @click="addNode">Create</UButton>

    <h2>New PXComponent</h2>
    <input v-model="newComponentName" placeholder="Component name" />
    <select v-model="newComponentType">
      <option value="number">Number</option>
      <option value="string">String</option>
      <option value="boolean">Boolean</option>
    </select>
    <UButton @click="addComponent">Create</UButton>

    <h2>Components</h2>
    <ul>
      <li v-for="comp in componentDefs" :key="comp.id">
        {{ comp.name }} ({{ comp.type }})
        <UButton @click="attachToFirstNode(comp.id, comp.type === 'number' ? 42 : 'default')">
          Attach to first node with example value
        </UButton>
      </li>
    </ul>

    <h2>PXNodes</h2>
    <ul>
      <li v-for="node in nodes" :key="node.id">
        <strong>{{ node.name }}</strong> - {{ node.description }}
        <ul>
          <li v-for="comp in getAttachedComponents(node)" :key="comp.id">
            {{ comp.name }} = {{ getComponentValue(node, comp.id) }}
          </li>
        </ul>
      </li>
    </ul>
  </div>
</template>
