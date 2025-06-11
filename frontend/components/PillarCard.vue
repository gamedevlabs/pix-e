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

const hasFeedback = ref(
  props.pillar.llm_feedback !== null && props.pillar.llm_feedback !== undefined,
)
const feedbackOpen = ref(
  props.pillar.llm_feedback !== null && props.pillar.llm_feedback !== undefined,
)

async function handleValidation() {
  await pillars.validatePillar(props.pillar)
  hasFeedback.value = true
  feedbackOpen.value = true
}

async function initialValidation() {
  if (hasFeedback.value) {
    return
  }
  handleValidation()
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
      pillar.llm_feedback?.hasStructureIssue ? 'outline-error-500' : 'outline-success-500',
    ]"
  >
    <template #footerExtra>
      <div class="relative">
        <UCollapsible v-model:open="feedbackOpen" class="flex flex-col gap-2 w-50">
          <UButton
            v-model="feedbackOpen"
            class="group"
            color="neutral"
            variant="subtle"
            trailing-icon="i-lucide-chevron-down"
            :ui="{
              trailingIcon: 'group-data-[state=open]:rotate-180 transition-transform duration-200',
            }"
            block
            @click="initialValidation"
          >
            <span v-if="hasFeedback">LLM Feedback</span>
            <span v-else>Validate Pillar</span>
          </UButton>

          <template #content>
            {{ pillar.llm_feedback }}
          </template>
        </UCollapsible>

        <UButton
          class="absolute top-0 right-0"
          size="xl"
          icon="i-lucide-refresh-cw"
          color="secondary"
          variant="ghost"
          @click="handleValidation"
        />
      </div>
    </template>
  </NamedEntityCard>
</template>
