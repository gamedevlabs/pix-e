<script setup lang="ts">
defineProps<{
  results: Array<SimplifiedAspectResponse & { name: string }>
  reEvaluatingAspect?: string | null
}>()

const emit = defineEmits<{
  (event: 'reEvaluate', aspect: SPARCV2AspectName): void
}>()
</script>

<template>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    <SparcV2AspectCard
      v-for="result in results"
      :key="result.name"
      :aspect-name="result.name"
      :result="result"
      :is-re-evaluating="reEvaluatingAspect === result.name"
      @re-evaluate="emit('reEvaluate', result.name as SPARCV2AspectName)"
    />
  </div>
</template>
