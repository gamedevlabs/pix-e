<script setup lang="ts">
import { usePxNodesLLMApi } from '@/composables/api/pxNodesLLMApi'
import { useApi } from '@/composables/useApi'

const props = defineProps<{
  finding: ConsistencyFinding
  projectId: string
}>()

const emit = defineEmits<{
  close: [null]
  accepted: []
}>()

const pxNodesLLMApi = usePxNodesLLMApi()
const { apiFetch } = useApi()

const fixResponse = ref<ConsistencyFixResponse | null>(null)
const isLoading = ref(true)
const isSaving = ref(false)
const error = ref<string | null>(null)

// Fetch the AI improvement with explanations on open.
pxNodesLLMApi
  .fixConsistencyFindingAPICall({
    nodeId: props.finding.entity_id,
    findingCategory: props.finding.category,
    findingDescription: props.finding.message,
    projectId: props.projectId,
  })
  .then((result) => {
    fixResponse.value = result
    isLoading.value = false
  })
  .catch((err) => {
    console.error('Error generating consistency fix:', err)
    error.value = 'Failed to generate improvement. Please try again.'
    isLoading.value = false
  })

const hasNameChange = computed(
  () => !!fixResponse.value && fixResponse.value.original.name !== fixResponse.value.improved.name,
)
const hasDescriptionChange = computed(
  () =>
    !!fixResponse.value &&
    fixResponse.value.original.description !== fixResponse.value.improved.description,
)

async function acceptImprovement() {
  if (!fixResponse.value) return
  isSaving.value = true
  try {
    await apiFetch(`/api/pxnodes/${fixResponse.value.node_id}/`, {
      method: 'PATCH',
      body: {
        name: fixResponse.value.improved.name,
        description: fixResponse.value.improved.description,
      },
      credentials: 'include',
      headers: {
        'X-CSRFToken': useCookie('csrftoken').value,
      } as HeadersInit,
    })
    emit('accepted')
  } catch (err) {
    console.error('Error accepting consistency fix:', err)
    error.value = 'Failed to save improvement. Please try again.'
  } finally {
    isSaving.value = false
  }
}

function keepOriginal() {
  emit('close', null)
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
                <USkeleton class="h-6 w-32 rounded" />
              </template>
              <div class="space-y-2 mt-4">
                <USkeleton class="h-4 w-full rounded" />
                <USkeleton class="h-4 w-2/3 rounded" />
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
                  {{ fixResponse.original.name || '(no name)' }}
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
                {{ fixResponse.original.description || '(no description)' }}
              </p>
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
                  {{ fixResponse.improved.name || '(no name)' }}
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
                {{ fixResponse.improved.description || '(no description)' }}
              </p>
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

          <div v-if="fixResponse.improved.changes.length > 0" class="space-y-4">
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
          <p v-else class="text-sm text-gray-500">
            The AI did not propose any changes for this finding.
          </p>

          <!-- Overall Summary -->
          <div v-if="fixResponse.improved.overall_summary" class="mt-4 pt-4 border-t">
            <p class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Summary:</p>
            <p class="text-sm">{{ fixResponse.improved.overall_summary }}</p>
          </div>

          <!-- Issues Fixed -->
          <div v-if="fixResponse.improved.issues_fixed.length" class="mt-4 pt-4 border-t">
            <p class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Issues Fixed:</p>
            <div class="flex flex-wrap gap-2">
              <UBadge
                v-for="issue in fixResponse.improved.issues_fixed"
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
          <UButton color="primary" size="lg" :loading="isSaving" @click="acceptImprovement">
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
