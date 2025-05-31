<script setup lang="ts">
const props = defineProps<{useAddButton?: boolean}>()

const emit = defineEmits<{(e: 'addClicked'): void}>()

</script>

<template>
  <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
    <slot />
    <div>
      <UButton
          v-if="props.useAddButton"
          icon="i-lucide-plus"
          variant="soft"
          color="primary"
          class="w-70 min-h-55 [&>*]:text-[50px] justify-center"
          @click="emit('addClicked')"
      />
    </div>
  </div>
</template>

<style scoped>

</style>