<script setup lang="ts">
import { PillarFixModal } from '#components'

const props = defineProps<{
  pillar: Pillar
  isBeingEdited?: boolean
  showEdit?: boolean
  showDelete?: boolean
  variant?: 'compact'
}>()

const emit = defineEmits<{
  (event: 'update', namedEntityDraft: Partial<NamedEntity>): void
  (event: 'edit' | 'delete'): void
  (event: 'dismiss', index: number): void
}>()

const toast = useToast()
const pillars = usePillars()
const overlay = useOverlay()

async function openFixModal() {
  const modal = overlay.create(PillarFixModal, {
    props: {
      originalPillar: props.pillar,
      validationIssues: props.pillar.llm_feedback?.structuralIssues ?? [],
      onClose: () => modal.close(),
      onAccepted: (updatedPillar: Pillar) => {
        emit('update', updatedPillar)
        modal.close()
        toast.add({
          title: 'Pillar Updated',
          description: 'The AI improvement has been applied.',
          color: 'success',
        })
      },
    },
  })
  modal.open()
}

async function handleValidation() {
  await pillars.validatePillar(props.pillar)
  if (props.pillar.llm_feedback?.hasStructureIssue) {
    toast.add({
      title: 'Structural Issues Found',
      description: `Found ${props.pillar.llm_feedback.structuralIssues.length} issues.`,
      color: 'warning',
    })
  } else {
    toast.add({
      title: 'No Structural Issues',
      description: 'The pillar is structurally sound.',
      color: 'success',
    })
  }
}
</script>

<template>
  <NamedEntityCard
    :named-entity="{
      name: pillar.name,
      description: pillar.description,
    }"
    :is-being-edited="isBeingEdited"
    :show-edit="showEdit"
    :show-delete="showDelete"
    :variant="variant"
    :class="[
      'outline-1',
      (pillar.llm_feedback?.structuralIssues.length ?? 0 > 0)
        ? 'outline-error-500'
        : 'outline-success-500',
    ]"
    @edit="emit('edit')"
    @update="(v) => emit('update', v)"
    @delete="emit('delete')"
  >
    <template #footerExtra>
      <div class="relative">
        <div class="justify-between flex items-center mb-2 gap-2">
          <h2 class="font-semibold text-lg">LLM Feedback</h2>
          <UButton
            size="md"
            icon="i-lucide-refresh-cw"
            color="secondary"
            variant="subtle"
            label="Generate"
            loading-auto
            @click="handleValidation"
          />
        </div>
        
        <!-- Show issues list -->
        <div v-for="(issue, index) in pillar.llm_feedback?.structuralIssues" :key="index">
          <UAlert
            class="mb-2"
            variant="subtle"
            :color="issue.severity >= 3 ? 'error' : 'warning'"
            :title="issue.title"
            :description="'Severity ' + issue.severity"
            :actions="[
              {
                label: 'Dismiss',
                color: 'warning',
                variant: 'subtle',
                class: 'ml-auto',
                onClick: () => emit('dismiss', index),
              },
            ]"
          />
        </div>
        
        <!-- Single "Fix All Issues" button (only show if there are issues) -->
        <UButton
          v-if="(pillar.llm_feedback?.structuralIssues?.length ?? 0) > 0"
          class="mt-3 w-full"
          color="primary"
          icon="i-heroicons-sparkles"
          label="Fix All Issues with AI"
          @click="openFixModal"
        />
      </div>
    </template>
  </NamedEntityCard>
</template>
