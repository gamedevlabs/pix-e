<template>
  <UDropdownMenu :items="dropdownItems" :ui="{ width: 'w-48' }">
    <UButton
      color="white"
      :label="buttonLabel"
      trailing-icon="i-heroicons-chevron-down-20-solid"
    />

    <template #item="{ item }">
      <div class="flex flex-col">
        <UCheckbox
          :model-value="item.checked"
          :label="item.label"
          @update:model-value="toggleOption(item.value)"
        />
      </div>
    </template>
  </UDropdownMenu>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps({
  options: {
    type: Array as () => string[],
    default: () => []
  },
  modelValue: {
    type: Array as () => string[],
    default: () => []
  },
  placeholder: {
    type: String,
    default: 'Select items'
  }
})

const emit = defineEmits(['update:modelValue'])

const dropdownItems = computed(() => {
  return [
    props.options.map(option => ({
      label: option,
      value: option,
      checked: props.modelValue.includes(option),
    }))
  ]
})

const toggleOption = (optionValue: string) => {
  const newSelection = props.modelValue.includes(optionValue)
    ? props.modelValue.filter(item => item !== optionValue)
    : [...props.modelValue, optionValue]
  emit('update:modelValue', newSelection)
}

const buttonLabel = computed(() => {
  if (props.modelValue.length === 0) {
    return props.placeholder
  } else if (props.modelValue.length === props.options.length) {
    return 'All selected'
  } else {
    return props.modelValue.join(', ')
  }
})
</script>
