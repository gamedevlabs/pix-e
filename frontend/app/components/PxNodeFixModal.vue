<script setup lang="ts">
const props = defineProps<{
  originalNode: PxNode
  validationIssues?: NodeCoherenceIssue[]
}>()

const emit = defineEmits<{
  close: [PxNode | null]
  accepted: [PxNode]
}>()

const pxNodesLLM = usePxNodesLLM()
const { fetchById: fetchDefinitionById } = usePxComponentDefinitions()

const fixResponse = ref<FixNodeAPIResponse | null>(null)
const isLoading = ref(true)
const error = ref<string | null>(null)

// Cache for component definition names (used during loading state)
const definitionNames = ref<Record<string, string>>({})

// Fetch definition names for original node components (for loading state display)
onMounted(async () => {
  for (const comp of props.originalNode.components ?? []) {
    if (comp.definition && !definitionNames.value[comp.definition]) {
      try {
        const def = await fetchDefinitionById(comp.definition)
        if (def) {
          definitionNames.value[comp.definition] = def.name
        }
      } catch {
        definitionNames.value[comp.definition] = 'Unknown'
      }
    }
  }
})

// Fetch the AI improvement with explanations
pxNodesLLM
  .fixNodeWithAI(props.originalNode.id, props.validationIssues ?? [])
  .then((result) => {
    fixResponse.value = result
    isLoading.value = false
  })
  .catch((err) => {
    console.error('Error generating AI node:', err)
    error.value = 'Failed to generate improvement. Please try again.'
    isLoading.value = false
  })

// Get component value with suggested change applied
function getImprovedComponentValue(componentId: string, originalValue: unknown): unknown {
  if (!fixResponse.value) return originalValue
  const change = fixResponse.value.improved.component_changes.find(
    (c) => c.component_id === componentId,
  )
  return change ? change.suggested_value : originalValue
}

// Check if component has a suggested change
function hasComponentChange(componentId: string): boolean {
  if (!fixResponse.value) return false
  return fixResponse.value.improved.component_changes.some((c) => c.component_id === componentId)
}

// Check if name changed
const hasNameChange = computed(() => {
  if (!fixResponse.value) return false
  return fixResponse.value.original.name !== fixResponse.value.improved.name
})

// Check if description changed
const hasDescriptionChange = computed(() => {
  if (!fixResponse.value) return false
  return fixResponse.value.original.description !== fixResponse.value.improved.description
})

// Accept the AI improvement and persist to DB
async function acceptImprovement() {
  if (!fixResponse.value) return

  try {
    // Map component changes to the format expected by the API
    const componentUpdates = fixResponse.value.improved.component_changes.map((change) => ({
      id: change.component_id,
      value: change.suggested_value,
    }))

    const updated = await pxNodesLLM.acceptNodeFix(
      fixResponse.value.node_id,
      fixResponse.value.improved.name,
      fixResponse.value.improved.description,
      componentUpdates,
    )
    if (updated) {
      emit('accepted', updated)
    }
  } catch (err) {
    console.error('Error accepting improvement:', err)
    error.value = 'Failed to save improvement. Please try again.'
  }
}

// Keep original node
function keepOriginal() {
  emit('close', props.originalNode)
}
</script>

<template>
  <UModal
    class="max-w-5xl w-full"
    :close="{ onClick: () => emit('close', null) }"
    title="AI Improvement Proposal"
    :dismissible="false"
  >
    <template #body>
      <!-- Error State -->
      <div v-if="error" class="text-center py-8">
        <UIcon name="i-heroicons-exclamation-triangle" class="text-red-500 text-4xl mb-2" />
        <p class="text-red-500">{{ error }}</p>
        <UButton class="mt-4" @click="emit('close', null)">Close</UButton>
      </div>

      <!-- Loading State -->
      <div v-else-if="isLoading" class="space-y-6">
        <div class="flex justify-center gap-8">
          <div class="w-80">
            <h3 class="text-lg font-semibold text-center mb-2">Original Node</h3>
            <UCard class="min-h-50" variant="subtle">
              <template #header>
                <span class="font-medium">{{ originalNode.name }}</span>
              </template>
              <p class="text-sm text-gray-600 dark:text-gray-300 mb-3">
                {{ originalNode.description }}
              </p>
              <!-- Original Components from prop -->
              <div v-if="originalNode.components?.length > 0" class="mt-3 pt-3 border-t">
                <p class="text-xs font-semibold text-gray-500 mb-2">Components</p>
                <div class="space-y-1">
                  <div
                    v-for="comp in originalNode.components"
                    :key="comp.id"
                    class="flex justify-between text-sm"
                  >
                    <span class="text-gray-600 dark:text-gray-400">
                      {{ definitionNames[comp.definition] || 'Loading...' }}
                    </span>
                    <span class="font-mono">{{ comp.value }}</span>
                  </div>
                </div>
              </div>
            </UCard>
          </div>
          <div class="w-80">
            <h3 class="text-lg font-semibold text-center mb-2">AI Generated Node</h3>
            <UCard class="min-h-50" variant="subtle">
              <template #header>
                <USkeleton class="h-6 w-32 rounded" />
              </template>
              <div class="space-y-2 mt-4">
                <USkeleton class="h-4 w-full rounded" />
                <USkeleton class="h-4 w-2/3 rounded" />
              </div>
              <div class="mt-4 pt-3 border-t">
                <USkeleton class="h-3 w-20 rounded mb-2" />
                <USkeleton class="h-4 w-full rounded" />
              </div>
            </UCard>
          </div>
        </div>
        <div class="text-center text-gray-500">
          <UIcon name="i-heroicons-sparkles" class="animate-pulse" />
          Generating improvement with explanations...
        </div>
      </div>

      <!-- Loaded State with Explanations -->
      <div v-else-if="fixResponse" class="space-y-6">
        <!-- Side-by-side comparison -->
        <div class="flex justify-center gap-8">
          <div class="w-80">
            <h3 class="text-lg font-semibold text-center mb-2">Original Node</h3>
            <UCard class="min-h-50" variant="subtle">
              <template #header>
                <span
                  class="font-medium"
                  :class="{
                    'bg-error-50 dark:bg-error-900/20 px-1 rounded text-error-600 dark:text-error-400':
                      hasNameChange,
                  }"
                >
                  {{ fixResponse.original.name }}
                </span>
              </template>
              <p
                class="text-sm mb-3"
                :class="
                  hasDescriptionChange
                    ? 'bg-error-50 dark:bg-error-900/20 px-1 rounded text-error-600 dark:text-error-400'
                    : 'text-gray-600 dark:text-gray-300'
                "
              >
                {{ fixResponse.original.description }}
              </p>
              <!-- Original Components from API response -->
              <div v-if="fixResponse.original.components?.length > 0" class="mt-3 pt-3 border-t">
                <p class="text-xs font-semibold text-gray-500 mb-2">Components</p>
                <div class="space-y-1">
                  <div
                    v-for="comp in fixResponse.original.components"
                    :key="comp.component_id"
                    class="flex justify-between text-sm"
                    :class="{
                      'bg-error-50 dark:bg-error-900/20 -mx-2 px-2 py-0.5 rounded':
                        hasComponentChange(comp.component_id),
                    }"
                  >
                    <span class="text-gray-600 dark:text-gray-400">
                      {{ comp.definition_name }}
                    </span>
                    <span
                      class="font-mono"
                      :class="{
                        'text-error-600 dark:text-error-400': hasComponentChange(comp.component_id),
                      }"
                    >
                      {{ comp.value }}
                    </span>
                  </div>
                </div>
              </div>
            </UCard>
          </div>
          <div class="w-80">
            <h3 class="text-lg font-semibold text-center mb-2">AI Generated Node</h3>
            <UCard class="min-h-50" variant="subtle">
              <template #header>
                <span
                  class="font-medium"
                  :class="{
                    'bg-success-50 dark:bg-success-900/20 px-1 rounded text-success-600 dark:text-success-400':
                      hasNameChange,
                  }"
                >
                  {{ fixResponse.improved.name }}
                </span>
              </template>
              <p
                class="text-sm mb-3"
                :class="
                  hasDescriptionChange
                    ? 'bg-success-50 dark:bg-success-900/20 px-1 rounded text-success-600 dark:text-success-400'
                    : 'text-gray-600 dark:text-gray-300'
                "
              >
                {{ fixResponse.improved.description }}
              </p>
              <!-- Improved Components from API response -->
              <div v-if="fixResponse.original.components?.length > 0" class="mt-3 pt-3 border-t">
                <p class="text-xs font-semibold text-gray-500 mb-2">Components</p>
                <div class="space-y-1">
                  <div
                    v-for="comp in fixResponse.original.components"
                    :key="comp.component_id"
                    class="flex justify-between text-sm"
                    :class="{
                      'bg-success-50 dark:bg-success-900/20 -mx-2 px-2 py-0.5 rounded':
                        hasComponentChange(comp.component_id),
                    }"
                  >
                    <span class="text-gray-600 dark:text-gray-400">
                      {{ comp.definition_name }}
                    </span>
                    <span
                      class="font-mono"
                      :class="{
                        'text-success-600 dark:text-success-400 font-semibold': hasComponentChange(
                          comp.component_id,
                        ),
                      }"
                    >
                      {{ getImprovedComponentValue(comp.component_id, comp.value) }}
                    </span>
                  </div>
                </div>
              </div>
            </UCard>
          </div>
        </div>

        <!-- Explanation Section -->
        <UCard variant="subtle">
          <template #header>
            <div class="flex items-center gap-2">
              <UIcon name="i-heroicons-light-bulb" class="text-yellow-500" />
              <span class="font-semibold">What Changed & Why</span>
            </div>
          </template>

          <!-- Text Changes List -->
          <div v-if="fixResponse.improved.changes.length > 0" class="space-y-4">
            <h4 class="text-sm font-semibold text-gray-600 dark:text-gray-400">Text Changes</h4>
            <div
              v-for="(change, index) in fixResponse.improved.changes"
              :key="index"
              class="border-l-2 border-primary-500 pl-4"
            >
              <div class="flex items-center gap-2 mb-1">
                <span class="font-medium capitalize">{{ change.field }}:</span>
                <span class="text-sm text-gray-500 italic">"{{ change.after }}"</span>
              </div>
              <p class="text-sm text-gray-700 dark:text-gray-300 mb-2">
                {{ change.reasoning }}
              </p>
              <div v-if="change.issues_addressed.length" class="flex flex-wrap gap-1">
                <UBadge
                  v-for="issue in change.issues_addressed"
                  :key="issue"
                  color="success"
                  variant="subtle"
                  size="xs"
                >
                  <UIcon name="i-heroicons-check" class="mr-1" />
                  {{ issue }}
                </UBadge>
              </div>
            </div>
          </div>

          <!-- Component Changes List -->
          <div v-if="fixResponse.improved.component_changes.length > 0" class="space-y-4 mt-6">
            <h4 class="text-sm font-semibold text-gray-600 dark:text-gray-400">
              Component Value Changes
            </h4>
            <div
              v-for="(change, index) in fixResponse.improved.component_changes"
              :key="index"
              class="border-l-2 border-warning-500 pl-4"
            >
              <div class="flex items-center gap-2 mb-1">
                <span class="font-medium">{{ change.component_name }}:</span>
                <span class="text-sm text-gray-500">
                  {{ change.current_value }} → {{ change.suggested_value }}
                </span>
              </div>
              <p class="text-sm text-gray-700 dark:text-gray-300 mb-2">
                {{ change.reasoning }}
              </p>
              <div v-if="change.issues_addressed.length" class="flex flex-wrap gap-1">
                <UBadge
                  v-for="issue in change.issues_addressed"
                  :key="issue"
                  color="success"
                  variant="subtle"
                  size="xs"
                >
                  <UIcon name="i-heroicons-check" class="mr-1" />
                  {{ issue }}
                </UBadge>
              </div>
            </div>
          </div>

          <!-- Overall Summary -->
          <div v-if="fixResponse.improved.overall_summary" class="mt-4 pt-4 border-t">
            <p class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Summary:</p>
            <p class="text-sm">{{ fixResponse.improved.overall_summary }}</p>
          </div>

          <!-- Issues Fixed -->
          <div
            v-if="fixResponse.improved.validation_issues_fixed.length"
            class="mt-4 pt-4 border-t"
          >
            <p class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Issues Fixed:</p>
            <div class="flex flex-wrap gap-2">
              <UBadge
                v-for="issue in fixResponse.improved.validation_issues_fixed"
                :key="issue"
                color="success"
                variant="solid"
                size="sm"
              >
                <UIcon name="i-heroicons-check-circle" class="mr-1" />
                {{ issue }}
              </UBadge>
            </div>
          </div>
        </UCard>

        <!-- Action Buttons -->
        <div class="flex justify-center gap-4">
          <UButton color="primary" size="lg" @click="acceptImprovement">
            <UIcon name="i-heroicons-check" class="mr-1" />
            Accept Improvement
          </UButton>
          <UButton color="neutral" variant="outline" size="lg" @click="keepOriginal">
            Keep Original
          </UButton>
        </div>
      </div>
    </template>
  </UModal>
</template>
