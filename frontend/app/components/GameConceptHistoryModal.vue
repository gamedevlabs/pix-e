<script setup lang="ts">
const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const {
  conceptHistory,
  isLoadingHistory,
  isRestoringConcept,
  fetchConceptHistory,
  restoreConcept,
} = usePillars()

const isOpen = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

// Pagination
const currentPage = ref(1)
const itemsPerPage = 5

const totalPages = computed(() => Math.ceil(conceptHistory.value.length / itemsPerPage))

const paginatedHistory = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage
  const end = start + itemsPerPage
  return conceptHistory.value.slice(start, end)
})

// Expand/collapse state for each concept
const expandedConcepts = ref<Set<number>>(new Set())

function toggleExpand(conceptId: number) {
  if (expandedConcepts.value.has(conceptId)) {
    expandedConcepts.value.delete(conceptId)
  } else {
    expandedConcepts.value.add(conceptId)
  }
}

function isExpanded(conceptId: number): boolean {
  return expandedConcepts.value.has(conceptId)
}

// Truncate content to approximately 4 lines
function truncateContent(content: string): string {
  const lines = content.split('\n')
  if (lines.length <= 4) {
    return content
  }
  return lines.slice(0, 4).join('\n') + '...'
}

function needsTruncation(content: string): boolean {
  return content.split('\n').length > 4
}

// Format date
function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// Handle restore
async function handleRestore(conceptId: number) {
  await restoreConcept(conceptId)
  isOpen.value = false
}

// Load history when modal opens
watch(isOpen, async (newValue) => {
  if (newValue) {
    currentPage.value = 1
    expandedConcepts.value.clear()
    await fetchConceptHistory()
  }
})
</script>

<template>
  <UModal v-model:open="isOpen">
    <template #content>
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <UIcon name="i-heroicons-clock" class="text-secondary-500" />
              <span class="font-semibold text-lg">Game Concept History</span>
            </div>
            <UButton
              icon="i-heroicons-x-mark"
              color="neutral"
              variant="ghost"
              size="sm"
              @click="isOpen = false"
            />
          </div>
        </template>

        <!-- Loading State -->
        <div v-if="isLoadingHistory" class="flex items-center justify-center py-12">
          <UIcon name="i-heroicons-arrow-path" class="animate-spin text-2xl text-gray-400" />
          <span class="ml-2 text-gray-500">Loading history...</span>
        </div>

        <!-- Empty State -->
        <div v-else-if="conceptHistory.length === 0" class="text-center py-12 text-gray-500">
          <UIcon name="i-heroicons-document-text" class="text-4xl mb-2" />
          <p>No game concept history found.</p>
          <p class="text-sm mt-1">Save a game concept to see it here.</p>
        </div>

        <!-- History List -->
        <div v-else class="flex flex-col">
          <!-- Scrollable content area -->
          <div class="history-scroll-container space-y-4 max-h-[60vh] overflow-y-auto">
            <div
              v-for="concept in paginatedHistory"
              :key="concept.id"
              class="border border-gray-200 dark:border-gray-700 rounded-lg p-4"
            >
              <!-- Header -->
              <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-2">
                  <span class="text-sm text-gray-500">{{ formatDate(concept.updated_at) }}</span>
                  <UBadge v-if="concept.is_current" color="primary" variant="subtle" size="xs">
                    Current
                  </UBadge>
                </div>
                <UButton
                  v-if="!concept.is_current"
                  icon="i-heroicons-arrow-path"
                  label="Restore"
                  color="secondary"
                  variant="soft"
                  size="xs"
                  :loading="isRestoringConcept"
                  @click="handleRestore(concept.id)"
                />
              </div>

              <!-- Content -->
              <div class="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                {{ isExpanded(concept.id) ? concept.content : truncateContent(concept.content) }}
              </div>

              <!-- Expand/Collapse Button -->
              <UButton
                v-if="needsTruncation(concept.content)"
                :icon="
                  isExpanded(concept.id) ? 'i-heroicons-chevron-up' : 'i-heroicons-chevron-down'
                "
                :label="isExpanded(concept.id) ? 'Show less' : 'Show more'"
                color="neutral"
                variant="ghost"
                size="xs"
                class="mt-2"
                @click="toggleExpand(concept.id)"
              />
            </div>
          </div>

          <!-- Pagination (fixed at bottom) -->
          <div
            v-if="totalPages > 1"
            class="flex items-center justify-between pt-4 mt-4 border-t border-gray-200 dark:border-gray-700"
          >
            <UButton
              icon="i-heroicons-chevron-left"
              label="Previous"
              color="neutral"
              variant="ghost"
              size="sm"
              :disabled="currentPage === 1"
              @click="currentPage--"
            />
            <span class="text-sm text-gray-500"> Page {{ currentPage }} of {{ totalPages }} </span>
            <UButton
              icon="i-heroicons-chevron-right"
              label="Next"
              color="neutral"
              variant="ghost"
              size="sm"
              trailing
              :disabled="currentPage === totalPages"
              @click="currentPage++"
            />
          </div>
        </div>
      </UCard>
    </template>
  </UModal>
</template>

<style scoped>
.history-scroll-container {
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE and Edge */
}

.history-scroll-container::-webkit-scrollbar {
  display: none; /* Chrome, Safari, Opera */
}
</style>
