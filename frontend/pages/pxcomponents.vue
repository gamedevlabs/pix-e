<script setup lang="ts">
// todo: never code in bs javascript or typescript again
const { items: pxComponentDefinitions, fetchAll: fetchPxComponentDefinitions, createItem: createPxComponentDefinition } =
  usePxComponentDefinitions()

onMounted(() => {
  fetchPxComponentDefinitions()
})

const items = ref(['number', 'string', 'boolean'])

const state = ref<{ name: string; type: PxValueType }>({
  name: '',
  type: 'none',
})

async function handleCreate() {
  await createPxComponentDefinition(state.value)
  state.value.name = ''
  state.value.type = 'none'
}
</script>

<template>
  <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
    <div>
      <UForm :state="state" class="gap-6" @submit="handleCreate">
        <UFormField label="Name" name="name">
          <UInput v-model="state.name" />
        </UFormField>
        <UFormField label="Type" name="type">
          <USelectMenu v-model="state.type" :items="items" />
        </UFormField>
        <UButton type="submit">Submit</UButton>
      </UForm>

      <!-- Cards Section -->
      <section class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <div v-for="definition in pxComponentDefinitions" :key="definition.id">
          <UCard>
            <template #header>
              {{ definition.name }}
            </template>
            {{ definition.type }}
          </UCard>
        </div>
      </section>
    </div>
    <div>hello world</div>
  </div>
</template>

<style scoped></style>
