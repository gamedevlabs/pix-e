<template>
  <div class="ai-suggestions-panel" :class="{ 'panel-visible': isVisible }">
    <!-- Panel Header -->
    <div class="panel-header">
      <div class="header-left">
        <UIcon name="i-heroicons-sparkles-20-solid" class="text-purple-600 dark:text-purple-400" />
        <h3>AI Suggestions</h3>
        <UBadge
          v-if="totalSuggestions > 0"
          :label="totalSuggestions.toString()"
          color="primary"
          variant="soft"
          size="xs"
        />
      </div>
      <div class="header-actions">
        <UTooltip text="Regenerate suggestions">
          <UButton
            :loading="loading"
            :disabled="!lastPrompt || !currentPrompt || currentPrompt.trim().length < 3"
            variant="ghost"
            size="xs"
            icon="i-heroicons-arrow-path-20-solid"
            @click="handleRegenerate"
          />
        </UTooltip>
        <UButton
          variant="ghost"
          size="xs"
          icon="i-heroicons-x-mark-20-solid"
          @click="$emit('toggle')"
        />
      </div>
    </div>

    <!-- Settings Row -->
    <div class="panel-settings">
      <div class="settings-grid">
        <div class="settings-group">
          <label class="settings-label">Mode:</label>
          <UButton
            :label="mode === 'gaming' ? 'Gaming' : 'Default'"
            :color="mode === 'gaming' ? 'warning' : 'primary'"
            variant="soft"
            size="xs"
            :icon="
              mode === 'gaming'
                ? 'i-heroicons-command-line-20-solid'
                : 'i-heroicons-sparkles-20-solid'
            "
            @click="handleModeToggle"
          />
        </div>
        <div class="settings-group">
          <label class="settings-label">Length:</label>
          <UButton
            :label="suggestionType === 'long' ? 'Detailed' : 'Short'"
            :color="suggestionType === 'long' ? 'success' : 'neutral'"
            variant="soft"
            size="xs"
            :icon="
              suggestionType === 'long'
                ? 'i-heroicons-bars-3-center-left-20-solid'
                : 'i-heroicons-bars-2-20-solid'
            "
            @click="handleTypeToggle"
          />
        </div>
      </div>
      <div class="service-selector">
        <label class="settings-label">AI Service:</label>
        <div class="service-dropdown-wrapper">
          <USelectMenu
            v-model="selectedServiceItem"
            :items="serviceItems"
            :icon="selectedServiceItem?.icon"
            placeholder="Select AI Model"
            size="sm"
            class="service-select"
          />
          <div
            v-if="selectedServiceItem && selectedServiceItem.value"
            class="selected-service-info"
          >
            <UIcon :name="selectedServiceItem.icon" class="service-info-icon" />
            <span class="service-info-text">{{
              getProviderFromValue(selectedServiceItem.value)
            }}</span>
          </div>
        </div>
      </div>

      <!-- Advanced Prompt Toggle -->
      <div v-if="currentPrompt && currentPrompt.trim()" class="advanced-toggle">
        <UButton
          :variant="showAdvancedPrompt ? 'solid' : 'soft'"
          :color="showAdvancedPrompt ? 'primary' : 'neutral'"
          size="xs"
          block
          @click="showAdvancedPrompt = !showAdvancedPrompt"
        >
          <div class="advanced-toggle-content">
            <UIcon name="i-heroicons-code-bracket-square-20-solid" class="w-3.5 h-3.5" />
            <span class="advanced-toggle-text"
              >{{ showAdvancedPrompt ? 'Hide' : 'View' }} Prompt Engineering</span
            >
            <UIcon
              :name="
                showAdvancedPrompt
                  ? 'i-heroicons-chevron-up-20-solid'
                  : 'i-heroicons-chevron-down-20-solid'
              "
              class="w-3 h-3 ml-auto"
            />
          </div>
        </UButton>
      </div>
    </div>

    <!-- Advanced Prompt View -->
    <div
      v-if="showAdvancedPrompt && currentPrompt && currentPrompt.trim()"
      class="advanced-prompt-view"
    >
      <div class="advanced-prompt-header">
        <div class="header-badge">
          <UIcon name="i-heroicons-cpu-chip-20-solid" class="w-4 h-4" />
          <span>AI Prompt Template</span>
        </div>
        <UButton
          v-if="!isEditingPrompt"
          variant="ghost"
          size="xs"
          icon="i-heroicons-pencil-square-20-solid"
          @click="startEditingPrompt"
        >
          Customize
        </UButton>
        <div v-else class="edit-actions">
          <UButton
            variant="solid"
            color="success"
            size="xs"
            icon="i-heroicons-check-20-solid"
            @click="saveCustomPrompt"
          />
          <UButton
            variant="ghost"
            size="xs"
            icon="i-heroicons-x-mark-20-solid"
            @click="cancelEditingPrompt"
          />
        </div>
      </div>

      <div class="advanced-prompt-body">
        <div class="prompt-section">
          <div class="section-label">
            <UIcon name="i-heroicons-user-20-solid" class="w-3 h-3" />
            <span>Your Input</span>
          </div>
          <div class="section-content user-input">
            {{ currentPrompt }}
          </div>
        </div>

        <div class="prompt-divider">
          <UIcon name="i-heroicons-arrow-down-20-solid" class="w-3 h-3" />
        </div>

        <div class="prompt-section">
          <div class="section-label">
            <UIcon name="i-heroicons-sparkles-20-solid" class="w-3 h-3" />
            <span>AI Enhancement Template</span>
          </div>
          <div v-if="!isEditingPrompt" class="section-content ai-template">
            {{ customPromptTemplate || getFullAIPrompt() }}
          </div>
          <UTextarea
            v-else
            v-model="editablePromptTemplate"
            :rows="8"
            :maxrows="12"
            autoresize
            class="prompt-textarea"
            placeholder="Enter your custom AI prompt template..."
          />
          <div class="template-hint">
            <UIcon name="i-heroicons-information-circle-20-solid" class="w-3 h-3" />
            <span
              >This template guides the AI to generate relevant suggestions for your moodboard</span
            >
          </div>
        </div>
      </div>
    </div>

    <!-- Content Area -->
    <div class="panel-content">
      <!-- Loading State -->
      <div v-if="loading" class="loading-state">
        <div class="flex items-center justify-center py-8">
          <UIcon
            name="i-heroicons-arrow-path-20-solid"
            class="w-6 h-6 animate-spin text-purple-600"
          />
          <span class="ml-2 text-sm text-gray-600 dark:text-gray-400"
            >Generating suggestions...</span
          >
        </div>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="error-state">
        <div
          class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800/30 rounded-lg p-3"
        >
          <div class="flex items-start">
            <UIcon
              name="i-heroicons-exclamation-triangle-20-solid"
              class="w-4 h-4 text-red-600 dark:text-red-400 mt-0.5"
            />
            <div class="ml-2 flex-1">
              <p class="text-xs text-red-800 dark:text-red-200 font-medium">AI Service Error</p>
              <p class="text-xs text-red-600 dark:text-red-400 mt-1">{{ error }}</p>
              <div v-if="error.includes('token') || error.includes('API')" class="mt-2">
                <p class="text-xs text-red-700 dark:text-red-300 mb-1">
                  To use AI suggestions, you need to:
                </p>
                <ul class="text-xs text-red-600 dark:text-red-400 list-disc list-inside space-y-1">
                  <li>Configure API tokens below</li>
                  <li>Ensure tokens are valid and active</li>
                  <li>Check service availability</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="suggestions.length === 0" class="empty-state">
        <div class="text-center py-8">
          <UIcon
            name="i-heroicons-light-bulb-20-solid"
            class="w-8 h-8 text-gray-400 dark:text-gray-600 mx-auto mb-3"
          />
          <p class="text-sm text-gray-600 dark:text-gray-400 mb-2 font-medium">
            No suggestions yet
          </p>
          <div
            v-if="!currentPrompt || currentPrompt.trim().length < 3"
            class="text-xs text-gray-500 dark:text-gray-500 space-y-1"
          >
            <p>Enter a prompt to get AI-powered suggestions:</p>
            <ul class="list-disc list-inside space-y-1 mt-2 text-left max-w-xs mx-auto">
              <li>At least 3 characters long</li>
              <li>Describe what you want to create</li>
              <li>Be specific for better results</li>
            </ul>
          </div>
          <p v-else class="text-xs text-gray-500 dark:text-gray-500">
            Click "Generate Suggestions" to get AI-powered ideas for your moodboard
          </p>
        </div>
      </div>

      <!-- Suggestions List -->
      <div v-else class="suggestions-list">
        <div
          v-for="(suggestion, index) in suggestions"
          :key="index"
          class="suggestion-item"
          :class="{ 'suggestion-applied': suggestion.applied }"
        >
          <div class="suggestion-content">
            <p class="suggestion-text">{{ suggestion.text }}</p>
          </div>
          <div class="suggestion-actions">
            <UTooltip v-if="!suggestion.applied" text="Apply this suggestion">
              <UButton
                size="xs"
                variant="soft"
                color="primary"
                icon="i-heroicons-plus-20-solid"
                @click="$emit('apply-suggestion', index)"
              />
            </UTooltip>
            <UTooltip v-else text="Suggestion applied">
              <UButton
                size="xs"
                variant="soft"
                color="success"
                icon="i-heroicons-check-20-solid"
                @click="$emit('unapply-suggestion', index)"
              />
            </UTooltip>
          </div>
        </div>
      </div>

      <!-- Applied Count -->
      <div v-if="appliedSuggestionsCount > 0" class="panel-footer">
        <div class="text-xs text-green-600 dark:text-green-400 text-center">
          {{ appliedSuggestionsCount }} of {{ totalSuggestions }} suggestions applied
        </div>
      </div>
    </div>

    <!-- Token Management Section -->
    <div class="token-management-section">
      <div class="token-header">
        <UIcon name="i-heroicons-key-20-solid" class="text-blue-600 dark:text-blue-400" />
        <h4>API Tokens</h4>
        <UTooltip text="Manage your AI service API tokens">
          <UIcon name="i-heroicons-information-circle-20-solid" class="text-gray-400 w-3 h-3" />
        </UTooltip>
      </div>

      <div class="token-content">
        <div v-if="isTokensLoading" class="token-loading">
          <UIcon name="i-heroicons-arrow-path-20-solid" class="w-4 h-4 animate-spin" />
          <span class="text-xs ml-2">Loading tokens...</span>
        </div>

        <div v-else-if="tokenError" class="token-error">
          <UAlert
            color="error"
            variant="soft"
            :title="tokenError"
            :close-button="{
              icon: 'i-heroicons-x-mark-20-solid',
              color: 'gray',
              variant: 'link',
              padded: false,
            }"
            @close="tokenError = null"
          />
        </div>

        <div v-else class="token-list">
          <div class="token-services">
            <div
              v-for="serviceType in availableServiceTypes"
              :key="serviceType.value"
              class="token-service-item"
            >
              <div class="service-info">
                <UIcon :name="getServiceIcon(serviceType.value)" class="service-icon" />
                <div class="service-details">
                  <span class="service-name">{{ serviceType.label }}</span>
                  <span v-if="getTokenForService(serviceType.value)" class="token-status active">
                    ••••••••
                  </span>
                  <span v-else class="token-status inactive">Not configured</span>
                </div>
              </div>

              <div class="token-actions">
                <UButton
                  v-if="!getTokenForService(serviceType.value)"
                  size="xs"
                  variant="soft"
                  color="primary"
                  icon="i-heroicons-plus-20-solid"
                  label="Add"
                  @click="showTokenInput(serviceType.value)"
                />
                <div v-else class="token-action-group">
                  <UButton
                    size="xs"
                    variant="ghost"
                    icon="i-heroicons-pencil-20-solid"
                    @click="showTokenInput(serviceType.value)"
                  />
                  <UButton
                    size="xs"
                    variant="ghost"
                    color="error"
                    icon="i-heroicons-trash-20-solid"
                    @click="deleteToken(serviceType.value)"
                  />
                </div>
              </div>
            </div>
          </div>

          <!-- Token Input Modal/Form -->
          <div v-if="showTokenForm" class="token-input-form">
            <div class="token-form-header">
              <span class="text-sm font-medium"
                >{{ editingToken ? 'Update' : 'Add' }}
                {{ getServiceLabel(currentServiceType) }} Token</span
              >
              <UButton
                size="xs"
                variant="ghost"
                icon="i-heroicons-x-mark-20-solid"
                @click="hideTokenInput"
              />
            </div>
            <div class="token-form-content">
              <div class="mb-3">
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  API Token
                </label>
                <p class="text-xs text-gray-500 dark:text-gray-400 mb-2">
                  Enter your API key for this service
                </p>
                <UInput
                  v-model="tokenInput"
                  type="password"
                  placeholder="Enter API token..."
                  size="sm"
                  :disabled="isTokenSaving"
                />
              </div>
              <div class="token-form-actions">
                <UButton size="xs" variant="ghost" label="Cancel" @click="hideTokenInput" />
                <UButton
                  :loading="isTokenSaving"
                  :disabled="!tokenInput.trim()"
                  size="xs"
                  color="primary"
                  :label="editingToken ? 'Update' : 'Save'"
                  @click="saveToken"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Generate Button Footer -->
    <div v-if="!loading && suggestions.length === 0" class="panel-footer">
      <UButton
        :disabled="!canGenerate || loading || !currentPrompt || currentPrompt.trim().length < 3"
        color="primary"
        variant="solid"
        size="sm"
        block
        icon="i-heroicons-sparkles-20-solid"
        @click="handleGenerateFromInput"
      >
        {{
          !currentPrompt || currentPrompt.trim().length < 3
            ? 'Enter prompt to generate'
            : 'Generate'
        }}
      </UButton>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'

interface Props {
  isVisible: boolean
  suggestions: Array<{ text: string; applied: boolean }>
  loading: boolean
  error: string | null
  mode: 'default' | 'gaming'
  suggestionType: 'short' | 'long'
  totalSuggestions: number
  appliedSuggestionsCount: number
  lastPrompt: string
  currentPrompt?: string
  canGenerate?: boolean
  services?: Array<{ id: string; name: string; status: string }>
  activeService?: string
}

interface Emits {
  (e: 'toggle' | 'regenerate' | 'generate-from-input' | 'fetch-services' | 'clear-error'): void
  (e: 'apply-suggestion' | 'unapply-suggestion', index: number): void
  (e: 'mode-changed', mode: 'default' | 'gaming'): void
  (e: 'type-changed', type: 'short' | 'long'): void
  (e: 'service-changed', serviceId: string): void
}

const props = withDefaults(defineProps<Props>(), {
  currentPrompt: '',
  canGenerate: true,
  services: () => [],
  activeService: undefined,
})

const emit = defineEmits<Emits>()

// Convert services to SelectMenuItem format
const serviceItems = computed(() => {
  const items: Array<{ label: string; value: string; icon: string }> = []

  if (props.services) {
    items.push(
      ...props.services.map((service) => {
        // Extract provider from service name or ID and create better labels
        let shortName = service.name || service.id
        let fullLabel = shortName
        let icon = 'i-heroicons-cpu-chip-20-solid'

        if (service.id.includes('github_')) {
          shortName = shortName.replace(/^.*?\//, '').replace(/\s*\(.*?\)/, '')
          fullLabel = `${shortName} (GitHub)`
          icon = 'i-simple-icons-github'
        } else if (service.id.includes('tgi_')) {
          shortName = shortName.replace(/^.*?\//, '').replace(/\s*\(.*?\)/, '')
          fullLabel = `${shortName} (HF TGI)`
          icon = 'i-simple-icons-huggingface'
        } else if (service.id.includes('gemini')) {
          fullLabel = `${shortName} (Gemini)`
          icon = 'i-simple-icons-google'
        } else if (service.id.includes('openai') || service.id.includes('gpt')) {
          shortName = shortName.replace(/^.*?\//, '').replace(/\s*\(.*?\)/, '')
          fullLabel = `${shortName} (OpenAI)`
          icon = 'i-simple-icons-openai'
        }

        return {
          label: fullLabel,
          value: service.id,
          icon: icon,
          status: service.status,
        }
      }),
    )
  }

  return items
})

// Selected service object (not just string)
const selectedServiceItem = computed({
  get: () => {
    const activeValue = props.activeService || ''
    return serviceItems.value.find((item) => item.value === activeValue) || serviceItems.value[0]
  },
  set: (item) => {
    emit('service-changed', item?.value || '')
  },
})

// Helper function to get service icon based on service ID or value
const getServiceIcon = (serviceValue: string) => {
  if (!serviceValue || serviceValue === '') {
    return 'i-heroicons-cpu-chip-20-solid' // Default icon when no service selected
  }

  if (serviceValue.includes('github_')) {
    return 'i-simple-icons-github' // GitHub icon
  } else if (serviceValue.includes('tgi_')) {
    return 'i-simple-icons-huggingface' // Hugging Face icon
  } else if (serviceValue.includes('gemini') || serviceValue.includes('google')) {
    return 'i-simple-icons-google' // Google icon
  } else if (serviceValue.includes('openai') || serviceValue.includes('gpt')) {
    return 'i-simple-icons-openai' // OpenAI icon
  }

  return 'i-heroicons-cpu-chip-20-solid' // Default AI icon
}

// Helper function to get selected service provider info
const getProviderFromValue = (value: string) => {
  if (!value) return 'Auto'

  if (value.includes('github_')) {
    return 'GitHub Models'
  } else if (value.includes('tgi_')) {
    return 'Hugging Face TGI'
  } else if (value.includes('gemini')) {
    return 'Google Gemini'
  } else if (value.includes('openai') || value.includes('gpt')) {
    return 'OpenAI'
  }

  return 'Custom'
}

// Token management logic
const {
  userTokens,
  isTokensLoading,
  tokenError,
  fetchUserTokens,
  saveUserToken,
  updateUserToken,
  deleteUserToken,
} = useAISuggestions()

// Watch for active service changes and clear errors
watch(
  () => props.activeService,
  () => {
    emit('clear-error')
  },
)

// Token management state
const showTokenForm = ref(false)
const currentServiceType = ref('')
const tokenInput = ref('')
const editingToken = ref(false)
const isTokenSaving = ref(false)

// Advanced prompt state
const showAdvancedPrompt = ref(false)
const isEditingPrompt = ref(false)
const editablePromptTemplate = ref('')
const customPromptTemplate = ref('')

// Build the full AI prompt template (matches backend _create_contextual_prompt)
const getFullAIPrompt = () => {
  let template = ''

  // Determine format instruction based on suggestion type
  const wordCount = props.suggestionType === 'long' ? '10-20 words each' : '2-8 words each'
  const formatInstruction =
    props.suggestionType === 'long'
      ? 'Format as complete descriptive sentences, one per line'
      : 'Format as brief phrases only, one per line'

  // Always 3 suggestions (suggestion_type only affects length/format, not quantity)
  const numSuggestions = '3'

  if (props.mode === 'gaming') {
    template = `Help expand this gaming prompt: "${props.currentPrompt}"

Provide ${numSuggestions} creative suggestions (${wordCount}) that could enhance this prompt for game art creation.

${formatInstruction}`
  } else {
    template = `Help expand this artistic prompt: "${props.currentPrompt}"

Provide ${numSuggestions} creative suggestions (${wordCount}) that could enhance this prompt for visual art creation.

${formatInstruction}`
  }

  return template
}

// Advanced prompt editing functions
const startEditingPrompt = () => {
  editablePromptTemplate.value = customPromptTemplate.value || getFullAIPrompt()
  isEditingPrompt.value = true
}

const saveCustomPrompt = () => {
  customPromptTemplate.value = editablePromptTemplate.value.trim()
  isEditingPrompt.value = false
}

const cancelEditingPrompt = () => {
  editablePromptTemplate.value = ''
  isEditingPrompt.value = false
}

// Watch for mode/type changes to update the prompt preview
watch([() => props.mode, () => props.suggestionType, () => props.currentPrompt], () => {
  // If user hasn't customized the prompt, update it when settings change
  if (!customPromptTemplate.value && isEditingPrompt.value) {
    editablePromptTemplate.value = getFullAIPrompt()
  }
})

// Available service types that require tokens
const availableServiceTypes = computed(() => [
  { value: 'github', label: 'GitHub Models' },
  { value: 'huggingface', label: 'Hugging Face' },
])

// Get token for a specific service
const getTokenForService = (serviceType: string) => {
  return userTokens.value.find((token) => token.service_type === serviceType)
}

// Get service label from service type
const getServiceLabel = (serviceType: string) => {
  const service = availableServiceTypes.value.find((s) => s.value === serviceType)
  return service?.label || serviceType
}

// Show token input form
const showTokenInput = (serviceType: string) => {
  currentServiceType.value = serviceType
  const existingToken = getTokenForService(serviceType)
  editingToken.value = !!existingToken
  tokenInput.value = ''
  showTokenForm.value = true
}

// Hide token input form
const hideTokenInput = () => {
  showTokenForm.value = false
  currentServiceType.value = ''
  tokenInput.value = ''
  editingToken.value = false
  tokenError.value = null
}

// Save or update token
const saveToken = async () => {
  if (!tokenInput.value.trim() || !currentServiceType.value) return

  isTokenSaving.value = true
  tokenError.value = null

  try {
    if (editingToken.value) {
      await updateUserToken(currentServiceType.value, tokenInput.value.trim())
    } else {
      await saveUserToken(currentServiceType.value, tokenInput.value.trim())
    }
    hideTokenInput()
  } catch (error) {
    console.error('Error saving token:', error)
  } finally {
    isTokenSaving.value = false
  }
}

// Delete token
const deleteToken = async (serviceType: string) => {
  try {
    await deleteUserToken(serviceType)
  } catch (error) {
    console.error('Error deleting token:', error)
  }
}

// Load tokens when component mounts
onMounted(() => {
  fetchUserTokens()
})

const handleRegenerate = () => {
  emit('regenerate')
}

const handleModeToggle = () => {
  const newMode = props.mode === 'default' ? 'gaming' : 'default'
  emit('mode-changed', newMode)
}

const handleTypeToggle = () => {
  const newType = props.suggestionType === 'short' ? 'long' : 'short'
  emit('type-changed', newType)
}

const handleGenerateFromInput = () => {
  emit('generate-from-input')
}
</script>

<style scoped>
.ai-suggestions-panel {
  position: fixed;
  top: 80px; /* Below header */
  right: -400px; /* Hidden by default */
  width: 380px;
  height: calc(100vh - 160px); /* Account for header and prompt bar */
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  box-shadow:
    0 10px 25px -5px rgba(0, 0, 0, 0.1),
    0 10px 10px -5px rgba(0, 0, 0, 0.04);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 50;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.ai-suggestions-panel.panel-visible {
  right: 20px;
}

.dark .ai-suggestions-panel {
  background: #1f2937;
  border-color: #374151;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid #f3f4f6;
  flex-shrink: 0;
}

.dark .panel-header {
  border-bottom-color: #374151;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-left h3 {
  font-size: 14px;
  font-weight: 600;
  margin: 0;
  color: #1f2937;
}

.dark .header-left h3 {
  color: #f9fafb;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.panel-settings {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  border-bottom: 1px solid #f3f4f6;
  flex-shrink: 0;
  background: #f9fafb;
}

.dark .panel-settings {
  border-bottom-color: #374151;
  background: #111827;
}

.settings-grid {
  display: flex;
  align-items: center;
  gap: 16px;
}

.settings-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.service-selector {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.service-dropdown-wrapper {
  min-width: 200px;
  max-width: 250px;
  position: relative;
}

.service-select {
  width: 100%;
}

.selected-service-info {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
  padding: 2px 4px;
}

.service-info-icon {
  width: 12px !important;
  height: 12px !important;
  color: #6b7280;
}

.service-info-text {
  font-size: 10px;
  color: #6b7280;
  font-weight: 500;
}

.dark .service-info-icon,
.dark .service-info-text {
  color: #9ca3af;
}

.settings-label {
  font-size: 11px;
  font-weight: 500;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.dark .settings-label {
  color: #9ca3af;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.loading-state,
.error-state,
.empty-state {
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.suggestions-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.suggestion-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fafafa;
  transition: all 0.2s ease;
}

.suggestion-item:hover {
  border-color: #d1d5db;
  background: #f5f5f5;
}

.suggestion-item.suggestion-applied {
  border-color: #10b981;
  background: #ecfdf5;
}

.dark .suggestion-item {
  border-color: #374151;
  background: #111827;
}

.dark .suggestion-item:hover {
  border-color: #4b5563;
  background: #0f172a;
}

.dark .suggestion-item.suggestion-applied {
  border-color: #059669;
  background: #022c22;
}

.suggestion-content {
  flex: 1;
}

.suggestion-text {
  font-size: 13px;
  line-height: 1.4;
  color: #374151;
  margin: 0;
}

.dark .suggestion-text {
  color: #d1d5db;
}

.suggestion-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.panel-footer {
  padding: 16px;
  border-top: 1px solid #f3f4f6;
  flex-shrink: 0;
}

.dark .panel-footer {
  border-top-color: #374151;
}

/* Mobile adjustments */
@media (max-width: 768px) {
  .ai-suggestions-panel {
    top: 60px;
    right: -100vw;
    width: 100vw;
    height: calc(100vh - 120px);
    border-radius: 0;
    border-left: none;
    border-right: none;
  }

  .ai-suggestions-panel.panel-visible {
    right: 0;
  }

  .panel-settings {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .settings-grid {
    flex-direction: column;
    gap: 8px;
  }

  .settings-group,
  .service-selector {
    justify-content: space-between;
    width: 100%;
  }

  .service-dropdown-wrapper {
    min-width: auto;
    max-width: 100%;
    flex: 1;
  }

  .service-selector {
    align-items: flex-start;
    gap: 4px;
  }
}

/* Token Management Styles */
.token-management-section {
  border-top: 1px solid #e5e7eb;
  padding: 16px;
}

.dark .token-management-section {
  border-color: #374151;
}

.token-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.token-header h4 {
  font-size: 14px;
  font-weight: 600;
  margin: 0;
  color: #374151;
}

.dark .token-header h4 {
  color: #d1d5db;
}

.token-loading,
.token-error {
  display: flex;
  align-items: center;
  padding: 8px 0;
}

.token-service-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  margin-bottom: 8px;
  background: #f9fafb;
}

.dark .token-service-item {
  border-color: #374151;
  background: #1f2937;
}

.service-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.service-icon {
  width: 16px !important;
  height: 16px !important;
}

.service-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.service-name {
  font-size: 12px;
  font-weight: 500;
  color: #374151;
}

.dark .service-name {
  color: #d1d5db;
}

.token-status {
  font-size: 10px;
  font-weight: 400;
}

.token-status.active {
  color: #059669;
}

.token-status.inactive {
  color: #6b7280;
}

.token-actions {
  display: flex;
  gap: 4px;
}

.token-action-group {
  display: flex;
  gap: 4px;
}

.token-input-form {
  margin-top: 12px;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: white;
}

.dark .token-input-form {
  border-color: #374151;
  background: #1f2937;
}

.token-form-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.token-form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 12px;
}

/* Advanced Prompt Styles - Cyberpunk/Tech Aesthetic */
.advanced-toggle {
  margin-top: 8px;
}

.advanced-toggle-content {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.advanced-toggle-text {
  flex: 1;
  text-align: left;
}

.advanced-prompt-view {
  border-top: 2px solid #8b5cf6;
  background: linear-gradient(135deg, #f5f3ff 0%, #faf5ff 100%);
  padding: 16px;
  animation: slideDown 0.3s ease-out;
}

.dark .advanced-prompt-view {
  background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
  border-top-color: #a78bfa;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.advanced-prompt-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e9d5ff;
}

.dark .advanced-prompt-header {
  border-bottom-color: #4c1d95;
}

.header-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%);
  color: white;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.3);
}

.edit-actions {
  display: flex;
  gap: 4px;
}

.advanced-prompt-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.prompt-section {
  background: white;
  border: 1px solid #e9d5ff;
  border-radius: 8px;
  padding: 12px;
  position: relative;
  overflow: hidden;
}

.dark .prompt-section {
  background: #1f2937;
  border-color: #6b21a8;
}

/* Glowing effect on hover */
.prompt-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, #8b5cf6, #a78bfa, #8b5cf6);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.prompt-section:hover::before {
  opacity: 1;
}

.section-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  color: #7c3aed;
  margin-bottom: 8px;
}

.dark .section-label {
  color: #c4b5fd;
}

.section-content {
  font-size: 12px;
  line-height: 1.6;
  color: #374151;
  white-space: pre-wrap;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.dark .section-content {
  color: #d1d5db;
}

.section-content.user-input {
  background: #faf5ff;
  padding: 10px;
  border-radius: 6px;
  border-left: 3px solid #8b5cf6;
  font-weight: 500;
}

.dark .section-content.user-input {
  background: #1e1b4b;
  border-left-color: #a78bfa;
}

.section-content.ai-template {
  background: #f5f3ff;
  padding: 12px;
  border-radius: 6px;
  border: 1px dashed #c4b5fd;
}

.dark .section-content.ai-template {
  background: #312e81;
  border-color: #6b21a8;
}

.prompt-divider {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px 0;
  position: relative;
}

.prompt-divider::before,
.prompt-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, #c4b5fd, transparent);
}

.dark .prompt-divider::before,
.dark .prompt-divider::after {
  background: linear-gradient(90deg, transparent, #6b21a8, transparent);
}

.prompt-divider svg {
  color: #8b5cf6;
  background: white;
  padding: 4px;
  border-radius: 50%;
  border: 2px solid #e9d5ff;
  margin: 0 12px;
}

.dark .prompt-divider svg {
  color: #a78bfa;
  background: #1f2937;
  border-color: #6b21a8;
}

.prompt-textarea {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 11px;
  line-height: 1.6;
  background: #faf5ff !important;
  border: 1px solid #c4b5fd !important;
}

.dark .prompt-textarea {
  background: #1e1b4b !important;
  border-color: #6b21a8 !important;
}

.template-hint {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin-top: 8px;
  padding: 8px;
  background: #fef3c7;
  border-radius: 6px;
  font-size: 10px;
  line-height: 1.4;
  color: #92400e;
}

.dark .template-hint {
  background: #422006;
  color: #fde68a;
}

.template-hint svg {
  flex-shrink: 0;
  margin-top: 1px;
}
</style>
