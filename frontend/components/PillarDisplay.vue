<script setup lang="ts">
const emit = defineEmits<{
  (e: 'select', id: number): void
  (e: 'delete', id: number): void
}>()

const { pillar, selectedPillar } = defineProps<{
  pillar: Pillar
  selectedPillar: number
}>()

function selectThisPillar() {
  emit('select', pillar.pillar_id)
}

function unselectPillar() {
  emit('select', -1)
}
</script>

<template>
  <div class="relative">
    <UCard class="w-70 min-h-55 flex flex-col justify-center-safe" variant="soft">
      <template #header>
        <div class="w-full h-12 flex items-center justify-between">
          <div class="flex-1">
            <template v-if="selectedPillar === pillar.pillar_id">
              <UInput
                v-model="pillar.title"
                placeholder="Enter name..."
                size="xl"
                variant="subtle"
              />
            </template>
            <template v-else>
              <h3 class="text-lg font-semibold h-full flex items-center">
                {{ pillar.title !== '' ? pillar.title : 'Title' }}
              </h3>
            </template>
          </div>
        </div>
      </template>

      <div class="flex-1 w-full flex items-center left-0">
        <template v-if="selectedPillar === pillar.pillar_id">
          <UTextarea
            v-model="pillar.description"
            placeholder="Enter description here..."
            size="lg"
            variant="subtle"
            :rows="1"
            autoresize
            class="w-full"
          />
        </template>
        <template v-else>
          <p>{{ pillar.description !== '' ? pillar.description : 'Description' }}</p>
        </template>
      </div>
      <template #footer>
        <div class="flex items-center justify-between">
          <UButton
            color="neutral"
            variant="soft"
            @click="selectedPillar === pillar.pillar_id ? unselectPillar() : selectThisPillar()"
          >
            {{ selectedPillar === pillar.pillar_id ? 'Save' : 'Edit' }}
          </UButton>
          <UButton
            v-if="selectedPillar !== pillar.pillar_id"
            color="secondary"
            variant="soft"
            label="Validate"
            @click="validatePillar(pillar)"
          />
        </div>
        <UCollapsible class="pt-4" :open="pillar.display_open" :disabled="!pillar.llm_feedback">
          <UButton
            color="neutral"
            variant="soft"
            class="w-full text-left"
            :label="pillar.llm_feedback ? 'LLM Feedback' : 'No LLM Feedback'"
            icon="i-lucide-chevron-down"
            @click="pillar.display_open = !pillar.display_open"
          />
          <template #content>
            {{ pillar.llm_feedback }}
          </template>
        </UCollapsible>
      </template>
    </UCard>

    <UButton
      aria-label="Delete"
      icon="i-lucide-trash-2"
      color="error"
      variant="ghost"
      class="absolute top-2 right-2 z-10"
      @click="handlePillarDelete(pillar)"
    />
  </div>
</template>
