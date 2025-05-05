<script setup lang="ts">
import { ref } from 'vue'

const config = useRuntimeConfig()
type Pillar = {
  pillar_id: number
  description: string
}
type PillarResponse = {
  values: Pillar[]
}
type DesignResponse = {
  description: string
}
type LLMFeedback = {
  feedback: string
}

const newPillar = ref('')
const pillars = ref<Pillar[]>([])

const gameDesignIdea = ref('')
const llmFeedback = ref('Feedback will be displayed here')

if (import.meta.client) {
  //This is necessary as long as we use the botched cookie id solution
  await useFetch<PillarResponse>(`${config.public.apiBase}/llm/pillars/`, {
    credentials: 'include',
  })
    .then((data) => {
      if (data.data) {
        data.data.value?.values?.forEach((x) => {
          pillars.value.push(x)
        })
      }
    })
    .catch((error) => {
      console.error('Error fetching:', error)
    })

  await useFetch<DesignResponse>(`${config.public.apiBase}/llm/design/`, {
    method: 'GET',
    credentials: 'include',
  })
    .then((data) => {
      gameDesignIdea.value = data.data.value?.description ?? ''
    })
    .catch((error) => {
      console.error('Error fetching:', error)
    })
}

async function createPillar() {
  if (newPillar.value.trim() === '') return
  const usedIds = new Set(pillars.value.map((obj) => obj.pillar_id))
  let i = 0
  while (usedIds.has(i)) {
    i++
  }
  const index = i
  const pillar: Pillar = {
    pillar_id: index,
    description: newPillar.value.trim(),
  }
  pillars.value.push(pillar)
  try {
    await $fetch(`${config.public.apiBase}/llm/pillars/`, {
      method: 'POST',
      body: {
        pillar: pillar,
      },
      credentials: 'include',
    })
  } catch (error) {
    console.error('Error fetching:', error)
  }
  newPillar.value = ''
}

async function deletePillar(id: number) {
  const pillarIndex = pillars.value.findIndex((X) => X.pillar_id === id)
  if (pillarIndex === -1) return
  const pillar = pillars.value[pillarIndex]
  pillars.value.splice(pillarIndex, 1)
  try {
    await $fetch(`${config.public.apiBase}/llm/pillars/`, {
      method: 'DELETE',
      body: {
        pillar: pillar,
      },
      credentials: 'include',
    })
  } catch (error) {
    console.error('Error fetching:', error)
  }
}

async function updateDesignIdea() {
  if (gameDesignIdea.value.trim() === '') return
  try {
    await $fetch(`${config.public.apiBase}/llm/design/`, {
      method: 'POST',
      body: {
        description: gameDesignIdea.value,
      },
      credentials: 'include',
    })
  } catch (error) {
    console.error('Error fetching:', error)
  }
}

async function getLLMFeedback() {
  try {
    llmFeedback.value = (
      await $fetch<LLMFeedback>(`${config.public.apiBase}/llm/feedback/`, {
        method: 'GET',
        credentials: 'include',
      })
    ).feedback
  } catch (error) {
    console.error('Error fetching:', error)
  }
}
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

        <UButton
          @click="createPillar"
        >
          Save Pillar
        </UButton>
      </div>

      <!-- Game Design Idea Section -->
      <div class="flex items-start gap-2 w-full max-w-xl">
        <UButton
          @click="updateDesignIdea"
        >
          Save Design
        </UButton>
        <textarea
          v-model="gameDesignIdea"
          class="w-full p-2 border border-gray-300 rounded resize-none"
          rows="4"
          placeholder="Enter your game design idea here..."
        />
      </div>
    </div>

    <!-- Pillar Display -->
    <div class="flex mt-6 gap-4 flex-wrap p-5">
      <div
        v-for="msg in pillars"
        :key="msg.pillar_id"
        class="relative bg-blue-100 text-blue-900 p-6 rounded shadow w-70 min-h-[4rem] flex items-center justify-center text-center wrap-anywhere"
      >
        <UButton
          aria-label="Delete"
          @click="deletePillar(msg.pillar_id)"
        >
          🗑️
        </UButton>
        {{ msg.description }}
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
      <UButton
        @click="getLLMFeedback"
      >
        Get LLM Feedback
      </UButton>
    </div>
  </div>
</template>
