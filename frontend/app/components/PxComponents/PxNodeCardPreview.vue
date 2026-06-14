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

    <template #default>
      <div>
        <h2 class="font-semibold text-lg mb-2">Description</h2>
        <p>{{ props.node.description }}</p>
      </div>
      <div v-if="node.keys.length">
        <USeparator class="py-6" />
        <section class="flex flex-wrap gap-4">
          🔑
          <div v-for="pxKey in node.keys" :key="pxKey.id">
            <PxKeyCard visualization-style="preview" :pxkey="pxKey" :read-only="true" />
          </div>
        </section>
      </div>
    </template>
  </UCard>
</template>
