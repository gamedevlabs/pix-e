<script setup lang="ts">
const props = defineProps<{
  node: PxNode
}>()
</script>

<template>
  <UCard class="hover:shadow-lg transition">
    <template #header>
      <h2 class="font-semibold text-lg">
        <NuxtLink :to="{ name: 'pxnodes-id', params: { id: props.node.id } }">
          {{ props.node.name }}
        </NuxtLink>
      </h2>
    </template>

    <div>
      <p>{{ props.node.description }}</p>
    </div>
  </UCard>
</template>
