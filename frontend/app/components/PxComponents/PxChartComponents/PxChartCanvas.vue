<script setup lang="ts">
import {
  type NodeDragEvent,
  VueFlow,
  useVueFlow,
  Panel,
  type Connection,
  type EdgeChange,
  type NodeChange,
  type Node,
  type NodeSelectionChange,
} from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { PxChartEdge, PxChartSettingsForm, PxLockEditForm } from '#components'
const config = useRuntimeConfig()

const emit = defineEmits<{
  (e: 'containerAdded' | 'edgeConnected' | 'nodeAddedToContainer'): void
}>()

const { screenToFlowCoordinate, _onPaneReady, getSelectedEdges } = useVueFlow()

const props = defineProps({ chartId: { type: String, default: -1 } })

const chartId = props.chartId
const BASE_URL = config.public.apiBase + '/api'
const { success: successToast, error: errorToast } = usePixeToast()

const { items: pxNodes, fetchAll: fetchPxNodes } = usePxNodes()
const { items: pxComponents, fetchAll: fetchPxComponents } = usePxComponents()
const { items: pxComponentDefinitions, fetchAll: fetchPxComponentDefinitions } =
  usePxComponentDefinitions()

const { items: pxChartEdges, fetchAll: fetchPxChartEdges } = usePxChartEdges(props.chartId)

const { items: pxChartContainers, fetchAll: fetchPxChartContainers } = usePxChartContainers(
  props.chartId,
)

const { loadChartSettingsForUser, settings } = usePxChartSettings(props.chartId)

const {
  nodes,
  edges,
  error,
  pxChartError,
  loadGraph,
  addContainer,
  updateContainer,
  applyDefaultNodeChanges,
  addNodeToContainer,
  removeNodeFromContainer,
  deleteContainer,
  addEdge,
  applyDefaultEdgeChanges,
  deleteEdge,
  updateLocksOnEdge,
} = usePxChartsCanvasApi(chartId)

const {
  result,
  calculatePathFromSelection,
  resetPathCalculation,
  updateNodeStyling,
  updateEdgeStyling,
} = usePxChartPathCalculation(nodes, edges, settings)

const overlay = useOverlay()
const lockModal = overlay.create(PxLockEditForm)
const settingsModal = overlay.create(PxChartSettingsForm)

const edgeTypes = {
  pxGraph: markRaw(PxChartEdge),
}

// Selected node for context strategy panel
const selectedNodeForAnalysis = ref<{
  nodeId: string
  containerId: string
  nodeName: string
} | null>(null)
const showStrategyPanel = ref(false)
const precomputeLoading = ref(false)
const precomputeStrategy = ref('structural_memory')
const precomputeScope = ref('all')
const precomputeScopeOptions = [
  { value: 'global', label: 'Global Setup' },
  { value: 'node', label: 'Node Setup' },
  { value: 'all', label: 'All Setup' },
]
const precomputeStrategyOptions = [
  { value: 'structural_memory', label: 'Structural Memory' },
  { value: 'simple_sm', label: 'SM-Lite (facts + triples)' },
  { value: 'hierarchical_graph', label: 'H-Graph' },
  { value: 'hmem', label: 'H-MEM' },
  { value: 'combined', label: 'Combined' },
  { value: 'full_context', label: 'Full Context' },
]
const strategiesNeedingNode = new Set(['hmem', 'combined'])

function handleNodeClick(event: { node: Node }) {
  const container = event.node.data as PxChartContainer
  if (container?.content) {
    selectedNodeForAnalysis.value = {
      nodeId: container.content,
      containerId: container.id,
      nodeName: container.name || 'Unknown',
    }
  }
}

function openStrategyPanel() {
  if (selectedNodeForAnalysis.value) {
    showStrategyPanel.value = true
  }
}

function closeStrategyPanel() {
  showStrategyPanel.value = false
}

async function handlePrecomputeArtifacts() {
  if (precomputeLoading.value) return
  if (
    precomputeScope.value !== 'global' &&
    strategiesNeedingNode.has(precomputeStrategy.value) &&
    !selectedNodeForAnalysis.value
  ) {
    errorToast('Select a node before precomputing this strategy.')
    return
  }
  precomputeLoading.value = true

  try {
    const payload: Record<string, string> = {
      chart_id: chartId,
      strategy: precomputeStrategy.value,
      scope: precomputeScope.value,
    }
    if (selectedNodeForAnalysis.value?.nodeId) {
      payload.node_id = selectedNodeForAnalysis.value.nodeId
    }

    await $fetch(`${BASE_URL}/context/precompute/`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'X-CSRFToken': useCookie('csrftoken').value,
      } as HeadersInit,
      body: payload,
    })

    successToast('Precompute complete for this chart.')
  } catch (err) {
    errorToast(err)
  } finally {
    precomputeLoading.value = false
  }
}

async function handleResetArtifacts() {
  const confirmed = window.confirm('Clear cached artifacts for this chart?')
  if (!confirmed) return

  try {
    await $fetch(`${BASE_URL}/context/precompute/reset/`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'X-CSRFToken': useCookie('csrftoken').value,
      } as HeadersInit,
      body: {
        chart_id: chartId,
        scope: precomputeScope.value,
      },
    })
    successToast('Artifact cache cleared.')
  } catch (err) {
    errorToast(err)
  }
}

onMounted(() => {
  loadGraph()
  fetchPxNodes()
  fetchPxComponents()
  fetchPxComponentDefinitions()
  fetchPxChartContainers()
  fetchPxChartEdges()
  loadChartSettingsForUser()
})

async function onNodeDragStop(event: NodeDragEvent) {
  for (const node of event.nodes) {
    await updateContainer({
      id: node.id,
      layout: {
        position_x: node.position.x,
        position_y: node.position.y,
        width: node.width as number,
        height: node.height as number,
      },
    })
  }
}

async function onConnect(connection: Connection) {
  await addEdge(connection)
  emit('edgeConnected')
  fetchPxChartEdges()
  updatePath()
}

async function handleDeletePxGraphContainer(containerId: string) {
  await deleteContainer(containerId, true)
  fetchPxChartContainers()
  removeFromSelected(containerId)
}

async function handleUpdatePxGraphContainer(updatedPxChartContainer: Partial<PxChartContainer>) {
  await updateContainer(updatedPxChartContainer)
  fetchPxChartContainers()
}

async function handleAddPxNode(pxGraphContainerId: string, pxNodeId: string) {
  await addNodeToContainer(pxGraphContainerId, pxNodeId)
  emit('nodeAddedToContainer')
  fetchPxNodes()
  fetchPxChartContainers()
}

async function handleDeletePxNode(pxGraphContainerId: string) {
  await removeNodeFromContainer(pxGraphContainerId)
  fetchPxNodes()
  fetchPxChartContainers()
}

// We disabled the automatic behavior of Vue Flow, therefore, we need to handle all
// changes either ourselves, or let Vue Flow handle them explicitly
async function onNodesChange(changes: NodeChange[]) {
  const defaultChanges: NodeChange[] = []
  for (const change of changes) {
    switch (change.type) {
      // Adding nodes is already handled in addNode
      case 'add':
        break
      case 'remove':
        await deleteContainer(change.id)
        break
      case 'position':
        if (change.dragging) {
          defaultChanges.push(change)
        }
        break
      case 'dimensions':
        defaultChanges.push(change)
        break
      case 'select':
        defaultChanges.push(change)
        await onNodeSelectionChange(change)
        break
    }
  }

  applyDefaultNodeChanges(defaultChanges)
}

async function onEdgesChange(changes: EdgeChange[]) {
  const defaultChanges: EdgeChange[] = []
  for (const change of changes) {
    switch (change.type) {
      // Handled in onConnect
      case 'add':
        break
      case 'select':
        defaultChanges.push(change)
        break
      case 'remove':
        await deleteEdge(change.id)
        break
    }
  }

  applyDefaultEdgeChanges(defaultChanges)
}

async function onContextMenu(mouseEvent: MouseEvent) {
  // prevent the browser's default menu
  mouseEvent.preventDefault()
  // for now, just create a container
  const pos = screenToFlowCoordinate({ x: mouseEvent.x, y: mouseEvent.y })
  await addContainer(pos.x, pos.y)
  emit('containerAdded')
  fetchPxChartContainers()
}

async function handleAddContainerFromPanel() {
  await addContainer(0, 0)
  emit('containerAdded')
}

const pxNodeIdsInPath = computed(() => {
  const nodes: Array<string | null> = []
  result.value.pathNodes.forEach((containerId) => {
    const container = pxChartContainers.value.find((container) => container.id === containerId)
    if (container) {
      nodes.push(container.content)
    }
  })
  return nodes
})

const pxNodesInChart = computed(() => {
  const ids = nodes.value.map((vueNode) => vueNode.data.content)
  return pxNodes.value.filter((pxN) => ids.includes(pxN.id))
})

async function updatePath() {
  if (selectedNodesInOrder.value.length >= 2) {
    await calculatePathFromSelection(selectedNodesInOrder.value)
    await updateNodeStyling()
    await updateEdgeStyling()
  }
}

const selectedNodesInOrder: Ref<string[]> = ref([])

async function removeFromSelected(idToRemove: string) {
  selectedNodesInOrder.value = selectedNodesInOrder.value.filter((id) => id != idToRemove)
}

async function onNodeSelectionChange(change: NodeSelectionChange) {
  // update record of selected nodes
  if (change.selected) {
    selectedNodesInOrder.value.push(change.id)
  } else {
    removeFromSelected(change.id)
  }

  // update path based on current selection
  if (selectedNodesInOrder.value.length >= 2) {
    await calculatePathFromSelection(selectedNodesInOrder.value)
  } else {
    await resetPathCalculation()
  }
  await updateNodeStyling()
  await updateEdgeStyling()
}

async function handleEditLocks() {
  if (!getSelectedEdges.value.length) return

  const selectedEdge = getSelectedEdges.value[0]!
  const pxChartEdge = pxChartEdges.value.find((pxEdge) => pxEdge.id === selectedEdge.id)!

  await lockModal
    .open({ selectedEdge: pxChartEdge, chartId: chartId }).result
    .then(async (edgeId) => await updateLocksOnEdge(edgeId))
}

async function handleEditSettings() {
  console.log(`Old PxChartPathSettings: ${JSON.stringify(settings.value)}`)
  const { _newSettings } = await settingsModal.open({ chartId: chartId, settings: settings.value })
    .result
  await loadChartSettingsForUser()
  console.log(`New PxChartPathSettings: ${JSON.stringify(settings.value)}`)
}
</script>

<template>
  <PxDiagrams
    :nodes-in-path="pxNodeIdsInPath"
    :px-nodes="pxNodesInChart"
    :px-components="pxComponents"
    :px-component-definitions="pxComponentDefinitions"
  />
  <div v-if="pxChartError">
    <div v-if="pxChartError.response?.status === 403">You do not have access to this graph.</div>
    <div v-if="pxChartError.response?.status === 404">This graph does not exist.</div>
  </div>
  <VueFlow
    v-else
    v-model:nodes="nodes"
    v-model:edges="edges"
    class="max-h-full"
    :edge-types="edgeTypes"
    :apply-default="false"
    @node-drag-stop="onNodeDragStop"
    @connect="onConnect"
    @nodes-change="onNodesChange"
    @edges-change="onEdgesChange"
    @pane-context-menu="onContextMenu($event)"
    @node-click="handleNodeClick"
  >
    <!--@nodes-initialized="fitView()"-->

    <Background />

    <template #node-pxEmpty="customNodeProps">
      <PxChartContainer
        v-bind="customNodeProps"
        @delete="handleDeletePxGraphContainer"
        @add-px-node="
          (containerId, nodeId) => {
            handleAddPxNode(containerId, nodeId)
          }
        "
        @edit="handleUpdatePxGraphContainer"
      />
    </template>

    <template #node-pxNode="customNodeProps">
      <PxChartContainerNode
        v-bind="customNodeProps"
        @remove-px-node="handleDeletePxNode"
        @delete="handleDeletePxGraphContainer"
        @edit="handleUpdatePxGraphContainer"
      />
    </template>

    <Panel :position="'top-left'">
      <UTooltip text="Create Node" :content="{ align: 'center', side: 'right' }">
        <UButton
          size="xl"
          icon="i-lucide-plus"
          color="primary"
          @click="handleAddContainerFromPanel"
        />
      </UTooltip>
      <UTooltip
        v-if="getSelectedEdges.length === 1"
        text="Add or Edit Locks"
        :content="{ align: 'center', side: 'right' }"
      >
        <UButton size="xl" icon="i-lucide-lock" color="primary" @click="handleEditLocks" />
      </UTooltip>
      <UTooltip text="Edit Settings" :content="{ align: 'center', side: 'right' }">
        <UButton size="xl" icon="i-lucide-settings" color="primary" @click="handleEditSettings" />
      </UTooltip>
    </Panel>

    <!-- Context Strategy Analysis Button -->
    <Panel :position="'top-right'">
      <div class="flex flex-col items-end gap-2">
        <div class="flex items-center gap-2">
          <USelect
            v-model="precomputeScope"
            :items="precomputeScopeOptions"
            value-key="value"
            label-key="label"
            size="sm"
            :disabled="true"
          />
          <USelect
            v-model="precomputeStrategy"
            :items="precomputeStrategyOptions"
            value-key="value"
            label-key="label"
            size="sm"
            :disabled="true"
          />
          <UButton
            size="sm"
            icon="i-heroicons-cog-6-tooth"
            color="primary"
            :loading="precomputeLoading"
            :disabled="true"
            @click="handlePrecomputeArtifacts"
          >
            Precompute Artifacts
          </UButton>
          <UButton
            size="sm"
            icon="i-heroicons-trash"
            color="error"
            variant="outline"
            :disabled="true"
            @click="handleResetArtifacts"
          >
            Reset Cache
          </UButton>
        </div>
        <UTooltip
          :text="selectedNodeForAnalysis ? 'Analyze Node Context' : 'Select a node first'"
          :content="{ align: 'center', side: 'left' }"
        >
          <UButton
            size="lg"
            icon="i-heroicons-cpu-chip"
            color="warning"
            :disabled="!selectedNodeForAnalysis || true"
            @click="openStrategyPanel"
          >
            Context Analysis
          </UButton>
        </UTooltip>
        <div v-if="selectedNodeForAnalysis" class="text-xs text-gray-600 dark:text-gray-400">
          Selected: {{ selectedNodeForAnalysis.nodeName }}
        </div>
      </div>
    </Panel>
  </VueFlow>

  <!-- Context Strategy Slideover -->
  <USlideover v-model:open="showStrategyPanel" :ui="{ width: 'max-w-lg' }">
    <template #title>
      <div class="flex items-center gap-2">
        <UIcon name="i-heroicons-cpu-chip" />
        Context Strategy Analysis
      </div>
    </template>

    <template #body>
      <ContextStrategyPanel
        v-if="selectedNodeForAnalysis"
        :chart-id="chartId"
        :node-id="selectedNodeForAnalysis.nodeId"
        :node-name="selectedNodeForAnalysis.nodeName"
      />
    </template>

    <template #footer>
      <UButton color="neutral" variant="outline" @click="closeStrategyPanel"> Close </UButton>
    </template>
  </USlideover>

  <div v-if="error" style="color: red; margin-top: 1rem">
    {{ error }}
  </div>
</template>

<style scoped></style>
