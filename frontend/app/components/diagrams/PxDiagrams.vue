<script setup lang="ts">
    import {v4} from 'uuid'

definePageMeta({
  middleware: 'authentication',
})

const props = defineProps({
  nodesInPath: {
    type: Array<string>,
    default: () => [],
  }
})

const diagrams = ref(new Array<string>())

function addItem() {
    const newUuid = v4()
    diagrams.value.push(newUuid)
}

async function deleteDiagram(deleteId: string) {
    diagrams.value = diagrams.value.filter((id) => id != deleteId)
}
</script>

<template>
  <div>
    <SimpleContentWrapper>
      <UCollapsible :unmount-on-hide="false" class="flex flex-col gap-6">
      <UButton
        label="Show Diagrams"
        variant="subtle"
        trailing-icon="i-lucide-chevron-down"
        block
      />
      <template #content>
      <DiagramCardSection use-add-button @add-clicked="addItem">
        <div v-for="d in diagrams" :key="d">
          <PxLineDiagram
            :nodes-in-path="props.nodesInPath"
            show-edit
            show-delete
            @delete="deleteDiagram(d)"
          />
        </div>
      </DiagramCardSection>
      </template>
      </UCollapsible>
    </SimpleContentWrapper>
  </div>
</template>

<style scoped></style>