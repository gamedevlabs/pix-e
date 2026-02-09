<script setup lang="ts">
const props = defineProps<{ useAddButton?: boolean }>()

const emit = defineEmits<{ (e: 'addClicked'): void }>()
</script>

<template>
  <div class="grid grid-cols-3 gap-6" style="grid-template-columns: repeat(auto-fill, minmax(576px, 2fr))">
    <slot />
    <div>
      <UButton
        v-if="props.useAddButton"
        icon="i-lucide-plus"
        variant="soft"
        color="primary"
        class="w-181 min-h-55 [&>*]:text-[50px] justify-center"
        @click="emit('addClicked')"
      />
    </div>
  </div>
</template>

<style scoped></style>
