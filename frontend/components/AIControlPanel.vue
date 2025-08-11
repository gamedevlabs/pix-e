<template>
  <div class="ai-control-panel">
    <!-- Main AI Dropdown (ChatGPT style) -->
    <USelect
      v-model="selectedOption"
      :options="selectOptions"
      placeholder="Select AI Model & Settings"
      class="ai-dropdown"
      size="md"
      :loading="servicesLoading"
      @update:model-value="handleSelectionChange"
    >
      <template #leading>
        <UIcon :name="getSelectedIcon()" class="text-purple-600 dark:text-purple-400" />
      </template>
    </USelect>

    <!-- Quick Action Buttons -->
    <div class="flex items-center gap-2 ml-3">
      <UTooltip text="Regenerate suggestions">
        <UButton 
          @click="$emit('regenerate')"
          :loading="loading"
          :disabled="!canRegenerate"
          variant="ghost" 
          size="sm"
          icon="i-heroicons-arrow-path-20-solid"
        />
      </UTooltip>
      
      <UTooltip text="Configure API tokens">
        <UButton 
          @click="$emit('configure-tokens')"
          variant="ghost" 
          size="sm"
          icon="i-heroicons-key-20-solid"
          :color="hasValidTokens ? 'success' : 'warning'"
        />
      </UTooltip>
    </div>
  </div>
</template>

<script setup lang="ts">
interface AIService {
  id: string
  name: string
  status: 'available' | 'unavailable' | 'loading'
}

interface Option {
  value: string
  label: string
  description?: string
  icon: string
  iconClass?: string
  badge?: string
  badgeColor?: string
  category: 'service' | 'mode' | 'setting'
  serviceId?: string
  mode?: 'default' | 'gaming'
  suggestionType?: 'short' | 'long'
}

interface Props {
  services: AIService[]
  servicesLoading: boolean
  activeService: string | null
  mode: 'default' | 'gaming'
  suggestionType: 'short' | 'long'
  loading: boolean
  canRegenerate: boolean
  hasValidTokens: boolean
}

interface Emits {
  (e: 'service-changed', serviceId: string): void
  (e: 'mode-changed', mode: 'default' | 'gaming'): void
  (e: 'type-changed', type: 'short' | 'long'): void
  (e: 'regenerate'): void
  (e: 'configure-tokens'): void
}

const props = withDefaults(defineProps<Props>(), {
  activeService: null,
  mode: 'default',
  suggestionType: 'short',
  loading: false,
  canRegenerate: false,
  hasValidTokens: false
})

const emit = defineEmits<Emits>()

// Current selected option
const selectedOption = ref<string>('')

// Generate select options (simplified for USelect)
const selectOptions = computed(() => {
  const options: { value: string; label: string }[] = []
  
  // Add services
  if (props.services.length > 0) {
    props.services.forEach(service => {
      options.push({
        value: `service-${service.id}`,
        label: `${service.name} ${service.id === props.activeService ? '(Active)' : ''}`
      })
    })
  }
  
  // Add mode options
  options.push({
    value: 'mode-default',
    label: `Default Mode ${props.mode === 'default' ? '(Active)' : ''}`
  })
  
  options.push({
    value: 'mode-gaming', 
    label: `Gaming Mode ${props.mode === 'gaming' ? '(Active)' : ''}`
  })
  
  // Add type options
  options.push({
    value: 'type-short',
    label: `Short Suggestions ${props.suggestionType === 'short' ? '(Active)' : ''}`
  })
  
  options.push({
    value: 'type-long',
    label: `Detailed Suggestions ${props.suggestionType === 'long' ? '(Active)' : ''}`
  })
  
  return options
})

// Generate all options (ChatGPT style)
const allOptions = computed<Option[]>(() => {
  const options: Option[] = []
  
  // Add service options
  if (props.services.length > 0) {
    options.push({
      value: 'divider-services',
      label: '━━━━━ AI Models ━━━━━',
      icon: 'i-heroicons-cpu-chip-20-solid',
      iconClass: 'text-blue-500',
      category: 'service'
    })
    
    props.services.forEach(service => {
      const isActive = service.id === props.activeService
      options.push({
        value: `service-${service.id}`,
        label: service.name,
        description: service.status === 'available' ? 'Ready to use' : 'Currently unavailable',
        icon: getServiceIcon(service.name),
        iconClass: service.status === 'available' ? 'text-green-500' : 'text-gray-400',
        badge: isActive ? 'Active' : undefined,
        badgeColor: isActive ? 'green' : undefined,
        category: 'service',
        serviceId: service.id
      })
    })
  }
  
  // Add mode options
  options.push({
    value: 'divider-modes',
    label: '━━━━━ Generation Modes ━━━━━',
    icon: 'i-heroicons-adjustments-horizontal-20-solid',
    iconClass: 'text-purple-500',
    category: 'mode'
  })
  
  options.push({
    value: 'mode-default',
    label: 'Default Mode',
    description: 'Balanced suggestions for general use',
    icon: 'i-heroicons-sparkles-20-solid',
    iconClass: 'text-blue-500',
    badge: props.mode === 'default' ? 'Active' : undefined,
    badgeColor: props.mode === 'default' ? 'blue' : undefined,
    category: 'mode',
    mode: 'default'
  })
  
  options.push({
    value: 'mode-gaming',
    label: 'Gaming Mode',
    description: 'Specialized suggestions for games',
    icon: 'i-heroicons-command-line-20-solid',
    iconClass: 'text-orange-500',
    badge: props.mode === 'gaming' ? 'Active' : undefined,
    badgeColor: props.mode === 'gaming' ? 'orange' : undefined,
    category: 'mode',
    mode: 'gaming'
  })
  
  // Add suggestion type options
  options.push({
    value: 'divider-types',
    label: '━━━━━ Suggestion Length ━━━━━',
    icon: 'i-heroicons-document-text-20-solid',
    iconClass: 'text-green-500',
    category: 'setting'
  })
  
  options.push({
    value: 'type-short',
    label: 'Short Suggestions',
    description: 'Quick, concise suggestions',
    icon: 'i-heroicons-minus-20-solid',
    iconClass: 'text-gray-500',
    badge: props.suggestionType === 'short' ? 'Active' : undefined,
    badgeColor: props.suggestionType === 'short' ? 'gray' : undefined,
    category: 'setting',
    suggestionType: 'short'
  })
  
  options.push({
    value: 'type-long',
    label: 'Detailed Suggestions',
    description: 'Comprehensive, detailed suggestions',
    icon: 'i-heroicons-plus-20-solid',
    iconClass: 'text-green-500',
    badge: props.suggestionType === 'long' ? 'Active' : undefined,
    badgeColor: props.suggestionType === 'long' ? 'green' : undefined,
    category: 'setting',
    suggestionType: 'long'
  })
  
  return options
})

// Get service icon based on service name
function getServiceIcon(serviceName: string): string {
  if (serviceName.toLowerCase().includes('gpt') || serviceName.toLowerCase().includes('github')) {
    return 'i-simple-icons-openai'
  }
  if (serviceName.toLowerCase().includes('mistral')) {
    return 'i-heroicons-fire-20-solid'
  }
  if (serviceName.toLowerCase().includes('gemma')) {
    return 'i-heroicons-star-20-solid'
  }
  if (serviceName.toLowerCase().includes('hugging')) {
    return 'i-simple-icons-huggingface'
  }
  return 'i-heroicons-cpu-chip-20-solid'
}

// Get icon for currently selected option
function getSelectedIcon(): string {
  if (selectedOption.value.startsWith('service-')) {
    const serviceId = selectedOption.value.replace('service-', '')
    const service = props.services.find(s => s.id === serviceId)
    if (service) return getServiceIcon(service.name)
  } else if (selectedOption.value === 'mode-gaming') {
    return 'i-heroicons-command-line-20-solid'
  } else if (selectedOption.value === 'mode-default') {
    return 'i-heroicons-sparkles-20-solid'
  } else if (selectedOption.value === 'type-long') {
    return 'i-heroicons-plus-20-solid'
  } else if (selectedOption.value === 'type-short') {
    return 'i-heroicons-minus-20-solid'
  }
  
  // Default based on current active service
  if (props.activeService) {
    const activeServiceObj = props.services.find(s => s.id === props.activeService)
    if (activeServiceObj) return getServiceIcon(activeServiceObj.name)
  }
  
  return 'i-heroicons-sparkles-20-solid'
}

// Handle selection changes
function handleSelectionChange(value: any) {
  const stringValue = typeof value === 'string' ? value : (value?.value || '')
  
  if (stringValue.startsWith('service-')) {
    const serviceId = stringValue.replace('service-', '')
    emit('service-changed', serviceId)
  } else if (stringValue.startsWith('mode-')) {
    const mode = stringValue.replace('mode-', '') as 'default' | 'gaming'
    emit('mode-changed', mode)
  } else if (stringValue.startsWith('type-')) {
    const type = stringValue.replace('type-', '') as 'short' | 'long'
    emit('type-changed', type)
  }
}

// Update selected option when props change
watch([() => props.activeService, () => props.mode, () => props.suggestionType], () => {
  updateSelectedOption()
}, { immediate: true })

function updateSelectedOption() {
  // Priority: active service > mode > suggestion type
  if (props.activeService) {
    selectedOption.value = `service-${props.activeService}`
  } else if (props.mode === 'gaming') {
    selectedOption.value = 'mode-gaming'
  } else {
    selectedOption.value = 'mode-default'
  }
}
</script>

<style scoped>
.ai-control-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.ai-dropdown {
  flex: 1;
  max-width: 20rem;
}
</style>
