<script setup lang="ts">
definePageMeta({
  middleware: 'authentication',
})

const { fetchGameConcept } = useGameConcept()
const { context } = useSparc()

await fetchGameConcept()

</script>

<template>
  <div class="flex -m-10">
    <!-- Main Content -->
    <div class="flex-1 min-w-0 p-10">
      <h1 class="text-3xl font-bold mb-6">SPARC Evaluation</h1>

      <div class="pt-6">
        <SparcV2EvaluationPanel />
      </div>
    </div>

    <!-- Game Concept Sidebar -->
    <GameConceptSidebar>
      <h2 class="text-2xl font-semibold mt-6 mb-4">Additional Context</h2>
      <UTextarea
        v-model="context"
        placeholder="Add any additional context or constraints..."
        variant="outline"
        color="secondary"
        size="xl"
        :rows="8"
        :max-rows="0"
        autoresize
        class="w-full h-[35vh]"
      />

      <div class="mt-6 p-4 rounded-lg">
        <p class="text-xs text-neutral-400">
          SPARC evaluates 10 aspects: Player Experience, Theme, Gameplay, Place, Unique Features,
          Story & Narrative, Goals/Challenges/Rewards, Art Direction, Purpose, and Opportunities &
          Risks.
        </p>
      </div>
    </GameConceptSidebar>
  </div>
</template>
