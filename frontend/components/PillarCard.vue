<script setup lang="ts">
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
}>()

const toast = useToast()
const pillars = usePillars()

async function dismissIssue(index: number) {
  props.pillar.llm_feedback?.structuralIssues.splice(index, 1)
}

async function handleValidation() {
  await pillars.validatePillar(props.pillar)
}

async function fixWithAI(pillar: Pillar) {
  await pillars.fixPillarWithAI(pillar)
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
    @edit="emit('edit')"
    @update="(v) => emit('update', v)"
    @delete="emit('delete')"
    :class="[
      'outline outline-1',
      pillar.llm_feedback?.structuralIssues.length > 0
        ? 'outline-error-500'
        : 'outline-success-500',
    ]"
  >
    <template #footerExtra>
      <div class="relative">
        <div class="justify-between flex items-center mb-2">
          <h2 class="font-semibold text-lg">LLM Feedback</h2>
          <UButton
            size="xl"
            trailing-icon="i-lucide-refresh-cw"
            color="secondary"
            variant="ghost"
            label="Generate"
            @click="handleValidation"
          />
        </div>
        <div v-for="(issue, index) in pillar.llm_feedback?.structuralIssues" :key="index">
          <UAlert
            class="mb-2"
            variant="subtle"
            :color="issue.severity >= 3 ? 'error' : 'warning'"
            :title="'Structural Issue Severity: ' + issue.severity"
            :description="issue.description"
            :actions="[
              {
                label: 'Fix with AI',
                color: 'primary',
                variant: 'subtle',
                onClick: () => fixWithAI(props.pillar),
              },
              {
                label: 'Dismiss',
                color: 'warning',
                variant: 'subtle',
                class: 'ml-auto',
                onClick: () => dismissIssue(index),
              },
            ]"
          />
        </div>
      </div>
    </template>
  </NamedEntityCard>
</template>
