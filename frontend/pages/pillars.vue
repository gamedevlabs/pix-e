<script setup lang="ts">
import { usePillars } from '~/composables/usePillars'
import { ref } from 'vue'
import type { Pillar, GameDesign } from '~/types/pillars'

const config = useRuntimeConfig()

const {
  pillars,
  designIdea,
  llmFeedback,
  createPillar,
  deletePillar,
  getLLMFeedback,
  updateDesignIdea,
} = await usePillars()

const newPillar = ref('')

await useFetch<Pillar[]>(`${config.public.apiBase}/llm/pillars/`, {
  credentials: 'include',
})
  .then((data) => {
    if (data.data) {
      data.data.value?.forEach((x) => {
        pillars.value.push(x)
      })
    }
  })
  .catch((error) => {
    console.error('Error fetching:', error)
  })

await useFetch<GameDesign>(`${config.public.apiBase}/llm/design/0/get_or_create/`, {
  method: 'GET',
  credentials: 'include',
}).then((data) => {
  designIdea.value = data.data.value?.description ?? ''
})
</script>

<template>
  <div class="p-6">
    <div class="flex p-4 gap-40">
      <!-- New Pillar Section -->
      <div class="flex items-start gap-2 w-full max-w-xl">
        <textarea
          v-model="newPillar"
          placeholder="Enter new pillar..."
          class="border rounded px-3 py-2 w-full resize-none"
          rows="4"
        />

        <UButton @click="createPillar(newPillar)"> Save Pillar</UButton>
      </div>

      <!-- Game Design Idea Section -->
      <div class="flex items-start gap-2 w-full max-w-xl">
        <UButton @click="updateDesignIdea(designIdea)"> Save Design</UButton>
        <textarea
          v-model="designIdea"
          class="w-full p-2 border border-gray-300 rounded resize-none"
          rows="4"
          placeholder="Enter your game design idea here..."
        />
      </div>
    </div>

    <!-- Pillar Display -->
    <div class="flex mt-6 gap-4 flex-wrap p-5">
      <div v-for="pillar in pillars" :key="pillar.pillar_id" class="relative">
        <UCard>
          <template #header>
            <h2 class="font-semibold text-lg">Pillar</h2>
          </template>
          <p>{{ pillar.description }}</p>
          <template #footer>
            <UButton color="neutral" variant="soft">Read more</UButton>
          </template>
        </UCard>

        <UButton
          aria-label="Delete"
          icon="i-lucide-trash-2"
          color="error"
          variant="ghost"
          class="absolute top-2 right-2 z-10"
          @click="deletePillar(pillar)"
        />
      </div>
    </div>
    <!-- LLM Feedback -->
    <div class="flex mt-6 gap-4 flex-wrap p-5">
      <div
        class="relative bg-green-100 text-blue-800 p-6 rounded shadow w-full min-h-[4rem] flex items-center justify-center text-center wrap-anywhere"
      >
        {{ llmFeedback }}
      </div>
    </div>
    <div class="flex mt-0 gap-4 flex-wrap p-5">
      <UButton @click="getLLMFeedback"> Get LLM Feedback</UButton>
    </div>
  </div>
</template>
