<script setup lang="ts">
import { PxComponentCreationForm, PxNodeFixModal } from '#components'
import PxKeyCreationForm from './PxLockKeyComponents/PxKeyCreationForm.vue'
import type { ContextMenuItem } from '#ui/components/ContextMenu.vue'

const props = defineProps<{
  node: PxNode
  isCollapsible: boolean
}>()

const emit = defineEmits<{
  (e: 'update', updatedNode: PxNode): void
  (e: 'delete', nodeId: string): void
  (
    e: 'deleteComponent' | 'addComponent' | 'deleteKey' | 'addKey',
    nodeId: string,
    componentId: string,
  ): void
  (e: 'switchNode'): void
}>()

const isCollapsed = ref(true)
const isBeingEdited = ref(false)
const toast = useToast()
const pxNodesLLM = usePxNodesLLM()

const overlay = useOverlay()
const modal = overlay.create(PxComponentCreationForm)
const keyModal = overlay.create(PxKeyCreationForm)

const editForm = ref({
  name: props.node.name,
  description: props.node.description,
})

const menuItems = ref<ContextMenuItem[]>([
  {
    label: 'Add component',
    onSelect() {
      handleAddComponent()
    },
  },
  {
    type: 'separator' as const,
  },
  {
    label: 'Switch node',
    onSelect() {
      handleSwitchNode()
    },
  },
  {
    label: 'Edit node',
    onSelect() {
      startEdit()
    },
  },
  {
    type: 'separator' as const,
  },
  {
    label: 'Delete node',
    onSelect() {
      emitDelete()
    },
  },
])

// LLM Feedback state
const llmFeedback = ref<NodeValidationFeedback | null>(null)
const isValidating = ref(false)

async function toggleCollapsed() {
  isCollapsed.value = !isCollapsed.value
}

function onDbClick() {
  if (!isBeingEdited.value && !llmFeedback.value) {
    startEdit()
  }
}

function startEdit() {
  editForm.value = { ...props.node }
  isBeingEdited.value = true
  isCollapsed.value = false
}

function confirmEdit() {
  isBeingEdited.value = false
  emit('update', { ...props.node, ...editForm.value })
}

function cancelEdit() {
  isBeingEdited.value = !isBeingEdited.value
  editForm.value.name = props.node.name
  editForm.value.description = props.node.description
}

function emitDelete() {
  emit('delete', props.node.id)
}

function handleDeleteComponent(componentId: string) {
  emit('deleteComponent', props.node.id, componentId)
}

async function handleAddComponent() {
  const result = (await modal.open({ selectedNodeId: props.node.id }).result) as {
    nodeId: string
    componentId: string
  }

  emit('addComponent', result.nodeId, result.componentId)
}

async function handleSwitchNode() {
  emit('switchNode')
}

// LLM Validation
async function handleValidation() {
  isValidating.value = true
  try {
    const result = await pxNodesLLM.validateNode(props.node.id)
    llmFeedback.value = result
    if (result?.has_issues) {
      toast.add({
        title: 'Coherence Issues Found',
        description: `Found ${result.issues.length} issues. Score: ${result.overall_coherence_score}/10`,
        color: 'warning',
      })
    } else {
      toast.add({
        title: 'Node is Coherent',
        description: `Coherence score: ${result?.overall_coherence_score}/10`,
        color: 'success',
      })
    }
  } finally {
    isValidating.value = false
  }
}

function dismissIssue(index: number) {
  if (llmFeedback.value?.issues) {
    llmFeedback.value.issues.splice(index, 1)
    if (llmFeedback.value.issues.length === 0) {
      llmFeedback.value.has_issues = false
    }
  }
}

async function openFixModal() {
  const fixModal = overlay.create(PxNodeFixModal, {
    props: {
      originalNode: props.node,
      validationIssues: llmFeedback.value?.issues ?? [],
      onClose: () => fixModal.close(),
      onAccepted: (updatedNode: PxNode) => {
        emit('update', updatedNode)
        fixModal.close()
        // Clear feedback after accepting fix
        llmFeedback.value = null
        toast.add({
          title: 'Node Updated',
          description: 'The AI improvement has been applied.',
          color: 'success',
        })
      },
    },
  })
  fixModal.open()
}

function handleDeleteKey(keyId: string) {
  emit('deleteKey', props.node.id, keyId)
}

async function handleAddKey() {
  const { nodeId, keyId } = await keyModal.open({ selectedNodeId: props.node.id }).result

  emit('addKey', nodeId, keyId)
}
</script>

<template>
  <UContextMenu :items="menuItems" :disabled="!!(isBeingEdited || llmFeedback || !isCollapsible)">
    <UCard class="hover:shadow-lg transition" @dblclick.stop="onDbClick()">
      <template #header>
        <h2 v-if="!isBeingEdited" class="font-semibold text-lg">
          <NuxtLink :to="{ name: 'pxnodes-id', params: { id: props.node.id } }">
            {{ props.node.name }}
          </NuxtLink>
        </h2>
        <UTextarea v-else v-model="editForm.name" />
      </template>

      <template #default>
        <div v-if="!isBeingEdited">
          <h2 class="font-semibold text-lg mb-2">Description</h2>
          <p>{{ props.node.description }}</p>
          <USeparator class="mt-6" />
          <br />
          <h2 v-if="node.components.length === 0" class="italic">This node has no components.</h2>
          <h2 v-else class="font-semibold text-lg mb-2">Components</h2>
          <section class="flex flex-wrap gap-4">
            <div
              v-for="component in node.components"
              :key="component.id"
              @dblclick="$event.stopPropagation()"
            >
              <PxComponentCard
                visualization-style="preview"
                :component="component"
                @delete="handleDeleteComponent"
              />
            </div>
          </section>
          <USeparator class="mt-6" />
          <br />
          <h2 v-if="node.keys.length === 0" class="italic">This node has no keys.</h2>
          <h2 v-else class="font-semibold text-lg mb-2">Keys</h2>
          <section class="flex flex-wrap gap-4">
            <div v-for="pxKey in node.keys" :key="pxKey.id">
              <PxKeyCard visualization-style="preview" :pxkey="pxKey" @delete="handleDeleteKey" />
            </div>
          </section>
          <USeparator class="mt-6" />
          <br />
          <h2 v-if="node.charts.length === 0" class="italic">
            This node is not associated to any charts.
          </h2>
          <div v-else>
            <h2 class="font-semibold text-lg mb-2">Associated Charts</h2>
            <section class="grid grid-cols-1 gap-6">
              <div v-for="chart in node.charts" :key="chart.id">
                <PxChartCard :px-chart="chart" :visualization-style="'preview'" />
              </div>
            </section>
          </div>

          <!-- LLM Feedback Section -->
          <div v-if="llmFeedback" class="mt-6 pt-4 border-t">
            <!-- Coherence Score -->
            <div class="mb-3">
              <div class="flex items-center gap-2 mb-2">
                <span class="text-sm text-gray-600 dark:text-gray-400">Coherence Score:</span>
                <UBadge
                  :color="
                    llmFeedback.overall_coherence_score >= 7
                      ? 'success'
                      : llmFeedback.overall_coherence_score >= 4
                        ? 'warning'
                        : 'error'
                  "
                  variant="solid"
                >
                  {{ llmFeedback.overall_coherence_score }}/10
                </UBadge>
              </div>
              <p class="text-sm text-gray-600 dark:text-gray-300">{{ llmFeedback.summary }}</p>
            </div>

            <!-- Show issues list -->
            <div v-for="(issue, index) in llmFeedback?.issues" :key="index">
              <UAlert
                class="mb-2"
                variant="subtle"
                :color="issue.severity >= 3 ? 'error' : 'warning'"
                :title="issue.title"
                :description="`${issue.description} (Severity: ${issue.severity})`"
                :actions="[
                  {
                    label: 'Dismiss',
                    color: 'warning',
                    variant: 'subtle',
                    class: 'ml-auto',
                    onClick: () => dismissIssue(index),
                  },
                ]"
              />
              <!-- Related components -->
              <div
                v-if="issue.related_components.length > 0"
                class="ml-4 mb-2 flex flex-wrap gap-1"
              >
                <span class="text-xs text-gray-500">Related components:</span>
                <UBadge
                  v-for="comp in issue.related_components"
                  :key="comp"
                  color="neutral"
                  variant="subtle"
                  size="xs"
                >
                  {{ comp }}
                </UBadge>
              </div>
            </div>

            <!-- Single "Fix All Issues" button (only show if there are issues) -->
            <UButton
              v-if="(llmFeedback?.issues?.length ?? 0) > 0"
              class="mt-3 w-full"
              color="primary"
              icon="i-heroicons-sparkles"
              label="Fix All Issues with AI"
              @click="openFixModal"
            />
          </div>
        </div>
        <UTextarea v-else v-model="editForm.description" />
      </template>

      <template #footer>
        <div v-if="!isBeingEdited" @dblclick="$event.stopPropagation()">
          <!--collapsed-->
          <div
            v-if="isCollapsed && isCollapsible"
            class="flex justify-center"
            style="padding: -5px; margin: -5px; cursor: default"
            @click="toggleCollapsed()"
          >
            <Icon name="heroicons:chevron-down-20-solid" class="size-5" />
          </div>
          <!-- not collapsed-->
          <div v-else class="flex flex-col w-full">
            <!-- First row -->
            <div class="grid grid-cols-3 items-center w-full">
              <!-- Left aligned -->
              <div class="justify-self-start">
                <UTooltip text="Check with AI">
                  <UButton
                    icon="i-lucide-sparkles"
                    color="warning"
                    variant="soft"
                    :loading="isValidating"
                    @click="handleValidation"
                  />
                </UTooltip>
              </div>

              <!-- Center aligned -->
              <div class="flex justify-center gap-2">
                <UTooltip text="Add Component">
                  <UButton
                    icon="i-lucide-component"
                    color="primary"
                    variant="soft"
                    @click="handleAddComponent"
                  />
                </UTooltip>
                <UTooltip text="Add Key">
                  <UButton
                    icon="i-lucide-key-round"
                    color="primary"
                    variant="soft"
                    @click="handleAddKey"
                  />
                </UTooltip>
              </div>

              <!-- Right aligned -->
              <div class="flex justify-self-end gap-2">
                <UTooltip text="Edit">
                  <UButton
                    icon="i-lucide-square-pen"
                    color="secondary"
                    variant="soft"
                    @click="startEdit"
                  />
                </UTooltip>
                <UTooltip text="Switch Node">
                  <!-- TODO: nodes should not know about switching nodes. this can be handled with a vue slot
                   vue slots allow us to inject buttons from the parent -->
                  <UButton
                    v-if="isCollapsible"
                    icon="i-lucide-arrow-right-left"
                    color="secondary"
                    variant="soft"
                    @click="handleSwitchNode()"
                  />
                </UTooltip>

                <UTooltip text="Delete">
                  <UButton icon="i-lucide-trash" color="error" variant="soft" @click="emitDelete" />
                </UTooltip>
              </div>
            </div>

            <!-- Second row -->
            <div
              v-if="isCollapsible"
              class="flex justify-center pt-4 cursor-default"
              @click="toggleCollapsed()"
            >
              <Icon name="heroicons:chevron-up-20-solid" class="size-5" />
            </div>
          </div>
        </div>
        <!-- during edit-->
        <div v-else class="flex gap-2">
          <UButton color="error" variant="soft" @click="cancelEdit">Cancel</UButton>
          <UButton color="secondary" variant="soft" @click="confirmEdit">Confirm</UButton>
        </div>
      </template>
    </UCard>
  </UContextMenu>
</template>
