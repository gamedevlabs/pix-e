<script setup lang="ts">
const props = defineProps<{
  originalPillar: Pillar
}>()

const aiPillar = ref<Pillar | null>(null)

const emit = defineEmits<{ close: [Pillar] }>()

const pillars = usePillars()

pillars
  .fixPillarWithAI(props.originalPillar)
  .then((result) => {
    const nPillar = { ...props.originalPillar }
    nPillar.name = result.name
    nPillar.description = result.description
    nPillar.llm_feedback = null
    aiPillar.value = nPillar
  })
  .catch((error) => {
    console.error('Error generating AI pillar:', error)
    aiPillar.value = null
  })
</script>

<template>
  <UModal
    class="max-w-2xl w-full min-h-100"
    :close="{ onClick: () => emit('close', originalPillar) }"
    :title="'Select a Pillar'"
    :dismissible="false"
  >
    <template #body>
      <div class="flex justify-center gap-10">
        <div class="justify-center">
          <h3 class="text-lg font-semibold text-center mb-2">Original Pillar</h3>
          <UButton
            variant="ghost"
            color="neutral"
            class="p-0"
            size="xl"
            @click="emit('close', originalPillar)"
          >
            <NamedEntityCard
              :named-entity="{
                name: props.originalPillar.name,
                description: props.originalPillar.description,
              }"
              :is-being-edited="false"
              :show-edit="false"
              :show-delete="false"
              variant="compact"
              class="text-left"
            />
          </UButton>
        </div>

        <div class="justify-center">
          <h3 class="text-lg font-semibold text-center mb-2">AI Generated Pillar</h3>
          <UButton
            variant="ghost"
            color="neutral"
            class="p-0"
            size="xl"
            @click="emit('close', aiPillar ?? originalPillar)"
          >
            <NamedEntityCard
              v-if="aiPillar"
              :named-entity="{
                name: aiPillar.name,
                description: aiPillar.description,
              }"
              :is-being-edited="false"
              :show-edit="false"
              :show-delete="false"
              variant="compact"
              class="text-left"
            />
            <div v-else>
              <UCard class="w-72 min-h-50" variant="subtle">
                <template #header>
                  <USkeleton class="h-6 w-32 rounded color-error-100" />
                </template>

                <div class="space-y-2 mt-4">
                  <USkeleton class="h-4 w-full rounded" />
                  <USkeleton class="h-4 w-2/3 rounded" />
                </div>
              </UCard>
            </div>
          </UButton>
        </div>
      </div>
    </template>
  </UModal>
</template>
